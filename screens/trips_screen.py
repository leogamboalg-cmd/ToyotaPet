# trips_screen.py

import math
import pygame

# =========================
# COLORS
# =========================

TEXT = (12, 24, 45)
MUTED = (82, 91, 110)
FAINT = (132, 148, 169)

WHITE = (255, 255, 255)
PAGE_BG = (239, 249, 255)
CARD_BLUE = (239, 248, 255)

BLUE = (38, 126, 245)
BLUE_SOFT = (225, 241, 255)
GREEN = (20, 166, 112)
GREEN_SOFT = (225, 249, 239)
RED = (235, 73, 83)
RED_SOFT = (255, 236, 238)
ORANGE = (255, 145, 26)
ORANGE_SOFT = (255, 242, 224)
YELLOW = (240, 171, 0)

BORDER = (151, 198, 233)
BORDER_SOFT = (207, 226, 241)
GRID = (219, 232, 243)
SHADOW = (83, 125, 160)


# =========================
# GENERAL HELPERS
# =========================

def _font(fonts, preferred, fallback):
    """Returns a requested font, or a safe fallback from the shared font map."""
    return fonts.get(preferred, fonts[fallback])


def _draw_text(surface, text, x, y, font, color=TEXT):
    rendered = font.render(str(text), True, color)
    surface.blit(rendered, (x, y))
    return rendered.get_rect(topleft=(x, y))


def _draw_centered(surface, text, rect, font, color=TEXT):
    rendered = font.render(str(text), True, color)
    text_rect = rendered.get_rect(center=rect.center)
    surface.blit(rendered, text_rect)
    return text_rect


def _draw_panel(surface, rect, radius=20, fill=WHITE, border=BORDER_SOFT,
                shadow=True, shadow_offset=5):
    if shadow:
        shadow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (*SHADOW, 24),
            shadow_surface.get_rect(),
            border_radius=radius,
        )
        surface.blit(shadow_surface, rect.move(0, shadow_offset))

    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)


def _value(trip_data, *keys, default=0):
    """
    Reads the first matching key.

    This accepts both the old names such as "time" and the names currently
    used in main.py such as "elapsed_time".
    """
    for key in keys:
        if key in trip_data:
            return trip_data[key]
    return default


# =========================
# SMALL ICONS
# =========================

def _draw_clock_icon(surface, center, color=BLUE):
    pygame.draw.circle(surface, color, center, 13, width=3)
    pygame.draw.line(surface, color, center, (center[0], center[1] - 7), 3)
    pygame.draw.line(surface, color, center, (center[0] + 6, center[1] + 3), 3)


def _draw_pin_icon(surface, center, color=BLUE):
    pygame.draw.circle(surface, color, (center[0], center[1] - 3), 10, width=3)
    pygame.draw.circle(surface, color, (center[0], center[1] - 3), 3)
    pygame.draw.polygon(
        surface,
        color,
        [
            (center[0] - 8, center[1] + 3),
            (center[0], center[1] + 14),
            (center[0] + 8, center[1] + 3),
        ],
        width=3,
    )


def _draw_gauge_icon(surface, center, color=BLUE):
    gauge_rect = pygame.Rect(center[0] - 14, center[1] - 9, 28, 24)
    pygame.draw.arc(surface, color, gauge_rect, math.pi, math.tau, 3)
    pygame.draw.line(
        surface,
        color,
        center,
        (center[0] + 7, center[1] - 7),
        3,
    )
    pygame.draw.circle(surface, color, center, 3)


def _draw_star_icon(surface, center, color=BLUE):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = 14 if i % 2 == 0 else 6
        points.append(
            (
                center[0] + math.cos(angle) * radius,
                center[1] + math.sin(angle) * radius,
            )
        )
    pygame.draw.polygon(surface, color, points, width=3)


def _draw_car_icon(surface, center, color=BLUE):
    body = pygame.Rect(center[0] - 15, center[1] - 7, 30, 16)
    pygame.draw.rect(surface, color, body, width=3, border_radius=5)
    pygame.draw.polygon(
        surface,
        color,
        [
            (center[0] - 10, center[1] - 7),
            (center[0] - 5, center[1] - 14),
            (center[0] + 7, center[1] - 14),
            (center[0] + 12, center[1] - 7),
        ],
        width=3,
    )
    pygame.draw.circle(surface, color, (center[0] - 9, center[1] + 11), 3)
    pygame.draw.circle(surface, color, (center[0] + 9, center[1] + 11), 3)


def _draw_stat_icon(surface, kind, center):
    pygame.draw.circle(surface, BLUE_SOFT, center, 27)

    if kind == "clock":
        _draw_clock_icon(surface, center)
    elif kind == "pin":
        _draw_pin_icon(surface, center)
    elif kind == "star":
        _draw_star_icon(surface, center)
    elif kind == "car":
        _draw_car_icon(surface, center)
    else:
        _draw_gauge_icon(surface, center)


# =========================
# HEADER AND STAT CARDS
# =========================

def _draw_header(surface, width, top_h, fonts, mouse_pos):
    pygame.draw.rect(surface, WHITE, (0, 0, width, top_h))
    pygame.draw.line(surface, BORDER_SOFT, (0, top_h - 1), (width, top_h - 1))

    title_font = _font(fonts, "brand", "card_title")
    _draw_text(
        surface,
        "Trips",
        34,
        top_h // 2 - title_font.get_height() // 2,
        title_font,
        TEXT,
    )

    back_button = pygame.Rect(width - 146, top_h // 2 - 23, 116, 46)
    hovered = back_button.collidepoint(mouse_pos)

    pygame.draw.rect(
        surface,
        BLUE_SOFT if hovered else CARD_BLUE,
        back_button,
        border_radius=17,
    )
    pygame.draw.rect(
        surface,
        BLUE if hovered else BORDER,
        back_button,
        width=1,
        border_radius=17,
    )
    _draw_centered(
        surface,
        "← Home",
        back_button,
        _font(fonts, "body_bold", "body"),
        BLUE,
    )

    return back_button


def _draw_stat_card(surface, rect, title, value, subtitle, icon_kind, fonts,
                    value_color=TEXT):
    _draw_panel(surface, rect, radius=16, shadow=True)

    icon_center = (rect.x + 38, rect.centery)
    _draw_stat_icon(surface, icon_kind, icon_center)

    text_x = rect.x + 78
    small_font = _font(fonts, "tiny", "small")
    value_font = _font(fonts, "card_title_small", "card_title")

    _draw_text(surface, title.upper(), text_x, rect.y + 17, small_font, MUTED)
    _draw_text(surface, value, text_x, rect.y + 42, value_font, value_color)

    if subtitle:
        _draw_text(surface, subtitle, text_x, rect.y + 75, small_font,
                   GREEN if value_color == GREEN else FAINT)


# =========================
# SPEED GRAPH
# =========================

def _draw_speed_graph(surface, rect, fonts, speed_history):
    _draw_panel(surface, rect, radius=18)

    _draw_text(
        surface,
        "⌁  Speed History",
        rect.x + 20,
        rect.y + 16,
        _font(fonts, "body_bold", "body"),
        TEXT,
    )

    unit = pygame.Rect(rect.right - 90, rect.y + 10, 70, 32)
    pygame.draw.rect(surface, (249, 252, 255), unit, border_radius=10)
    pygame.draw.rect(surface, BORDER_SOFT, unit, width=1, border_radius=10)
    _draw_centered(surface, "MPH⌄", unit, _font(fonts, "small", "tiny"), TEXT)

    plot = pygame.Rect(rect.x + 48, rect.y + 58,
                       rect.width - 70, rect.height - 82)

    max_mph = 80
    for mph in range(0, max_mph + 1, 20):
        y = plot.bottom - int((mph / max_mph) * plot.height)
        pygame.draw.line(surface, GRID, (plot.x, y), (plot.right, y), 1)
        label = _font(fonts, "tiny", "small").render(str(mph), True, MUTED)
        surface.blit(label, (plot.x - 34, y - label.get_height() // 2))

    values = list(speed_history or [])
    if len(values) < 2:
        values = [0, 0]

    points = []
    for index, speed in enumerate(values):
        x = plot.x + int(index / (len(values) - 1) * plot.width)
        normalized = max(0, min(float(speed), max_mph)) / max_mph
        y = plot.bottom - int(normalized * plot.height)
        points.append((x, y))

    if len(points) >= 2:
        fill_points = [(points[0][0], plot.bottom), *points,
                       (points[-1][0], plot.bottom)]
        fill_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(fill_surface, (*BLUE, 24), fill_points)
        surface.blit(fill_surface, (0, 0))
        pygame.draw.lines(surface, BLUE, False, points, 3)

    labels = ["0 min", "5 min", "10 min", "15 min", "20 min", "24 min"]
    for index, label_text in enumerate(labels):
        x = plot.x + int(index / (len(labels) - 1) * plot.width)
        label = _font(fonts, "tiny", "small").render(label_text, True, MUTED)
        surface.blit(label, (x - label.get_width() // 2, plot.bottom + 8))


# =========================
# EVENTS, CONTROLS, BUDDY, HISTORY
# =========================

def _draw_driving_events(surface, rect, fonts, trip_data):
    _draw_panel(surface, rect, radius=18)

    _draw_text(
        surface,
        "⚠  Driving Events",
        rect.x + 20,
        rect.y + 16,
        _font(fonts, "body_bold", "body"),
        TEXT,
    )
    _draw_text(
        surface,
        "View All",
        rect.right - 72,
        rect.y + 18,
        _font(fonts, "small", "tiny"),
        BLUE,
    )

    rows = [
        ("◉", "Hard Brakes", "Braked strongly",
         str(_value(trip_data, "hard_brakes", default=0)), RED, RED_SOFT),
        ("ϟ", "Fast Accelerations", "Rapid acceleration",
         str(_value(trip_data, "fast_accelerations", default=0)),
         ORANGE, ORANGE_SOFT),
        ("◷", "Long Idle", "Idle over 1 minute",
         str(_value(trip_data, "long_idle_events", default=0)),
         YELLOW, ORANGE_SOFT),
        ("●", "Smoothness", "Steady and consistent",
         str(_value(trip_data, "smoothness", default="Excellent")),
         GREEN, GREEN_SOFT),
    ]

    row_top = rect.y + 48
    row_h = max(42, (rect.height - 58) // 4)

    for index, (symbol, title, subtitle, value, color, soft) in enumerate(rows):
        row = pygame.Rect(rect.x + 10, row_top + index * row_h,
                          rect.width - 20, row_h)

        if index:
            pygame.draw.line(surface, BORDER_SOFT, (row.x, row.y),
                             (row.right, row.y), 1)

        pygame.draw.circle(surface, soft, (row.x + 25, row.centery), 16)
        _draw_centered(
            surface,
            symbol,
            pygame.Rect(row.x + 9, row.centery - 16, 32, 32),
            _font(fonts, "body_bold", "body"),
            color,
        )

        _draw_text(surface, title, row.x + 50, row.y + 8,
                   _font(fonts, "small", "tiny"), TEXT)
        _draw_text(surface, subtitle, row.x + 50, row.y + 25,
                   _font(fonts, "tiny", "small"), MUTED)

        value_surface = _font(fonts, "body_bold", "body").render(
            value, True, color)
        surface.blit(value_surface, (row.right - value_surface.get_width() - 24,
                                     row.centery - value_surface.get_height() // 2))


def _draw_trip_controls(
    surface,
    rect,
    fonts,
    mouse_pos,
    trip_active,
    trip_paused,
):
    _draw_panel(surface, rect, radius=18)

    _draw_text(
        surface,
        "◉  Trip Controls",
        rect.x + 20,
        rect.y + 15,
        _font(fonts, "body_bold", "body"),
        TEXT,
    )

    gap = 12
    button_y = rect.y + 55
    button_h = rect.height - 72
    button_w = (rect.width - 40 - gap * 2) // 3

    start_button = pygame.Rect(
        rect.x + 20,
        button_y,
        button_w,
        button_h,
    )

    pause_button = pygame.Rect(
        start_button.right + gap,
        button_y,
        button_w,
        button_h,
    )

    end_button = pygame.Rect(
        pause_button.right + gap,
        button_y,
        button_w,
        button_h,
    )

    # Start button
    start_enabled = not trip_active
    start_fill = BLUE if start_enabled else (210, 220, 230)
    start_text = WHITE if start_enabled else MUTED

    if start_enabled and start_button.collidepoint(mouse_pos):
        start_fill = (28, 110, 225)

    pygame.draw.rect(
        surface,
        start_fill,
        start_button,
        border_radius=12,
    )

    _draw_centered(
        surface,
        "▶ Start Trip",
        start_button,
        _font(fonts, "small", "tiny"),
        start_text,
    )

    # Pause/resume button
    pause_enabled = trip_active

    if trip_paused:
        pause_label = "▶ Resume"
    else:
        pause_label = "Ⅱ Pause"

    pause_fill = CARD_BLUE if pause_enabled else (235, 239, 243)
    pause_text = BLUE if pause_enabled else MUTED

    if pause_enabled and pause_button.collidepoint(mouse_pos):
        pause_fill = BLUE_SOFT

    pygame.draw.rect(
        surface,
        pause_fill,
        pause_button,
        border_radius=12,
    )

    pygame.draw.rect(
        surface,
        BORDER,
        pause_button,
        width=1,
        border_radius=12,
    )

    _draw_centered(
        surface,
        pause_label,
        pause_button,
        _font(fonts, "small", "tiny"),
        pause_text,
    )

    # End button
    end_enabled = trip_active
    end_fill = RED_SOFT if end_enabled else (240, 240, 240)
    end_text = RED if end_enabled else MUTED

    if end_enabled and end_button.collidepoint(mouse_pos):
        end_fill = (250, 220, 223)

    pygame.draw.rect(
        surface,
        end_fill,
        end_button,
        border_radius=12,
    )

    pygame.draw.rect(
        surface,
        (245, 190, 194),
        end_button,
        width=1,
        border_radius=12,
    )

    _draw_centered(
        surface,
        "■ End Trip",
        end_button,
        _font(fonts, "small", "tiny"),
        end_text,
    )

    return {
        "start": start_button if start_enabled else None,
        "pause": pause_button if pause_enabled else None,
        "end": end_button if end_enabled else None,
    }


def _draw_buddy(surface, rect, fonts, trip_data):
    _draw_panel(surface, rect, radius=18)
    _draw_text(surface, "🤖  Buddy Says", rect.x + 18, rect.y + 15,
               _font(fonts, "body_bold", "body"), TEXT)

    robot_center = (rect.x + 62, rect.y + 91)
    pygame.draw.circle(surface, BLUE_SOFT, robot_center, 32)
    head = pygame.Rect(robot_center[0] - 22, robot_center[1] - 16, 44, 32)
    pygame.draw.rect(surface, (31, 63, 80), head, border_radius=10)
    pygame.draw.rect(surface, WHITE, head, width=2, border_radius=10)
    pygame.draw.circle(surface, (83, 239, 224),
                       (robot_center[0] - 9, robot_center[1]), 4)
    pygame.draw.circle(surface, (83, 239, 224),
                       (robot_center[0] + 9, robot_center[1]), 4)

    bubble = pygame.Rect(rect.x + 105, rect.y + 56,
                         rect.width - 122, rect.height - 72)
    pygame.draw.rect(surface, CARD_BLUE, bubble, border_radius=14)
    pygame.draw.rect(surface, BORDER, bubble, width=1, border_radius=14)

    score = float(_value(trip_data, "drive_score", default=100))
    if score >= 90:
        headline = "Nice smooth drive!"
        detail = "Keep it up! You're driving great."
    elif score >= 75:
        headline = "Looking good!"
        detail = "A little smoother and your score will climb."
    else:
        headline = "Let's take it easy."
        detail = "Gentler braking can improve your score."

    _draw_text(surface, headline, bubble.x + 14, bubble.y + 15,
               _font(fonts, "small", "tiny"), TEXT)
    _draw_text(surface, detail, bubble.x + 14, bubble.y + 39,
               _font(fonts, "tiny", "small"), MUTED)


def _draw_recent_trips(surface, rect, fonts, recent_trips):
    _draw_panel(surface, rect, radius=18)
    _draw_text(surface, "◷  Recent Trips", rect.x + 18, rect.y + 14,
               _font(fonts, "body_bold", "body"), TEXT)
    _draw_text(surface, "View History", rect.right - 95, rect.y + 16,
               _font(fonts, "small", "tiny"), BLUE)

    trips = recent_trips or []

    table = pygame.Rect(rect.x + 16, rect.y + 45,
                        rect.width - 32, rect.height - 60)
    pygame.draw.rect(surface, (252, 254, 255), table, border_radius=12)
    pygame.draw.rect(surface, BORDER_SOFT, table, width=1, border_radius=12)

    header_h = 26
    _draw_text(surface, "DATE & TIME", table.x + 14, table.y + 7,
               _font(fonts, "tiny", "small"), FAINT)
    _draw_text(surface, "DISTANCE", table.x + int(table.width * 0.48), table.y + 7,
               _font(fonts, "tiny", "small"), FAINT)
    _draw_text(surface, "DRIVE SCORE", table.x + int(table.width * 0.74), table.y + 7,
               _font(fonts, "tiny", "small"), FAINT)

    row_h = max(24, (table.height - header_h) // 3)
    for index, trip in enumerate(trips[:3]):
        row_y = table.y + header_h + index * row_h
        pygame.draw.line(surface, BORDER_SOFT, (table.x, row_y),
                         (table.right, row_y), 1)

        _draw_text(surface, trip.get("date", "Unknown"), table.x + 14, row_y + 7,
                   _font(fonts, "tiny", "small"), TEXT)
        _draw_text(surface, trip.get("distance", "0.00 mi"),
                   table.x + int(table.width * 0.48), row_y + 7,
                   _font(fonts, "tiny", "small"), TEXT)
        _draw_text(surface, trip.get("score", "100/100"),
                   table.x + int(table.width * 0.74), row_y + 7,
                   _font(fonts, "tiny", "small"), GREEN)


# =========================
# MAIN DRAW FUNCTION
# =========================

def draw_trips_screen(surface, width, height, fonts, trip_data, mouse_pos):
    """
    Draws the complete Trips dashboard.

    The function intentionally returns only the Home button so it remains
    compatible with your existing main.py event handling.
    """
    surface.fill(PAGE_BG)

    top_h = max(68, min(82, int(height * 0.11)))
    back_button = _draw_header(surface, width, top_h, fonts, mouse_pos)
    trip_buttons = {
        "start": None,
        "pause": None,
        "end": None,
    }

    margin = max(20, int(width * 0.025))
    outer = pygame.Rect(
        margin,
        top_h + 20,
        width - margin * 2,
        height - top_h - 38,
    )
    _draw_panel(surface, outer, radius=24, shadow=True)

    title_y = outer.y + 20
    _draw_text(surface, "Current Trip", outer.x + 24, title_y,
               _font(fonts, "card_title", "heading"), TEXT)

    trip_active = bool(
        _value(trip_data, "trip_active", default=False)
    )
    trip_paused = bool(
        _value(trip_data, "trip_paused", default=False)
    )

    if trip_paused:
        status_text = "Paused"
        status_color = ORANGE
        status_fill = ORANGE_SOFT
    elif trip_active:
        status_text = "Active Trip"
        status_color = GREEN
        status_fill = GREEN_SOFT
    else:
        status_text = "No Active Trip"
        status_color = MUTED
        status_fill = CARD_BLUE

    active_pill = pygame.Rect(outer.x + 172, title_y - 1, 122, 28)
    pygame.draw.rect(surface, status_fill, active_pill, border_radius=14)
    pygame.draw.rect(
        surface,
        status_color,
        active_pill,
        width=1,
        border_radius=14,
    )
    pygame.draw.circle(
        surface,
        status_color,
        (active_pill.x + 15, active_pill.centery),
        5,
    )
    _draw_text(
        surface,
        status_text,
        active_pill.x + 28,
        active_pill.y + 6,
        _font(fonts, "tiny", "small"),
        status_color,
    )

    # Values support both your old and current main.py key names.
    elapsed = _value(trip_data, "elapsed_time", "time", default="00:00:00")
    distance = float(
        _value(trip_data, "distance_miles", "distance", default=0))
    average = float(_value(trip_data, "average_speed", default=0))
    maximum = float(_value(trip_data, "maximum_speed", "max_speed", default=0))
    score = float(_value(trip_data, "drive_score", default=100))
    idle_time = _value(trip_data, "idle_time", default="00:00")

    stat_specs = [
        ("Trip Time", str(elapsed), "hh:mm:ss", "clock", TEXT),
        ("Distance", f"{distance:.2f} mi", "Total", "pin", TEXT),
        ("Average Speed", f"{average:.0f} MPH", "Moving", "gauge", TEXT),
        ("Max Speed", f"{maximum:.0f} MPH", "Top Speed", "gauge", TEXT),
        ("Drive Score", f"{score:.0f}/100",
         "Excellent" if score >= 90 else "Keep improving", "star", GREEN),
        ("Idle Time", str(idle_time), "hh:mm:ss", "car", TEXT),
    ]

    content_x = outer.x + 22
    content_w = outer.width - 44
    stat_y = outer.y + 66
    stat_gap = 12

    if width >= 1120:
        columns = 6
    elif width >= 820:
        columns = 3
    else:
        columns = 2

    stat_rows = math.ceil(len(stat_specs) / columns)
    stat_h = 98 if stat_rows == 1 else 82
    stat_w = (content_w - stat_gap * (columns - 1)) // columns

    for index, spec in enumerate(stat_specs):
        row = index // columns
        col = index % columns
        rect = pygame.Rect(
            content_x + col * (stat_w + stat_gap),
            stat_y + row * (stat_h + stat_gap),
            stat_w,
            stat_h,
        )
        title, value, subtitle, icon_kind, value_color = spec

        _draw_stat_card(
            surface=surface,
            rect=rect,
            title=title,
            value=value,
            subtitle=subtitle,
            icon_kind=icon_kind,
            fonts=fonts,
            value_color=value_color,
        )

    below_stats_y = stat_y + stat_rows * \
        stat_h + (stat_rows - 1) * stat_gap + 16
    bottom_padding = 18
    available_h = outer.bottom - bottom_padding - below_stats_y

    # Full dashboard layout for normal laptop/Pi landscape sizes.
    if width >= 950 and available_h >= 260:
        upper_h = int(available_h * 0.57)
        lower_h = available_h - upper_h - 14

        left_w = int(content_w * 0.58)
        right_w = content_w - left_w - 14

        graph_rect = pygame.Rect(content_x, below_stats_y, left_w, upper_h)
        events_rect = pygame.Rect(content_x + left_w + 14,
                                  below_stats_y, right_w, upper_h)

        lower_y = below_stats_y + upper_h + 14
        controls_w = int(left_w * 0.60)
        buddy_w = left_w - controls_w - 14

        controls_rect = pygame.Rect(content_x, lower_y, controls_w, lower_h)
        buddy_rect = pygame.Rect(content_x + controls_w + 14,
                                 lower_y, buddy_w, lower_h)
        recent_rect = pygame.Rect(content_x + left_w + 14,
                                  lower_y, right_w, lower_h)

        _draw_speed_graph(
            surface,
            graph_rect,
            fonts,
            _value(trip_data, "speed_history", default=None),
        )

        _draw_driving_events(
            surface,
            events_rect,
            fonts,
            trip_data,
        )

        trip_buttons = _draw_trip_controls(
            surface=surface,
            rect=controls_rect,
            fonts=fonts,
            mouse_pos=mouse_pos,
            trip_active=trip_active,
            trip_paused=trip_paused,
        )

        _draw_buddy(
            surface,
            buddy_rect,
            fonts,
            trip_data,
        )
        _draw_recent_trips(
            surface,
            recent_rect,
            fonts,
            _value(trip_data, "recent_trips", default=None),
        )

    else:
        # Compact fallback keeps the screen usable at 800x480.
        graph_h = max(145, int(available_h * 0.62))
        graph_rect = pygame.Rect(content_x, below_stats_y, content_w, graph_h)
        _draw_speed_graph(
            surface,
            graph_rect,
            fonts,
            _value(trip_data, "speed_history", default=None),
        )

    return {
        "back": back_button,
        "start": trip_buttons["start"],
        "pause": trip_buttons["pause"],
        "end": trip_buttons["end"],
    }
