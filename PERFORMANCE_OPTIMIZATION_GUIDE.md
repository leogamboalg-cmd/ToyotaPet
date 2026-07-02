# DashBuddy Raspberry Pi Performance Optimization Guide

This guide focuses on the biggest CPU bottlenecks I found in `main.py` and the files it calls. The goal is to make `python main.py` lighter on a Raspberry Pi without changing the dashboard's behavior first.

## Research References

- Pygame display docs: `pygame.display.flip()` updates the full display, while `pygame.display.update(rects)` can update only changed rectangles for software displays: https://www.pygame.org/docs/ref/display.html
- Pygame transform docs: transforms return new surfaces, and resizing is a transform operation, so repeated scaling should be avoided or cached: https://www.pygame.org/docs/ref/transform.html
- python-OBD connection docs: `query()` is blocking, `fast=True` enables command optimizations, and `timeout` controls connection/query wait time: https://python-obd.readthedocs.io/en/latest/Connections/
- python-OBD async docs: `obd.Async` keeps watched command values updated in a background loop and makes later `query()` calls return the latest value immediately: https://python-obd.readthedocs.io/en/latest/Async%20Connections/
- Python profiling docs: `cProfile` is the standard low-overhead profiler to find real hot functions before and after changes: https://docs.python.org/3/library/profile.html

## Highest Impact Fixes

### 1. Reduce full-screen redraw work

Current bottleneck:

- `main.py` runs the loop at `FPS = 30`.
- Every frame ends with `pygame.display.flip()` in `main.py`, which updates the whole display.
- The home screen redraws background, top bar, all cards, icons, panels, text, circles, and bottom nav every frame.
- The Pi has to redraw roughly 921,600 pixels per frame at 1280x720, before counting all the alpha blending and rounded rectangles.

Files and lines:

- `main.py:25` sets `FPS = 30`.
- `main.py:1273` calls `clock.tick(FPS)`.
- `main.py:1391-1410` redraws the full home screen.
- `main.py:1465` calls `pygame.display.flip()`.

Fix plan:

1. Lower the frame rate first. Try `FPS = 15` or `FPS = 20`. Car telemetry only updates every 0.5 seconds right now, so 30 FPS does not give more real vehicle data.
2. Split each screen into a cached static layer and a small dynamic layer.
3. Use `pygame.display.update(dirty_rects)` when only a few values changed.
4. Redraw the full screen only after screen changes, resize events, hover changes, or layout changes.

Suggested first change:

```python
FPS = 15
```

Better follow-up structure:

```python
needs_full_redraw = True
dirty_rects = []

if current_screen_changed or resized:
    needs_full_redraw = True

if needs_full_redraw:
    draw_current_screen()
    pygame.display.flip()
    needs_full_redraw = False
else:
    dirty_rects.extend(draw_dynamic_values_only())
    pygame.display.update(dirty_rects)
```

Expected impact:

- Lowering FPS is the fastest win and can cut UI CPU significantly.
- Dirty rectangles and static layer caching are the biggest long-term win because the dashboard is mostly static UI with a few changing numbers.

### 2. Cache repeated surfaces created inside draw functions

Current bottleneck:

- `draw_soft_circle()` creates a new alpha surface every call.
- `screens/trips_screen.py` creates a new graph fill surface every frame.
- Some text rendering bypasses the existing text caches.
- Alpha surfaces and antialiased text are expensive on a Pi when repeated every frame.

Files and lines:

- `main.py:376-379` creates a new circle surface every call.
- `main.py:643` and `main.py:1213` call `draw_soft_circle()` from card drawing.
- `screens/trips_screen.py:304-313` creates and blits a new `fill_surface` every graph draw.
- `main.py:335`, `main.py:682-683`, `main.py:866`, `screens/telemetry_screen.py:258`, `screens/telemetry_screen.py:442`, and `screens/telemetry_screen.py:1040` render text without always using the local cache.

Fix plan:

1. Add a `soft_circle_cache` like `round_rect_cache`.
2. Cache graph fill surfaces when the graph size and point list are unchanged, or redraw the graph only once per second.
3. Route all repeated text through cached text helpers.
4. Keep caches bounded if the window can resize often.

Suggested `draw_soft_circle()` replacement:

```python
soft_circle_cache = {}

def draw_soft_circle(center, radius, color=(229, 246, 255), alpha=220):
    key = (radius, color, alpha)
    circle = soft_circle_cache.get(key)

    if circle is None:
        circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle, (*color, alpha), (radius, radius), radius)
        soft_circle_cache[key] = circle

    screen.blit(circle, (center[0] - radius, center[1] - radius))
```

Expected impact:

- This removes repeated surface allocation from the hottest draw path.
- It also reduces garbage collection pressure.

### 3. Stop doing duplicate telemetry reads and derived calculations every frame

Current bottleneck:

- `main()` calls `safe_data()` every frame.
- `draw_home_screen()` calls `safe_data()` again, so the home screen reads the same telemetry twice per frame.
- `safe_mpg()` calculates derived MPG every frame even on screens that do not display MPG.
- `trip_manager.get_data()` runs every frame and copies `speed_history` every time.

Files and lines:

- `main.py:1369` calls `safe_data()`.
- `main.py:1370` calls `safe_mpg()`.
- `main.py:1377` calls `trip_manager.get_data()`.
- `main.py:1011` calls `safe_data()` again inside `draw_home_screen()`.
- `trip_manager_solo.py:523` returns `self.speed_history.copy()`.
- `mpg_calculator.py:45-51` recalculates MPG whenever `get_data()` is called.

Fix plan:

1. Pass the already-read `speed` into `draw_home_screen()` instead of calling `safe_data()` inside it.
2. Only call `safe_mpg()` when `current_screen == "telemetry"` or when a visible card needs MPG.
3. Update trip snapshots on a timer, not every frame. For example, rebuild `trip_data` 2 to 5 times per second.
4. Avoid copying full `speed_history` every frame. Return the list/deque only when the current screen needs the graph.

Suggested main-loop pattern:

```python
last_trip_snapshot_at = 0.0
trip_data = trip_manager.get_data()

while running:
    now = time.monotonic()
    speed, rpm, coolant, dtc = safe_data()

    trip_manager.update(speed_mph=speed, rpm=rpm)

    if now - last_trip_snapshot_at >= 0.25:
        trip_data = trip_manager.get_data()
        last_trip_snapshot_at = now

    instant_mpg = 0.0
    if current_screen == "telemetry":
        instant_mpg = safe_mpg()
```

Expected impact:

- Less lock contention, less formatting, fewer list copies, and less work on screens that do not need all data.

### 4. Optimize OBD polling for Raspberry Pi

Current bottleneck:

- `CarTelemetry` opens `obd.OBD("COM7", fast=False, timeout=10)`.
- On a Pi the adapter is usually `/dev/ttyUSB0`, `/dev/ttyAMA0`, `/dev/rfcomm0`, or auto-detected with `None`, not `COM7`.
- `fast=False` disables python-OBD's command optimizations.
- `timeout=10` can make failed reads or connection problems wait a long time.
- The update loop sends RPM, speed, coolant, and MAF every 0.5 seconds, plus DTC every 10 seconds.

Files and lines:

- `car_telemetry.py:9` creates the OBD connection.
- `car_telemetry.py:46-49` performs four blocking queries each loop.
- `car_telemetry.py:56` queries DTC.
- `car_telemetry.py:84` sleeps for 0.5 seconds.

Fix plan:

1. Use a Pi-friendly port setting. Prefer making it configurable through an environment variable.
2. Try `fast=True` and a much shorter timeout, such as `timeout=1` or `timeout=0.5`.
3. Consider python-OBD's `Async` connection and `watch()` for RPM, SPEED, COOLANT_TEMP, and MAF.
4. Slow low-priority commands. Coolant can be 1 Hz or slower. DTC can be every 30 to 60 seconds, or only when opening the telemetry screen.
5. Avoid printing every telemetry exception in a tight loop. Rate-limit error logs.

Suggested connection change:

```python
port = os.environ.get("DASHBUDDY_OBD_PORT")
self.connection = obd.OBD(port, fast=True, timeout=1)
```

Suggested async direction:

```python
self.connection = obd.Async(port, fast=True, timeout=1, delay_cmds=0.25)
self.connection.watch(obd.commands.RPM, callback=self._handle_rpm)
self.connection.watch(obd.commands.SPEED, callback=self._handle_speed)
self.connection.watch(obd.commands.COOLANT_TEMP, callback=self._handle_coolant)
self.connection.watch(obd.commands.MAF, callback=self._handle_maf)
self.connection.start()
```

Expected impact:

- Faster OBD reads reduce background CPU time and prevent long waits when the adapter is slow.
- Async mode removes your manual query loop and lets python-OBD keep latest values ready.

### 5. Cap graph history and avoid full-list copies

Current bottleneck:

- `TripManager.speed_history` is a normal list that grows for the whole trip.
- `get_data()` copies the full list every frame.
- Trips screen converts history to another list before graphing.
- Telemetry screen slices the latest 60 values, but it receives the copied list first.

Files and lines:

- `trip_manager_solo.py:87` initializes `self.speed_history = []`.
- `trip_manager_solo.py:377` appends speed samples once per second.
- `trip_manager_solo.py:523` copies the full list.
- `screens/trips_screen.py:290` calls `values = list(speed_history or [])`.
- `screens/telemetry_screen.py:775` uses `values[-60:]`.

Fix plan:

1. Use `collections.deque(maxlen=300)` or similar for the last 5 minutes at 1 sample per second.
2. Only copy the history when drawing a graph.
3. Pass only the visible slice to screens.

Suggested change:

```python
from collections import deque

self.speed_history = deque(maxlen=300)
```

When returning data:

```python
"speed_history": list(self.speed_history)[-60:]
```

Expected impact:

- Prevents long trips from making every frame progressively more expensive.

### 6. Reduce visual cost on Raspberry Pi

Current bottleneck:

- The UI is visually rich: rounded rectangles, shadows, alpha overlays, arcs, graphs, and PNG scaling.
- That is fine on a laptop, but expensive on Pi software rendering.

Fix plan:

1. Add a Pi performance mode flag.
2. In performance mode, disable shadows or lower alpha effects.
3. Use an internal size of `800x480` on Pi and scale to the display if needed.
4. Prefer cached bitmap panels for static cards.

Suggested flag:

```python
PI_PERFORMANCE_MODE = os.environ.get("DASHBUDDY_PI_MODE") == "1"

FPS = 15 if PI_PERFORMANCE_MODE else 30
ENABLE_SHADOWS = not PI_PERFORMANCE_MODE
```

Expected impact:

- Lower resolution plus fewer alpha effects is often the most visible CPU drop on a Pi touchscreen build.

## Recommended Implementation Order

1. Set `FPS = 15` and test CPU usage.
2. Remove duplicate `safe_data()` from `draw_home_screen()` by passing `speed` in.
3. Only call `safe_mpg()` on the telemetry screen.
4. Add `soft_circle_cache`.
5. Throttle `trip_manager.get_data()` to 4 Hz.
6. Change OBD connection to configurable port, `fast=True`, and shorter timeout.
7. Cap `speed_history` with `deque(maxlen=300)`.
8. Add static screen/layer caching and dirty rectangle updates.
9. Consider replacing the manual OBD thread with `obd.Async`.

## How To Measure Before And After

Run the app normally and watch per-process CPU:

```bash
top -p "$(pgrep -f 'python.*main.py')"
```

Watch threads if OBD or audio might be the problem:

```bash
top -H -p "$(pgrep -f 'python.*main.py')"
```

Run a short Python profile:

```bash
python -m cProfile -o dashbuddy.prof main.py
python - <<'PY'
import pstats
from pstats import SortKey
pstats.Stats("dashbuddy.prof").strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(30)
PY
```

What to look for:

- If draw functions dominate, prioritize static layers, dirty rectangles, lower FPS, and caching.
- If OBD dominates, prioritize `fast=True`, shorter timeout, slower polling, and `obd.Async`.
- If `get_data()`, list copying, or graph drawing appears high, cap `speed_history` and throttle trip snapshots.

## Quick Win Patch Set

These are the smallest code changes likely to help immediately:

1. `main.py`: change `FPS = 30` to `FPS = 15`.
2. `main.py`: remove `safe_data()` inside `draw_home_screen()` and pass `speed` from the main loop.
3. `main.py`: only run `safe_mpg()` when `current_screen == "telemetry"`.
4. `main.py`: cache `draw_soft_circle()`.
5. `car_telemetry.py`: use `fast=True`, `timeout=1`, and a configurable OBD port.
6. `trip_manager_solo.py`: make `speed_history` a bounded `deque`.

Do those before a larger dirty-rectangle rewrite. They are lower risk and should make the Raspberry Pi noticeably cooler.
