import math
import pygame


# =========================
# COLORS
# =========================

TEXT = (12, 24, 45)
MUTED = (82, 91, 110)
FAINT = (130, 145, 165)

WHITE = (255, 255, 255)
CARD = (255, 255, 255)
CARD_BLUE = (235, 248, 255)

BLUE = (38, 126, 245)
BLUE_DARK = (8, 43, 90)
BLUE_SOFT = (166, 213, 250)

GREEN = (48, 193, 131)
YELLOW = (255, 192, 53)
RED = (240, 91, 91)

BORDER = (147, 195, 231)
BORDER_SOFT = (202, 224, 241)
SHADOW = (90, 136, 172)

_background_cache = {}
_text_cache = {}

# =========================
# HELPERS
# =========================


def _font(fonts, preferred, fallback="body"):
    """
    Return the requested font when available.

    The fallback prevents the screen from crashing if a font key
    is missing from main.py.
    """
    return fonts.get(preferred, fonts[fallback])


def _draw_text(
    surface,
    text,
    x,
    y,
    font,
    color=TEXT,
):
    key = (str(text), id(font), color)

    rendered = _text_cache.get(key)

    if rendered is None:
        rendered = font.render(str(text), True, color)
        _text_cache[key] = rendered

    surface.blit(rendered, (x, y))
    return rendered.get_rect(topleft=(x, y))


def _draw_centered(
    surface,
    text,
    rect,
    font,
    color=TEXT,
):
    key = (str(text), id(font), color)

    rendered = _text_cache.get(key)

    if rendered is None:
        rendered = font.render(str(text), True, color)
        _text_cache[key] = rendered

    rendered_rect = rendered.get_rect(center=rect.center)
    surface.blit(rendered, rendered_rect)
    return rendered_rect


_round_rect_cache = {}


def _draw_round_rect_alpha(surface, rect, color, radius):
    key = (rect.width, rect.height, color, radius)

    cached = _round_rect_cache.get(key)

    if cached is None:
        cached = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        pygame.draw.rect(
            cached,
            color,
            cached.get_rect(),
            border_radius=radius,
        )

        _round_rect_cache[key] = cached

    surface.blit(cached, rect)


def _draw_panel(
    surface,
    rect,
    radius=22,
    fill=WHITE,
    border=BORDER_SOFT,
    shadow=True,
):
    """
    Draw one rounded dashboard card.
    """
    if shadow:
        shadow_rect = rect.move(0, 6)

        _draw_round_rect_alpha(
            surface,
            shadow_rect,
            (*SHADOW, 30),
            radius,
        )

    pygame.draw.rect(
        surface,
        fill,
        rect,
        border_radius=radius,
    )

    pygame.draw.rect(
        surface,
        border,
        rect,
        width=1,
        border_radius=radius,
    )


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


# =========================
# BACKGROUND AND HEADER
# =========================

def _draw_background(surface, width, height):
    key = (width, height)

    cached = _background_cache.get(key)

    if cached is None:
        cached = pygame.Surface((width, height))
        cached.fill((231, 246, 255))

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.circle(
            overlay,
            (255, 255, 255, 105),
            (int(width * 0.18), int(height * 0.28)),
            int(height * 0.38),
        )

        pygame.draw.circle(
            overlay,
            (180, 224, 255, 80),
            (int(width * 0.82), int(height * 0.72)),
            int(height * 0.42),
        )

        cached.blit(overlay, (0, 0))
        _background_cache[key] = cached

    surface.blit(cached, (0, 0))


def _draw_header(
    surface,
    width,
    fonts,
    mouse_pos,
    connected,
):
    header_height = 78

    header_rect = pygame.Rect(
        0,
        0,
        width,
        header_height,
    )

    _draw_round_rect_alpha(
        surface,
        header_rect,
        (255, 255, 255, 244),
        0,
    )

    pygame.draw.line(
        surface,
        BORDER_SOFT,
        (0, header_height - 1),
        (width, header_height - 1),
        1,
    )

    back_button = pygame.Rect(
        24,
        16,
        112,
        46,
    )

    hovered = back_button.collidepoint(mouse_pos)

    pygame.draw.rect(
        surface,
        BLUE_SOFT if hovered else CARD_BLUE,
        back_button,
        border_radius=15,
    )

    pygame.draw.rect(
        surface,
        BLUE if hovered else BORDER,
        back_button,
        width=1,
        border_radius=15,
    )

    _draw_centered(
        surface,
        "← Home",
        back_button,
        _font(fonts, "body_bold"),
        BLUE,
    )

    title_font = _font(fonts, "card_title", "heading")

    title_surface = title_font.render(
        "Vehicle Telemetry",
        True,
        TEXT,
    )

    title_rect = title_surface.get_rect(
        center=(width // 2, header_height // 2),
    )

    surface.blit(title_surface, title_rect)

    status_color = GREEN if connected else YELLOW
    status_text = "LIVE" if connected else "OFFLINE"

    status_width = 90
    status_rect = pygame.Rect(
        width - status_width - 24,
        21,
        status_width,
        36,
    )

    pygame.draw.rect(
        surface,
        (230, 249, 240) if connected else (255, 247, 221),
        status_rect,
        border_radius=18,
    )

    pygame.draw.circle(
        surface,
        status_color,
        (status_rect.x + 18, status_rect.centery),
        6,
    )

    _draw_text(
        surface,
        status_text,
        status_rect.x + 32,
        status_rect.y + 9,
        _font(fonts, "small"),
        status_color,
    )

    return back_button, header_height


# =========================
# GAUGES
# =========================

def _draw_arc_gauge(
    surface,
    rect,
    value,
    minimum,
    maximum,
    label,
    unit,
    fonts,
    warning_start=None,
    danger_start=None,
):
    """
    Draw a semi-circular gauge.

    The gauge converts the numeric value into an angle between
    200 degrees and 340 degrees.
    """
    _draw_panel(
        surface,
        rect,
        radius=26,
        fill=WHITE,
        border=BORDER,
    )

    _draw_text(
        surface,
        label,
        rect.x + 24,
        rect.y + 20,
        _font(fonts, "body_bold"),
        MUTED,
    )

    center = (
        rect.centerx,
        rect.y + int(rect.height * 0.64),
    )

    radius = int(min(rect.width, rect.height) * 0.34)
    line_width = max(10, radius // 8)

    start_angle = math.radians(200)
    end_angle = math.radians(340)

    gauge_box = pygame.Rect(
        center[0] - radius,
        center[1] - radius,
        radius * 2,
        radius * 2,
    )

    pygame.draw.arc(
        surface,
        (220, 230, 240),
        gauge_box,
        start_angle,
        end_angle,
        line_width,
    )

    normalized = (
        (value - minimum) /
        max(maximum - minimum, 1)
    )

    normalized = _clamp(normalized, 0.0, 1.0)

    progress_angle = start_angle + (
        end_angle - start_angle
    ) * normalized

    if (
        danger_start is not None
        and value >= danger_start
    ):
        gauge_color = RED
    elif (
        warning_start is not None
        and value >= warning_start
    ):
        gauge_color = YELLOW
    else:
        gauge_color = BLUE

    if normalized > 0:
        pygame.draw.arc(
            surface,
            gauge_color,
            gauge_box,
            start_angle,
            progress_angle,
            line_width,
        )

    needle_length = radius - 12

    needle_x = center[0] + int(
        math.cos(progress_angle) * needle_length
    )

    needle_y = center[1] + int(
        math.sin(progress_angle) * needle_length
    )

    pygame.draw.line(
        surface,
        gauge_color,
        center,
        (needle_x, needle_y),
        5,
    )

    pygame.draw.circle(
        surface,
        WHITE,
        center,
        10,
    )

    pygame.draw.circle(
        surface,
        gauge_color,
        center,
        6,
    )

    value_font = _font(fonts, "speed_small", "heading")
    value_text = f"{int(value)}"

    value_surface = value_font.render(
        value_text,
        True,
        TEXT,
    )

    value_rect = value_surface.get_rect(
        center=(
            rect.centerx,
            rect.y + int(rect.height * 0.56),
        )
    )

    surface.blit(value_surface, value_rect)

    unit_surface = _font(fonts, "small").render(
        unit,
        True,
        MUTED,
    )

    unit_rect = unit_surface.get_rect(
        center=(
            rect.centerx,
            value_rect.bottom + 14,
        )
    )

    surface.blit(unit_surface, unit_rect)

    minimum_surface = _font(fonts, "tiny").render(
        str(int(minimum)),
        True,
        FAINT,
    )

    maximum_surface = _font(fonts, "tiny").render(
        str(int(maximum)),
        True,
        FAINT,
    )

    surface.blit(
        minimum_surface,
        (
            rect.x + 34,
            rect.bottom - 40,
        ),
    )

    surface.blit(
        maximum_surface,
        (
            rect.right - maximum_surface.get_width() - 34,
            rect.bottom - 40,
        ),
    )


# =========================
# INFORMATION CARDS
# =========================

def _draw_metric_card(
    surface,
    rect,
    title,
    value,
    subtitle,
    fonts,
    accent=BLUE,
):
    _draw_panel(
        surface,
        rect,
        radius=20,
        fill=WHITE,
        border=BORDER_SOFT,
    )

    pygame.draw.circle(
        surface,
        accent,
        (rect.x + 26, rect.y + 28),
        7,
    )

    _draw_text(
        surface,
        title,
        rect.x + 44,
        rect.y + 17,
        _font(fonts, "small"),
        MUTED,
    )

    _draw_text(
        surface,
        value,
        rect.x + 22,
        rect.y + 52,
        _font(fonts, "heading"),
        TEXT,
    )

    _draw_text(
        surface,
        subtitle,
        rect.x + 22,
        rect.bottom - 30,
        _font(fonts, "tiny"),
        MUTED,
    )


def _engine_state(speed, rpm, connected):
    if not connected:
        return "Offline", YELLOW

    if rpm < 300:
        return "Engine Off", FAINT

    if speed < 1:
        return "Idling", YELLOW

    return "Driving", GREEN


def _coolant_state(coolant):
    if coolant <= 0:
        return "No reading", FAINT

    if coolant >= 230:
        return "Hot", RED

    if coolant >= 215:
        return "Warm", YELLOW

    return "Normal", GREEN


def _mpg_state(mpg, connected):
    if not connected:
        return "Waiting for OBD data", YELLOW

    if mpg <= 0:
        return "No fuel flow reading", FAINT

    if mpg >= 35:
        return "Efficient cruising", GREEN

    if mpg >= 24:
        return "Normal economy", BLUE

    return "Heavy fuel use", YELLOW


def _draw_diagnostics_card(
    surface,
    rect,
    dtc,
    fonts,
    connected,
):
    _draw_panel(
        surface,
        rect,
        radius=22,
        fill=WHITE,
        border=BORDER_SOFT,
    )

    _draw_text(
        surface,
        "Diagnostics",
        rect.x + 22,
        rect.y + 18,
        _font(fonts, "body_bold"),
        TEXT,
    )

    dtc_text = str(dtc).strip()

    no_codes = (
        not dtc_text
        or dtc_text.lower() in {
            "clear",
            "none",
            "[]",
            "offline",
        }
    )

    if not connected:
        status = "OBD adapter unavailable"
        status_color = YELLOW
        detail = "Connect the adapter to scan the vehicle."

    elif no_codes:
        status = "No trouble codes"
        status_color = GREEN
        detail = "The ECU is not reporting active faults."

    else:
        status = "Trouble code detected"
        status_color = RED
        detail = dtc_text

    icon_center = (
        rect.x + 42,
        rect.y + 72,
    )

    pygame.draw.circle(
        surface,
        status_color,
        icon_center,
        18,
    )

    if no_codes and connected:
        pygame.draw.lines(
            surface,
            WHITE,
            False,
            [
                (icon_center[0] - 8, icon_center[1]),
                (icon_center[0] - 2, icon_center[1] + 6),
                (icon_center[0] + 10, icon_center[1] - 8),
            ],
            4,
        )
    else:
        pygame.draw.line(
            surface,
            WHITE,
            (icon_center[0], icon_center[1] - 8),
            (icon_center[0], icon_center[1] + 3),
            4,
        )

        pygame.draw.circle(
            surface,
            WHITE,
            (icon_center[0], icon_center[1] + 10),
            2,
        )

    _draw_text(
        surface,
        status,
        rect.x + 72,
        rect.y + 52,
        _font(fonts, "body_bold"),
        status_color,
    )

    _draw_text(
        surface,
        detail,
        rect.x + 72,
        rect.y + 83,
        _font(fonts, "small"),
        MUTED,
    )


# =========================
# GRAPH
# =========================

def _draw_live_graph(
    surface,
    rect,
    values,
    maximum,
    title,
    unit,
    fonts,
):
    _draw_panel(
        surface,
        rect,
        radius=22,
        fill=WHITE,
        border=BORDER_SOFT,
    )

    _draw_text(
        surface,
        title,
        rect.x + 22,
        rect.y + 18,
        _font(fonts, "body_bold"),
        TEXT,
    )

    _draw_text(
        surface,
        unit,
        rect.right - 55,
        rect.y + 21,
        _font(fonts, "tiny"),
        MUTED,
    )

    graph_rect = pygame.Rect(
        rect.x + 22,
        rect.y + 58,
        rect.width - 44,
        rect.height - 82,
    )

    for index in range(4):
        y = graph_rect.y + int(
            graph_rect.height * index / 3
        )

        pygame.draw.line(
            surface,
            (225, 234, 242),
            (graph_rect.x, y),
            (graph_rect.right, y),
            1,
        )

    if len(values) < 2:
        _draw_centered(
            surface,
            "Waiting for data...",
            graph_rect,
            _font(fonts, "small"),
            MUTED,
        )
        return

    visible_values = values[-60:]

    points = []

    for index, value in enumerate(visible_values):
        normalized = _clamp(
            _safe_float(value) / max(maximum, 1),
            0.0,
            1.0,
        )

        x = graph_rect.x + int(
            index /
            max(len(visible_values) - 1, 1) *
            graph_rect.width
        )

        y = graph_rect.bottom - int(
            normalized * graph_rect.height
        )

        points.append((x, y))

    if len(points) >= 2:
        pygame.draw.lines(
            surface,
            BLUE,
            False,
            points,
            3,
        )

        pygame.draw.circle(
            surface,
            BLUE,
            points[-1],
            5,
        )


# =========================
# MAIN DRAW FUNCTION
# =========================

def draw_telemetry_screen(
    surface,
    width,
    height,
    fonts,
    mouse_pos,
    speed,
    rpm,
    coolant,
    dtc,
    connected,
    speed_history=None,
    instant_mpg=0.0,
):
    """
    Draw the complete vehicle telemetry dashboard.

    The function only displays telemetry. It does not query the car or
    calculate trip statistics.

    Returns a dictionary of clickable rectangles for main.py.
    """
    speed = max(0.0, _safe_float(speed))
    rpm = max(0.0, _safe_float(rpm))
    coolant = max(0.0, _safe_float(coolant))
    instant_mpg = max(0.0, _safe_float(instant_mpg))

    if speed_history is None:
        speed_history = []

    _draw_background(
        surface,
        width,
        height,
    )

    back_button, header_height = _draw_header(
        surface,
        width,
        fonts,
        mouse_pos,
        connected,
    )

    margin = 24
    gap = 16

    content_top = header_height + 20
    content_height = height - content_top - margin

    left_width = int((width - margin * 2 - gap) * 0.56)
    right_width = width - margin * 2 - gap - left_width

    left_x = margin
    right_x = left_x + left_width + gap

    top_gauge_height = int(content_height * 0.50)
    bottom_height = content_height - top_gauge_height - gap

    gauge_gap = 16
    gauge_width = (left_width - gauge_gap) // 2

    speed_rect = pygame.Rect(
        left_x,
        content_top,
        gauge_width,
        top_gauge_height,
    )

    rpm_rect = pygame.Rect(
        speed_rect.right + gauge_gap,
        content_top,
        gauge_width,
        top_gauge_height,
    )

    _draw_arc_gauge(
        surface=surface,
        rect=speed_rect,
        value=speed,
        minimum=0,
        maximum=120,
        label="Vehicle Speed",
        unit="MPH",
        fonts=fonts,
        warning_start=75,
        danger_start=95,
    )

    _draw_arc_gauge(
        surface=surface,
        rect=rpm_rect,
        value=rpm,
        minimum=0,
        maximum=7000,
        label="Engine RPM",
        unit="RPM",
        fonts=fonts,
        warning_start=4500,
        danger_start=6000,
    )

    graph_rect = pygame.Rect(
        left_x,
        speed_rect.bottom + gap,
        left_width,
        bottom_height,
    )

    _draw_live_graph(
        surface=surface,
        rect=graph_rect,
        values=speed_history,
        maximum=120,
        title="Speed History",
        unit="MPH",
        fonts=fonts,
    )

    metric_gap = 14
    metric_height = int(content_height * 0.22)

    metric_width = (right_width - metric_gap) // 2

    coolant_rect = pygame.Rect(
        right_x,
        content_top,
        metric_width,
        metric_height,
    )

    engine_rect = pygame.Rect(
        coolant_rect.right + metric_gap,
        content_top,
        metric_width,
        metric_height,
    )

    coolant_label, coolant_color = _coolant_state(
        coolant
    )

    _draw_metric_card(
        surface=surface,
        rect=coolant_rect,
        title="Coolant",
        value=(
            f"{int(coolant)}°F"
            if coolant > 0
            else "--"
        ),
        subtitle=coolant_label,
        fonts=fonts,
        accent=coolant_color,
    )

    engine_label, engine_color = _engine_state(
        speed,
        rpm,
        connected,
    )

    _draw_metric_card(
        surface=surface,
        rect=engine_rect,
        title="Engine State",
        value=engine_label,
        subtitle=(
            f"{int(rpm)} RPM"
            if connected
            else "No live telemetry"
        ),
        fonts=fonts,
        accent=engine_color,
    )

    live_rect = pygame.Rect(
        right_x,
        coolant_rect.bottom + gap,
        right_width,
        int(content_height * 0.28),
    )

    _draw_panel(
        surface,
        live_rect,
        radius=22,
        fill=WHITE,
        border=BORDER_SOFT,
    )

    mpg_label, mpg_color = _mpg_state(
        instant_mpg,
        connected,
    )

    pygame.draw.circle(
        surface,
        mpg_color,
        (live_rect.x + 28, live_rect.y + 28),
        8,
    )

    _draw_text(
        surface,
        "Fuel Economy",
        live_rect.x + 44,
        live_rect.y + 18,
        _font(fonts, "body_bold"),
        TEXT,
    )

    mpg_value = (
        f"{instant_mpg:.1f}"
        if connected and instant_mpg > 0
        else "--"
    )

    mpg_surface = _font(fonts, "speed_tiny", "heading").render(
        mpg_value,
        True,
        TEXT,
    )

    mpg_rect = mpg_surface.get_rect(
        topleft=(
            live_rect.x + 22,
            live_rect.y + 52,
        )
    )

    surface.blit(mpg_surface, mpg_rect)

    _draw_text(
        surface,
        "MPG",
        mpg_rect.right + 8,
        mpg_rect.y + 18,
        _font(fonts, "body_bold"),
        MUTED,
    )

    _draw_text(
        surface,
        mpg_label,
        live_rect.x + 22,
        mpg_rect.bottom + 2,
        _font(fonts, "tiny"),
        mpg_color,
    )

    readings = [
        ("Speed", f"{speed:.1f} MPH"),
        ("RPM", f"{rpm:.0f}"),
        (
            "Coolant",
            f"{coolant:.0f}°F" if coolant > 0 else "--",
        ),
        (
            "Connection",
            "Connected" if connected else "Offline",
        ),
    ]

    row_y = live_rect.y + 55
    row_height = 24
    row_x = live_rect.x + int(live_rect.width * 0.56)
    show_readings = live_rect.width >= 430

    if show_readings:
        for label, value in readings:
            _draw_text(
                surface,
                label,
                row_x,
                row_y,
                _font(fonts, "small"),
                MUTED,
            )

            value_surface = _font(
                fonts,
                "small",
            ).render(
                value,
                True,
                TEXT,
            )

            surface.blit(
                value_surface,
                (
                    live_rect.right -
                    value_surface.get_width() -
                    22,
                    row_y,
                ),
            )

            row_y += row_height

    diagnostics_rect = pygame.Rect(
        right_x,
        live_rect.bottom + gap,
        right_width,
        content_top + content_height -
        live_rect.bottom -
        gap,
    )

    _draw_diagnostics_card(
        surface=surface,
        rect=diagnostics_rect,
        dtc=dtc,
        fonts=fonts,
        connected=connected,
    )

    return {
        "back": back_button,
    }
