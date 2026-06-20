import math
import sys
import threading

import pygame

from car_telemetry import CarTelemetry


# =========================
# BASIC SETUP
# =========================

WIDTH, HEIGHT = 1040, 640
MIN_WIDTH, MIN_HEIGHT = 640, 480
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("DashBuddy OS")
clock = pygame.time.Clock()


# =========================
# COLORS
# =========================

BG_TOP = (8, 12, 23)
BG_BOTTOM = (13, 18, 32)
SURFACE = (20, 27, 43)
SURFACE_2 = (25, 34, 54)
SURFACE_HOVER = (31, 44, 70)
STROKE_SOFT = (37, 49, 70)
SHADOW = (3, 5, 10)

TEXT = (239, 243, 250)
MUTED = (154, 164, 181)
FAINT = (104, 116, 136)

BLUE = (88, 166, 255)
CYAN = (64, 211, 231)
GREEN = (85, 214, 149)
YELLOW = (244, 191, 79)
RED = (244, 105, 105)


# =========================
# FONTS
# =========================

FONT_NAME = "segoeui"


def make_font(size, bold=False):
    return pygame.font.SysFont(FONT_NAME, size, bold=bold)


fonts = {
    "brand": make_font(24, True),
    "hero": make_font(44, True),
    "hero_small": make_font(34, True),
    "speed": make_font(86, True),
    "speed_small": make_font(62, True),
    "value": make_font(38, True),
    "value_small": make_font(28, True),
    "heading": make_font(23, True),
    "body": make_font(18),
    "body_bold": make_font(18, True),
    "small": make_font(15),
    "tiny": make_font(13),
}


# =========================
# TELEMETRY STATE
# =========================

telemetry = None
telemetry_connected = False
telemetry_connecting = True
telemetry_error = ""


def connect_obd_in_background():
    """
    Tries to connect to OBD without freezing the Pygame window.

    If OBD connects, telemetry starts.
    If OBD fails, the UI keeps running and shows a warning.
    """
    global telemetry
    global telemetry_connected
    global telemetry_connecting
    global telemetry_error

    try:
        telemetry = CarTelemetry()
        telemetry.start()
        telemetry_connected = True
        telemetry_error = ""
    except Exception as e:
        telemetry = None
        telemetry_connected = False
        telemetry_error = str(e)
        print(f"[OBD Connection Failed] {e}")
    finally:
        telemetry_connecting = False


# Start OBD connection attempt in the background.
obd_thread = threading.Thread(
    target=connect_obd_in_background,
    daemon=True,
)
obd_thread.start()


# =========================
# UI HELPERS
# =========================

def lerp_color(a, b, amount):
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def draw_background(surface, elapsed):
    width, height = surface.get_size()

    for y in range(height):
        amount = y / max(1, height - 1)
        pygame.draw.line(surface, lerp_color(BG_TOP, BG_BOTTOM, amount), (0, y), (width, y))

    # Subtle dashboard grid and glow accents.
    grid_color = (19, 27, 42)
    for x in range(-40, width, 64):
        pygame.draw.line(surface, grid_color, (x, 0), (x + 90, height), 1)

    pulse = (math.sin(elapsed * 1.8) + 1) / 2
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*BLUE, 23 + int(10 * pulse)), (int(width * 0.22), 0), int(width * 0.36))
    pygame.draw.circle(glow, (*CYAN, 16), (int(width * 0.90), int(height * 0.16)), int(width * 0.25))
    surface.blit(glow, (0, 0))


def fit_text(text, font, max_width):
    text = str(text)
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    available = max_width - font.size(ellipsis)[0]
    if available <= 0:
        return ellipsis

    shortened = text
    while shortened and font.size(shortened)[0] > available:
        shortened = shortened[:-1]

    return shortened.rstrip() + ellipsis


def draw_text(text, x, y, font, color=TEXT, max_width=None):
    if max_width is not None:
        text = fit_text(text, font, max_width)

    text_surface = font.render(str(text), True, color)
    screen.blit(text_surface, (x, y))
    return text_surface.get_rect(topleft=(x, y))


def draw_panel(rect, fill=SURFACE, border=STROKE_SOFT, radius=18, shadow=True):
    if shadow:
        shadow_rect = rect.move(0, 8)
        shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (*SHADOW, 82), shadow_surface.get_rect(), border_radius=radius)
        screen.blit(shadow_surface, shadow_rect)

    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width=1, border_radius=radius)


def draw_pill(rect, label, color, fill_alpha=34):
    pill = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(pill, (*color, fill_alpha), pill.get_rect(), border_radius=rect.height // 2)
    pygame.draw.rect(pill, (*color, 170), pill.get_rect(), width=1, border_radius=rect.height // 2)
    screen.blit(pill, rect)
    draw_text(label, rect.x + 13, rect.y + 6, fonts["tiny"], color, rect.width - 26)


def draw_status_icon(center, color, state):
    x, y = center
    pygame.draw.circle(screen, (12, 18, 28), center, 26)
    pygame.draw.circle(screen, color, center, 26, width=2)

    if state == "connected":
        points = [(x - 10, y), (x - 2, y + 8), (x + 13, y - 9)]
        pygame.draw.lines(screen, color, False, points, 4)
    elif state == "connecting":
        pygame.draw.circle(screen, color, center, 10, width=3)
        pygame.draw.line(screen, color, (x + 8, y + 8), (x + 16, y + 16), 3)
    else:
        pygame.draw.line(screen, color, (x - 10, y - 10), (x + 10, y + 10), 3)
        pygame.draw.line(screen, color, (x + 10, y - 10), (x - 10, y + 10), 3)


def draw_mini_car(rect, status_color):
    body = pygame.Rect(rect.x + 20, rect.y + 28, rect.width - 40, rect.height - 54)
    cabin = pygame.Rect(rect.x + 52, rect.y + 10, rect.width - 104, 34)

    pygame.draw.rect(screen, (33, 44, 65), body, border_radius=15)
    pygame.draw.rect(screen, status_color, body, width=2, border_radius=15)
    pygame.draw.rect(screen, (27, 38, 57), cabin, border_radius=12)
    pygame.draw.line(screen, (66, 85, 112), (cabin.centerx, cabin.y + 6), (cabin.centerx, cabin.bottom - 6), 1)
    pygame.draw.circle(screen, (9, 13, 22), (body.x + 34, body.bottom), 15)
    pygame.draw.circle(screen, (9, 13, 22), (body.right - 34, body.bottom), 15)
    pygame.draw.circle(screen, status_color, (body.x + 34, body.bottom), 5)
    pygame.draw.circle(screen, status_color, (body.right - 34, body.bottom), 5)


def draw_metric_arc(rect, value, max_value, color):
    center = (rect.centerx, rect.y + max(46, min(58, rect.height // 3 + 12)))
    radius = min(rect.width // 3, rect.height // 3, 58)
    arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    arc_rect.center = center

    start_angle = math.radians(205)
    end_angle = math.radians(335)
    pygame.draw.arc(screen, (43, 55, 76), arc_rect, start_angle, end_angle, 8)

    try:
        progress = max(0.0, min(float(value) / max_value, 1.0))
    except (TypeError, ValueError):
        progress = 0.0

    progress_end = start_angle + (end_angle - start_angle) * progress
    pygame.draw.arc(screen, color, arc_rect, start_angle, progress_end, 8)


def pet_message():
    if telemetry_connected:
        return "DashBuddy: I am awake and watching your Corolla."

    if telemetry_connecting:
        return "DashBuddy: Looking for the OBD adapter so I can wake up."

    return "DashBuddy: Connect the OBD adapter so I can wake up."


def status_details():
    if telemetry_connecting:
        return {
            "state": "connecting",
            "title": "Searching for OBD-II adapter",
            "message": "DashBuddy is awake. Live data will appear when the adapter responds.",
            "color": CYAN,
            "pill": "CONNECTING",
        }

    if telemetry_connected:
        return {
            "state": "connected",
            "title": "OBD-II connected",
            "message": "Live telemetry is active.",
            "color": GREEN,
            "pill": "LIVE",
        }

    return {
        "state": "offline",
        "title": "Connect OBD-II adapter",
        "message": "Live gauges, trip stats, and diagnostics are paused.",
        "color": YELLOW,
        "pill": "OFFLINE",
    }


# =========================
# UI SECTIONS
# =========================

def draw_top_bar(width, height):
    top_rect = pygame.Rect(0, 0, width, 78)
    pygame.draw.rect(screen, (9, 13, 24), top_rect)
    pygame.draw.line(screen, STROKE_SOFT, (0, top_rect.bottom), (width, top_rect.bottom), 1)

    draw_text("DashBuddy OS", 30, 22, fonts["brand"], TEXT)

    status = status_details()
    pill_width = 110 if width >= 760 else 92
    draw_pill(pygame.Rect(width - pill_width - 30, 23, pill_width, 30), status["pill"], status["color"])

    if width >= 790:
        draw_text("ESC to quit", width - pill_width - 132, 28, fonts["small"], FAINT)


def draw_connection_card(rect):
    status = status_details()
    draw_panel(rect, fill=(18, 25, 39), border=status["color"], radius=20)
    icon_x = rect.x + (36 if rect.height < 72 else 42)
    draw_status_icon((icon_x, rect.centery), status["color"], status["state"])

    text_x = rect.x + (72 if rect.height < 72 else 82)
    title_font = fonts["body_bold"] if rect.height < 72 else fonts["heading"]
    draw_text(status["title"], text_x, rect.y + 12, title_font, TEXT, rect.width - 96)
    draw_text(status["message"], text_x, rect.y + 40, fonts["small"], MUTED, rect.width - 96)


def draw_stat_box(rect, label, value, unit="", color=CYAN, max_value=100):
    draw_panel(rect, fill=SURFACE, border=STROKE_SOFT, radius=18)
    draw_metric_arc(rect, value, max_value, color)

    label_y = rect.y + 15
    draw_text(label.upper(), rect.x + 18, label_y, fonts["tiny"], FAINT, rect.width - 36)

    value_font = fonts["value"] if rect.width >= 160 else fonts["value_small"]
    value_text = fit_text(value, value_font, rect.width - 36)
    value_rect = value_font.render(str(value_text), True, color).get_rect()
    value_x = rect.centerx - value_rect.width // 2
    value_y = rect.y + max(58, rect.height - 76)
    screen.blit(value_font.render(str(value_text), True, color), (value_x, value_y))

    if unit:
        unit_rect = fonts["tiny"].render(unit, True, MUTED).get_rect()
        screen.blit(fonts["tiny"].render(unit, True, MUTED), (rect.centerx - unit_rect.width // 2, rect.bottom - 27))


def draw_speed_card(rect, speed):
    status = status_details()
    draw_panel(rect, fill=(18, 27, 43), border=status["color"], radius=22)

    draw_text("SPEED", rect.x + 24, rect.y + 22, fonts["tiny"], FAINT, rect.width - 48)

    speed_font = fonts["speed"] if rect.width >= 380 and rect.height >= 240 else fonts["speed_small"]
    speed_text = fit_text(speed, speed_font, rect.width - 96)
    speed_surface = speed_font.render(str(speed_text), True, CYAN)
    speed_rect = speed_surface.get_rect(center=(rect.centerx, rect.y + rect.height * 0.36))
    screen.blit(speed_surface, speed_rect)

    unit_surface = fonts["heading"].render("MPH", True, MUTED)
    unit_rect = unit_surface.get_rect(center=(rect.centerx, speed_rect.bottom + 18))
    screen.blit(unit_surface, unit_rect)

    car_h = max(74, min(118, rect.height // 3))
    car_rect = pygame.Rect(rect.x + 24, rect.bottom - car_h - 22, min(220, rect.width // 2), car_h)
    draw_mini_car(car_rect, status["color"])

    message_x = car_rect.right + 20
    if message_x + 180 > rect.right:
        message_x = rect.x + 24
        message_y = car_rect.y - 62
        max_width = rect.width - 48
    else:
        message_y = car_rect.y + 16
        max_width = rect.right - message_x - 24

    draw_text(pet_message(), message_x, message_y, fonts["body_bold"], TEXT, max_width)
    draw_text(status["message"], message_x, message_y + 30, fonts["small"], MUTED, max_width)


def draw_secondary_metric(rect, label, value, unit, color, max_value):
    draw_panel(rect, fill=SURFACE, border=STROKE_SOFT, radius=18)
    draw_metric_arc(rect, value, max_value, color)

    draw_text(label.upper(), rect.x + 18, rect.y + 14, fonts["tiny"], FAINT, rect.width - 36)
    value_font = fonts["value"] if rect.width >= 190 else fonts["value_small"]
    value_text = fit_text(value, value_font, rect.width - 36)
    value_surface = value_font.render(str(value_text), True, color)
    value_rect = value_surface.get_rect(center=(rect.centerx, rect.y + rect.height * 0.58))
    screen.blit(value_surface, value_rect)

    if unit:
        unit_surface = fonts["tiny"].render(unit, True, MUTED)
        unit_rect = unit_surface.get_rect(center=(rect.centerx, rect.bottom - 22))
        screen.blit(unit_surface, unit_rect)


def draw_pet_panel(rect):
    status = status_details()
    draw_panel(rect, fill=SURFACE_2, border=STROKE_SOFT, radius=20)

    car_width = min(168, max(120, rect.width // 2 - 18), rect.width - 28)
    car_rect = pygame.Rect(rect.x + 14, rect.y + 16, car_width, rect.height - 28)
    draw_mini_car(car_rect, status["color"])

    text_x = car_rect.right + 18
    if text_x + 120 > rect.right:
        text_x = rect.x + 20
        text_y = rect.y + rect.height - 70
    else:
        text_y = rect.y + 27

    if telemetry_connected:
        line = "Connected and ready."
    elif telemetry_connecting:
        line = "Looking for your adapter."
    else:
        line = "Adapter needed for live data."

    title_font = fonts["body_bold"] if rect.height < 100 else fonts["heading"]
    draw_text("DashBuddy", text_x, text_y, title_font, TEXT, rect.right - text_x - 18)
    draw_text(line, text_x, text_y + 31, fonts["small"], MUTED, rect.right - text_x - 18)


def draw_button_icon(rect, title, color):
    center = rect.center

    if title == "Maps":
        pygame.draw.circle(screen, color, center, 13, width=3)
        pygame.draw.circle(screen, color, center, 4)
        pygame.draw.polygon(screen, color, [(center[0], center[1] + 21), (center[0] - 7, center[1] + 8), (center[0] + 7, center[1] + 8)])
    elif title == "Music":
        pygame.draw.line(screen, color, (center[0] - 5, center[1] - 14), (center[0] - 5, center[1] + 10), 4)
        pygame.draw.line(screen, color, (center[0] + 11, center[1] - 10), (center[0] + 11, center[1] + 14), 4)
        pygame.draw.line(screen, color, (center[0] - 5, center[1] - 14), (center[0] + 11, center[1] - 10), 4)
        pygame.draw.circle(screen, color, (center[0] - 10, center[1] + 12), 7)
        pygame.draw.circle(screen, color, (center[0] + 6, center[1] + 16), 7)
    elif title == "Trips":
        pygame.draw.circle(screen, color, (center[0] - 12, center[1] - 10), 5)
        pygame.draw.circle(screen, color, (center[0] + 13, center[1] + 12), 5)
        pygame.draw.line(screen, color, (center[0] - 8, center[1] - 6), (center[0] + 9, center[1] + 8), 3)
    elif title == "Settings":
        pygame.draw.circle(screen, color, center, 14, width=3)
        pygame.draw.circle(screen, color, center, 4)
        for angle in range(0, 360, 60):
            radians = math.radians(angle)
            x1 = center[0] + int(math.cos(radians) * 18)
            y1 = center[1] + int(math.sin(radians) * 18)
            x2 = center[0] + int(math.cos(radians) * 24)
            y2 = center[1] + int(math.sin(radians) * 24)
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)


def draw_touch_button(rect, title, accent, mouse_pos, enabled=True):
    hovered = rect.collidepoint(mouse_pos) and enabled
    fill = SURFACE_HOVER if hovered else SURFACE
    border = accent if hovered and enabled else STROKE_SOFT
    draw_panel(rect, fill=fill, border=border, radius=18)

    icon_size = 44 if rect.height >= 86 else 38
    icon_rect = pygame.Rect(rect.x + 18, rect.centery - icon_size // 2, icon_size, icon_size)
    icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
    pygame.draw.rect(icon, (*accent, 34 if enabled else 18), icon.get_rect(), border_radius=10)
    pygame.draw.rect(icon, (*accent, 180 if enabled else 80), icon.get_rect(), width=1, border_radius=10)
    screen.blit(icon, icon_rect)

    icon_color = accent if enabled else FAINT
    draw_button_icon(icon_rect, title, icon_color)

    title_color = TEXT if enabled else FAINT
    text_x = rect.x + icon_size + 30
    draw_text(title, text_x, rect.centery - 11, fonts["body_bold"], title_color, rect.right - text_x - 16)


def draw_home_screen(width, height, mouse_pos, elapsed):
    del elapsed

    if telemetry_connected and telemetry:
        speed, rpm, coolant, dtc = telemetry.get_data()
    else:
        speed = 0
        rpm = 0
        coolant = 0
        dtc = "Offline"

    margin = 30 if width >= 760 else 18
    gap = 18 if width >= 760 else 10
    content_top = 100 if height >= 560 else 88
    content_w = width - margin * 2
    compact = width < 780
    short = height < 560

    button_specs = [
        ("Maps", BLUE, False),
        ("Music", CYAN, False),
        ("Trips", GREEN, telemetry_connected),
        ("Settings", YELLOW, True),
    ]

    if compact:
        speed_h = 220 if not short else 178
        draw_speed_card(pygame.Rect(margin, content_top, content_w, speed_h), speed)

        metric_y = content_top + speed_h + gap
        metric_h = 104 if short else 122
        metric_w = (content_w - gap * 2) // 3
        metric_specs = [
            ("RPM", rpm, "rev/min", GREEN, 7000),
            ("Coolant", coolant, "F", YELLOW, 240),
            ("Codes", dtc, "", GREEN if dtc == "Clear" else RED, 1),
        ]
        for index, spec in enumerate(metric_specs):
            rect = pygame.Rect(margin + index * (metric_w + gap), metric_y, metric_w, metric_h)
            draw_secondary_metric(rect, *spec)

        button_y = metric_y + metric_h + gap
        button_h = 72 if short else 84
        button_w = (content_w - gap) // 2
        for index, (title, color, enabled) in enumerate(button_specs):
            row = index // 2
            col = index % 2
            rect = pygame.Rect(margin + col * (button_w + gap), button_y + row * (button_h + gap), button_w, button_h)
            if rect.bottom <= height - 12:
                draw_touch_button(rect, title, color, mouse_pos, enabled)
        return

    bottom_h = 96 if not short else 78
    main_top = content_top
    main_h = max(260, height - main_top - bottom_h - gap - margin)
    left_w = int(content_w * 0.58)
    right_w = content_w - left_w - gap

    draw_speed_card(pygame.Rect(margin, main_top, left_w, main_h), speed)

    metric_h = (main_h - gap * 2) // 3
    metric_specs = [
        ("RPM", rpm, "rev/min", GREEN, 7000),
        ("Coolant", coolant, "F", YELLOW, 240),
        ("Codes", dtc, "", GREEN if dtc == "Clear" else RED, 1),
    ]
    metric_x = margin + left_w + gap
    for index, spec in enumerate(metric_specs):
        rect = pygame.Rect(metric_x, main_top + index * (metric_h + gap), right_w, metric_h)
        draw_secondary_metric(rect, *spec)

    button_y = main_top + main_h + gap
    button_w = (content_w - gap * 3) // 4
    for index, (title, color, enabled) in enumerate(button_specs):
        rect = pygame.Rect(margin + index * (button_w + gap), button_y, button_w, bottom_h)
        draw_touch_button(rect, title, color, mouse_pos, enabled)


# =========================
# MAIN PROGRAM
# =========================

def main():
    """
    Runs the DashBuddy UI.

    The UI always stays open. OBD runs only if the adapter connects successfully.
    """
    global screen
    global telemetry

    running = True

    while running:
        clock.tick(FPS)
        elapsed = pygame.time.get_ticks() / 1000
        mouse_pos = pygame.mouse.get_pos()

        # Always process events so the window does not say Not Responding.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.VIDEORESIZE:
                new_width = max(MIN_WIDTH, event.w)
                new_height = max(MIN_HEIGHT, event.h)
                screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

        width, height = screen.get_size()
        draw_background(screen, elapsed)
        draw_top_bar(width, height)
        draw_home_screen(width, height, mouse_pos, elapsed)

        pygame.display.flip()

    try:
        if telemetry:
            telemetry.stop()
    except Exception:
        pass

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
