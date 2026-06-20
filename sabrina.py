import math
import sys

import pygame

import main as dash


ORIGINAL_DRAW_BUTTON_ICON = dash.draw_button_icon


# =========================
# SABRINA THEME
# =========================

dash.BG_TOP = (25, 28, 48)
dash.BG_BOTTOM = (255, 235, 242)
dash.SURFACE = (255, 248, 250)
dash.SURFACE_2 = (242, 247, 255)
dash.SURFACE_HOVER = (255, 241, 248)
dash.STROKE_SOFT = (230, 188, 207)
dash.SHADOW = (93, 55, 81)

dash.TEXT = (42, 35, 54)
dash.MUTED = (117, 91, 117)
dash.FAINT = (154, 126, 151)

dash.BLUE = (117, 159, 229)
dash.CYAN = (71, 157, 194)
dash.GREEN = (78, 170, 137)
dash.YELLOW = (218, 159, 78)
dash.RED = (209, 78, 103)

BLUSH = (246, 170, 196)
POWDER = (170, 205, 246)
CREAM = (255, 250, 238)
ROSE = (222, 96, 134)
LIPSTICK = (190, 49, 83)
INK = (42, 35, 54)
GOLD = (222, 174, 92)

pygame.display.set_caption("DashBuddy OS - Sabrina Edition")


def draw_soft_gradient(surface, top, bottom):
    width, height = surface.get_size()
    for y in range(height):
        amount = y / max(1, height - 1)
        pygame.draw.line(surface, dash.lerp_color(top, bottom, amount), (0, y), (width, y))


def draw_sparkle(surface, x, y, size, color, alpha=130):
    sparkle = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
    center = size + 2
    pygame.draw.line(sparkle, (*color, alpha), (center, 2), (center, center * 2 - 2), 2)
    pygame.draw.line(sparkle, (*color, alpha), (2, center), (center * 2 - 2, center), 2)
    pygame.draw.line(sparkle, (*color, alpha - 35), (center - size // 2, center - size // 2), (center + size // 2, center + size // 2), 1)
    pygame.draw.line(sparkle, (*color, alpha - 35), (center + size // 2, center - size // 2), (center - size // 2, center + size // 2), 1)
    surface.blit(sparkle, (x - center, y - center))


def draw_background(surface, elapsed):
    width, height = surface.get_size()
    draw_soft_gradient(surface, dash.BG_TOP, dash.BG_BOTTOM)

    beams = pygame.Surface((width, height), pygame.SRCALPHA)
    pulse = (math.sin(elapsed * 1.4) + 1) / 2

    pygame.draw.polygon(
        beams,
        (*POWDER, 42),
        [(int(width * 0.05), 0), (int(width * 0.28), 0), (int(width * 0.50), height)],
    )
    pygame.draw.polygon(
        beams,
        (*BLUSH, 44),
        [(int(width * 0.70), 0), (int(width * 0.94), 0), (int(width * 0.46), height)],
    )
    pygame.draw.circle(beams, (*BLUSH, 42 + int(16 * pulse)), (int(width * 0.78), int(height * 0.12)), int(width * 0.28))
    pygame.draw.circle(beams, (*POWDER, 38), (int(width * 0.16), int(height * 0.20)), int(width * 0.24))
    surface.blit(beams, (0, 0))

    for index in range(14):
        x = int((index * 173 + elapsed * 12) % max(1, width))
        y = int(86 + ((index * 89) % max(1, height - 130)))
        size = 4 + index % 4
        color = GOLD if index % 3 == 0 else CREAM
        draw_sparkle(surface, x, y, size, color, 68)


def draw_panel(rect, fill=None, border=None, radius=18, shadow=True):
    fill = fill or dash.SURFACE
    border = border or dash.STROKE_SOFT

    if shadow:
        shadow_rect = rect.move(0, 9)
        shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (*dash.SHADOW, 45), shadow_surface.get_rect(), border_radius=radius)
        dash.screen.blit(shadow_surface, shadow_rect)

    pygame.draw.rect(dash.screen, fill, rect, border_radius=radius)
    pygame.draw.rect(dash.screen, border, rect, width=1, border_radius=radius)

    highlight = pygame.Surface((rect.width, max(24, rect.height // 3)), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 42), highlight.get_rect(), border_radius=radius)
    dash.screen.blit(highlight, rect.topleft)


def draw_pill(rect, label, color, fill_alpha=44):
    pill = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(pill, (*color, fill_alpha), pill.get_rect(), border_radius=rect.height // 2)
    pygame.draw.rect(pill, (*LIPSTICK, 120), pill.get_rect(), width=1, border_radius=rect.height // 2)
    dash.screen.blit(pill, rect)
    dash.draw_text(label, rect.x + 13, rect.y + 6, dash.fonts["tiny"], color, rect.width - 26)


def draw_top_bar(width, height):
    del height

    top_rect = pygame.Rect(0, 0, width, 78)
    pygame.draw.rect(dash.screen, (255, 246, 251), top_rect)
    pygame.draw.line(dash.screen, (224, 182, 205), (0, top_rect.bottom), (width, top_rect.bottom), 1)

    dash.draw_text("DashBuddy OS", 30, 17, dash.fonts["brand"], INK)
    if width >= 620:
        dash.draw_text("Sabrina Edition", 31, 43, dash.fonts["tiny"], ROSE)

    status = dash.status_details()
    pill_width = 110 if width >= 760 else 92
    draw_pill(pygame.Rect(width - pill_width - 30, 23, pill_width, 30), status["pill"], status["color"])

    if width >= 830:
        dash.draw_text("ESC to quit", width - pill_width - 132, 28, dash.fonts["small"], dash.FAINT)


def draw_mini_car(rect, status_color):
    body = pygame.Rect(rect.x + 20, rect.y + 30, rect.width - 40, rect.height - 56)
    cabin = pygame.Rect(rect.x + 52, rect.y + 10, rect.width - 104, 36)

    pygame.draw.rect(dash.screen, (255, 236, 245), body, border_radius=17)
    pygame.draw.rect(dash.screen, ROSE, body, width=2, border_radius=17)
    pygame.draw.rect(dash.screen, (216, 232, 255), cabin, border_radius=13)
    pygame.draw.line(dash.screen, (168, 138, 167), (cabin.centerx, cabin.y + 7), (cabin.centerx, cabin.bottom - 7), 1)
    pygame.draw.circle(dash.screen, (55, 43, 63), (body.x + 34, body.bottom), 15)
    pygame.draw.circle(dash.screen, (55, 43, 63), (body.right - 34, body.bottom), 15)
    pygame.draw.circle(dash.screen, status_color, (body.x + 34, body.bottom), 5)
    pygame.draw.circle(dash.screen, status_color, (body.right - 34, body.bottom), 5)

    if rect.width >= 150:
        draw_sparkle(dash.screen, body.right - 26, body.y + 10, 6, GOLD, 160)


def pet_message():
    if dash.telemetry_connected:
        return "DashBuddy: Sweet, live data is on stage."

    if dash.telemetry_connecting:
        return "DashBuddy: Looking for the OBD adapter before showtime."

    return "DashBuddy: Connect the OBD adapter so I can wake up."


def status_details():
    if dash.telemetry_connecting:
        return {
            "state": "connecting",
            "title": "Searching for OBD-II adapter",
            "message": "DashBuddy is backstage waiting for the adapter.",
            "color": dash.CYAN,
            "pill": "CONNECTING",
        }

    if dash.telemetry_connected:
        return {
            "state": "connected",
            "title": "OBD-II connected",
            "message": "Live telemetry is active.",
            "color": dash.GREEN,
            "pill": "LIVE",
        }

    return {
        "state": "offline",
        "title": "Connect OBD-II adapter",
        "message": "Live gauges and trips are waiting in the wings.",
        "color": dash.YELLOW,
        "pill": "OFFLINE",
    }


def draw_metric_arc(rect, value, max_value, color):
    center = (rect.centerx, rect.y + max(46, min(58, rect.height // 3 + 12)))
    radius = min(rect.width // 3, rect.height // 3, 58)
    arc_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    arc_rect.center = center

    start_angle = math.radians(205)
    end_angle = math.radians(335)
    pygame.draw.arc(dash.screen, (228, 198, 215), arc_rect, start_angle, end_angle, 8)

    try:
        progress = max(0.0, min(float(value) / max_value, 1.0))
    except (TypeError, ValueError):
        progress = 0.0

    progress_end = start_angle + (end_angle - start_angle) * progress
    pygame.draw.arc(dash.screen, color, arc_rect, start_angle, progress_end, 8)


def draw_status_icon(center, color, state):
    x, y = center
    pygame.draw.circle(dash.screen, CREAM, center, 26)
    pygame.draw.circle(dash.screen, color, center, 26, width=2)

    if state == "connected":
        pygame.draw.lines(dash.screen, color, False, [(x - 10, y), (x - 2, y + 8), (x + 13, y - 9)], 4)
    elif state == "connecting":
        pygame.draw.circle(dash.screen, color, center, 10, width=3)
        pygame.draw.line(dash.screen, color, (x + 8, y + 8), (x + 16, y + 16), 3)
    else:
        pygame.draw.line(dash.screen, color, (x - 10, y - 10), (x + 10, y + 10), 3)
        pygame.draw.line(dash.screen, color, (x + 10, y - 10), (x - 10, y + 10), 3)


def draw_speed_card(rect, speed):
    status = status_details()
    draw_panel(rect, fill=(255, 248, 252), border=ROSE, radius=24)

    dash.draw_text("SPEED", rect.x + 24, rect.y + 22, dash.fonts["tiny"], dash.FAINT, rect.width - 48)
    draw_sparkle(dash.screen, rect.right - 34, rect.y + 32, 7, GOLD, 160)

    speed_font = dash.fonts["speed"] if rect.width >= 380 and rect.height >= 240 else dash.fonts["speed_small"]
    speed_text = dash.fit_text(speed, speed_font, rect.width - 96)
    speed_surface = speed_font.render(str(speed_text), True, LIPSTICK)
    speed_rect = speed_surface.get_rect(center=(rect.centerx, rect.y + rect.height * 0.36))
    dash.screen.blit(speed_surface, speed_rect)

    unit_surface = dash.fonts["heading"].render("MPH", True, dash.MUTED)
    unit_rect = unit_surface.get_rect(center=(rect.centerx, speed_rect.bottom + 18))
    dash.screen.blit(unit_surface, unit_rect)

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

    dash.draw_text(pet_message(), message_x, message_y, dash.fonts["body_bold"], INK, max_width)
    dash.draw_text(status["message"], message_x, message_y + 30, dash.fonts["small"], dash.MUTED, max_width)


def draw_button_icon(rect, title, color):
    if title == "Music":
        center = rect.center
        pygame.draw.circle(dash.screen, color, center, 17, width=3)
        pygame.draw.line(dash.screen, color, (center[0] - 6, center[1] - 13), (center[0] - 6, center[1] + 9), 4)
        pygame.draw.line(dash.screen, color, (center[0] + 8, center[1] - 10), (center[0] + 8, center[1] + 12), 4)
        pygame.draw.line(dash.screen, color, (center[0] - 6, center[1] - 13), (center[0] + 8, center[1] - 10), 4)
        return

    ORIGINAL_DRAW_BUTTON_ICON(rect, title, color)


def install_theme():
    dash.draw_background = draw_background
    dash.draw_panel = draw_panel
    dash.draw_pill = draw_pill
    dash.draw_top_bar = draw_top_bar
    dash.draw_mini_car = draw_mini_car
    dash.draw_metric_arc = draw_metric_arc
    dash.draw_status_icon = draw_status_icon
    dash.draw_speed_card = draw_speed_card
    dash.draw_button_icon = draw_button_icon
    dash.pet_message = pet_message
    dash.status_details = status_details


def main():
    install_theme()
    dash.main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
