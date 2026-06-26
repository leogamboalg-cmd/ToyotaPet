# main.py
import math
import os
import sys
import threading
from datetime import datetime
import subprocess
import pygame

from car_telemetry import CarTelemetry
from screens.trips_screen import draw_trips_screen
from trip_manager_solo import TripManager
from trip_history import get_recent_trips, save_trip
from screens.telemetry_screen import draw_telemetry_screen
from mpg_calculator import ExtendedTelemetry
from pet_manager import PetManager

# =========================
# BASIC SETUP
# =========================

WIDTH, HEIGHT = 1280, 720
MIN_WIDTH, MIN_HEIGHT = 800, 480
FPS = 60
carplay_process = None

CARPLAY_PATH = "/home/leog0495/Desktop/Carplay.AppImage"
trip_manager = TripManager()
pygame.init()
try:
    pygame.mixer.init()
except pygame.error as error:
    print(f"[Audio] Mixer failed to initialize: {error}")
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("DashBuddy OS")
clock = pygame.time.Clock()


# =========================
# ASSET PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "assets", "icons")
SOUND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

SOUND_PATHS = {
    "hard_brake": os.path.join(SOUND_DIR, "hard_brake.mp3"),
    "fast_acceleration": os.path.join(
        SOUND_DIR,
        "fast_acceleration.mp3",
    ),
    "high_speed": os.path.join(SOUND_DIR, "high_speed.mp3"),
}
pet_sounds = {}

for name, path in SOUND_PATHS.items():
    if not os.path.exists(path):
        print(f"[Missing sound] {name}: {path}")
        continue

    try:
        pet_sounds[name] = pygame.mixer.Sound(path)
        print(f"[Sound loaded] {name}")
    except pygame.error as error:
        print(f"[Sound load failed] {name}: {error}")

pet_manager = PetManager(pet_sounds)

ASSET_PATHS = {
    "background": os.path.join(ICON_DIR, "homepageBackgroundOverlay.png"),
    "bmo": os.path.join(ICON_DIR, "bmo.png"),
    "carplay": os.path.join(ICON_DIR, "carplay.png"),
    "trips": os.path.join(ICON_DIR, "trips.png"),
    "telemetry": os.path.join(ICON_DIR, "telemetry.png"),
    "settings": os.path.join(ICON_DIR, "settings.png"),
    "apps": os.path.join(ICON_DIR, "apps.png"),
    "wifi": os.path.join(ICON_DIR, "wifi.png"),
}

# =========================
# SCREEN NAVIGATION
# =========================

current_screen = "home"

click_targets = {
    "carplay": None,
    "trips": None,
    "telemetry": None,
    "settings": None,
    "apps": None,
    "media": None,
}

# =========================
# COLORS - CARTOON ROADTRIP THEME
# =========================

TEXT = (12, 24, 45)
MUTED = (82, 91, 110)
FAINT = (130, 145, 165)

WHITE = (255, 255, 255)
CARD = (255, 255, 255)
CARD_SOFT = (247, 252, 255)
CARD_BLUE = (235, 248, 255)

BLUE = (38, 126, 245)
BLUE_DARK = (8, 43, 90)
BLUE_SOFT = (166, 213, 250)

TEAL = (31, 188, 175)
GREEN = (48, 193, 131)
YELLOW = (255, 192, 53)
RED = (240, 91, 91)

BORDER = (147, 195, 231)
BORDER_SOFT = (202, 224, 241)

SHADOW = (90, 136, 172)

BOTTOM_NAV = (252, 254, 255)
TOP_BAR = (255, 255, 255)


# =========================
# FONTS
# =========================

FONT_NAME = "segoeui"


def make_font(size, bold=False):
    return pygame.font.SysFont(FONT_NAME, size, bold=bold)


fonts = {
    "brand": make_font(24, True),
    "brand_small": make_font(20, True),
    "card_title": make_font(25, True),
    "card_title_small": make_font(20, True),
    "heading": make_font(24, True),
    "body": make_font(17),
    "body_bold": make_font(17, True),
    "small": make_font(14),
    "tiny": make_font(12),
    "speed": make_font(78, True),
    "speed_small": make_font(56, True),
    "speed_tiny": make_font(42, True),
}


# =========================
# TELEMETRY STATE
# =========================

telemetry = None
extended_telemetry = None
telemetry_connected = False
telemetry_connecting = True
telemetry_error = ""


def connect_obd_in_background():
    """
    Tries to connect to the OBD adapter in a background thread.

    This keeps the Pygame window responsive. If the adapter fails,
    the UI still opens and shows offline data instead of crashing.
    """
    global telemetry
    global extended_telemetry
    global telemetry_connected
    global telemetry_connecting
    global telemetry_error

    try:
        telemetry = CarTelemetry()
        extended_telemetry = ExtendedTelemetry(telemetry)
        telemetry.start()
        telemetry_connected = True
        telemetry_error = ""
    except Exception as e:
        telemetry = None
        extended_telemetry = None
        telemetry_connected = False
        telemetry_error = str(e)
        print(f"[OBD Connection Failed] {e}")
    finally:
        telemetry_connecting = False


obd_thread = threading.Thread(target=connect_obd_in_background, daemon=True)
obd_thread.start()


# =========================
# ASSET LOADING
# =========================

image_cache = {}


def load_image(name):
    """
    Loads an image once and stores it in image_cache.

    convert_alpha() keeps transparent PNG edges smooth.
    """
    if name in image_cache:
        return image_cache[name]

    path = ASSET_PATHS.get(name)
    if not path or not os.path.exists(path):
        print(f"[Missing asset] {name}: {path}")
        image_cache[name] = None
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        image_cache[name] = img
        return img
    except Exception as e:
        print(f"[Asset load failed] {name}: {e}")
        image_cache[name] = None
        return None


def blit_image_fit(surface, image, rect, contain=True, alpha=255):
    """
    Draws an image inside a rectangle.

    contain=True keeps the whole image visible.
    contain=False fills the rectangle and crops extra edges.
    """
    if image is None:
        return

    iw, ih = image.get_size()
    rw, rh = rect.size

    if iw <= 0 or ih <= 0 or rw <= 0 or rh <= 0:
        return

    if contain:
        scale = min(rw / iw, rh / ih)
    else:
        scale = max(rw / iw, rh / ih)

    new_w = max(1, int(iw * scale))
    new_h = max(1, int(ih * scale))

    scaled = pygame.transform.smoothscale(image, (new_w, new_h))

    if alpha < 255:
        scaled = scaled.copy()
        scaled.set_alpha(alpha)

    x = rect.centerx - new_w // 2
    y = rect.centery - new_h // 2

    if contain:
        surface.blit(scaled, (x, y))
    else:
        crop = pygame.Rect(
            max(0, (new_w - rw) // 2),
            max(0, (new_h - rh) // 2),
            rw,
            rh,
        )
        surface.blit(scaled, rect.topleft, crop)


# =========================
# UI HELPERS
# =========================

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


def draw_centered_text(text, rect, font, color=TEXT):
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return text_rect


def draw_round_rect_alpha(surface, rect, color, radius):
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, temp.get_rect(), border_radius=radius)
    surface.blit(temp, rect)


def draw_panel(rect, radius=24, fill=CARD, border=BORDER, shadow=True, shadow_offset=7):
    """
    Draws the clean rounded white card style used across the dashboard.
    """
    if shadow:
        shadow_rect = rect.move(0, shadow_offset)
        draw_round_rect_alpha(
            screen,
            shadow_rect,
            (*SHADOW, 32),
            radius,
        )

    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width=1, border_radius=radius)


def draw_soft_circle(center, radius, color=(229, 246, 255), alpha=220):
    circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(circle, (*color, alpha), (radius, radius), radius)
    screen.blit(circle, (center[0] - radius, center[1] - radius))


def draw_background(width, height):
    """
    Uses the generated cartoon road image as the background.
    It fills the screen and crops slightly if the window ratio changes.
    """
    bg = load_image("background")

    if bg:
        blit_image_fit(screen, bg, pygame.Rect(
            0, 0, width, height), contain=False)
    else:
        screen.fill((232, 247, 255))

    # Soft white wash so cards stay readable.
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 70))
    screen.blit(overlay, (0, 0))


def get_time_text():
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def status_details():
    if telemetry_connecting:
        return {
            "state": "connecting",
            "title": "Searching",
            "message": "Looking for OBD",
            "color": BLUE,
            "pill": "CONNECTING",
        }

    if telemetry_connected:
        return {
            "state": "connected",
            "title": "Connected",
            "message": "Live data active",
            "color": GREEN,
            "pill": "LIVE",
        }

    return {
        "state": "offline",
        "title": "Offline",
        "message": "Connect OBD adapter",
        "color": YELLOW,
        "pill": "OFFLINE",
    }


def pet_message():
    if telemetry_connected:
        return "All systems look good!"

    if telemetry_connecting:
        return "Looking for your OBD adapter..."

    return "Plug in OBD so I can wake up."


def home_message():
    if telemetry_connected:
        return "Good morning! Dashboard systems go."

    if telemetry_connecting:
        return "Starting up. Searching for your car data."

    return "Home is ready. OBD features are paused."


def safe_data():
    """
    Gets telemetry if connected.

    The UI should never crash just because OBD returns something weird.
    """
    if telemetry_connected and telemetry:
        try:
            speed, rpm, coolant, dtc = telemetry.get_data()
            return speed, rpm, coolant, dtc
        except Exception:
            return 0, 0, 0, "Offline"

    return 0, 0, 0, "Offline"


def safe_mpg():
    """
    Calculates instant fuel economy if the OBD adapter is connected.
    """
    if telemetry_connected and extended_telemetry:
        try:
            data = extended_telemetry.get_data()
            return max(0.0, float(data.get("instant_mpg", 0.0)))
        except Exception:
            return 0.0

    return 0.0


# =========================
# TOP BAR
# =========================

def draw_wifi_icon(x, y, color=TEXT):
    pygame.draw.arc(screen, color, pygame.Rect(x, y, 30, 24),
                    math.radians(205), math.radians(335), 3)
    pygame.draw.arc(screen, color, pygame.Rect(
        x + 6, y + 7, 18, 14), math.radians(205), math.radians(335), 3)
    pygame.draw.circle(screen, color, (x + 15, y + 22), 3)


def draw_bluetooth_icon(x, y, color=TEXT):
    points_top = [(x + 8, y), (x + 20, y + 10), (x + 8, y + 20), (x + 8, y)]
    points_bottom = [(x + 8, y + 20), (x + 20, y + 30),
                     (x + 8, y + 40), (x + 8, y + 20)]
    pygame.draw.lines(screen, color, False, points_top, 3)
    pygame.draw.lines(screen, color, False, points_bottom, 3)
    pygame.draw.line(screen, color, (x, y + 10), (x + 20, y + 30), 3)
    pygame.draw.line(screen, color, (x, y + 30), (x + 20, y + 10), 3)


def draw_top_bar(width, top_h):
    rect = pygame.Rect(0, 0, width, top_h)
    draw_round_rect_alpha(screen, rect, (*TOP_BAR, 244), 0)
    pygame.draw.line(screen, BORDER_SOFT, (0, top_h - 1),
                     (width, top_h - 1), 1)

    compact = width < 900

    brand_font = fonts["brand_small"] if compact else fonts["brand"]
    draw_text("DashBuddy", 28, top_h // 2 -
              brand_font.get_height() // 2, brand_font, TEXT)

    os_badge_x = 190 if not compact else 164
    os_badge = pygame.Rect(os_badge_x, top_h // 2 - 16, 38, 32)
    pygame.draw.rect(screen, BLUE, os_badge, border_radius=8)
    draw_centered_text("OS", os_badge, fonts["body_bold"], WHITE)

    car_pill_w = 220 if not compact else 180
    car_pill = pygame.Rect(width // 2 - car_pill_w // 2,
                           top_h // 2 - 25, car_pill_w, 50)
    pygame.draw.rect(screen, (250, 253, 255), car_pill, border_radius=25)
    pygame.draw.rect(screen, BORDER_SOFT, car_pill, width=1, border_radius=25)

    car_text = "Toyota Corolla" if not compact else "Corolla"
    draw_centered_text(car_text, car_pill, fonts["body_bold"], TEXT)

    if width >= 820:
        wifi_icon = load_image("wifi")

        wifi_rect = pygame.Rect(
            width - 220,
            top_h // 2 - 17,
            34,
            34,
        )

        blit_image_fit(screen, wifi_icon, wifi_rect, contain=True)

        draw_bluetooth_icon(width - 155, top_h // 2 - 20)

        draw_text(
            get_time_text(),
            width - 92,
            top_h // 2 - 12,
            fonts["body_bold"],
            TEXT,
        )
# =========================
# CARDS
# =========================


def draw_buddy_panel(rect, pet_data):
    draw_panel(rect, radius=28, fill=(255, 255, 255),
               border=BORDER, shadow=True)

    title_font = fonts["card_title"] if rect.width >= 300 else fonts["card_title_small"]
    draw_text("Buddy", rect.x + 28, rect.y + 24,
              title_font, TEXT, rect.width - 56)

    bubble_w = min(rect.width - 64, 230)
    bubble_h = 86
    bubble = pygame.Rect(rect.x + 26, rect.y + 78, bubble_w, bubble_h)

    pygame.draw.rect(screen, WHITE, bubble, border_radius=16)
    pygame.draw.rect(screen, BORDER, bubble, width=1, border_radius=16)

    # Speech bubble tail.
    tail = [
        (bubble.right - 6, bubble.centery + 10),
        (bubble.right + 20, bubble.centery + 20),
        (bubble.right - 6, bubble.centery + 28),
    ]
    pygame.draw.polygon(screen, WHITE, tail)
    pygame.draw.lines(screen, BORDER, False, [tail[0], tail[1], tail[2]], 1)

    draw_text(
        pet_data["message"],
        bubble.x + 16,
        bubble.y + 16,
        fonts["body_bold"],
        TEXT,
        bubble.width - 32,
    )
    draw_text("I'm here to make", bubble.x + 16, bubble.y +
              46, fonts["small"], TEXT, bubble.width - 32)
    draw_text("your drive awesome.", bubble.x + 16, bubble.y +
              66, fonts["small"], TEXT, bubble.width - 32)

    # Small sparkle decoration.
    star_x = rect.right - 44
    star_y = rect.y + 130
    pygame.draw.line(screen, BLUE, (star_x, star_y - 14),
                     (star_x, star_y + 14), 2)
    pygame.draw.line(screen, BLUE, (star_x - 14, star_y),
                     (star_x + 14, star_y), 2)

    bmo = load_image("bmo")
    img_rect = pygame.Rect(
        rect.x + int(rect.width * 0.20),
        rect.y + int(rect.height * 0.34),
        int(rect.width * 0.60),
        int(rect.height * 0.45),
    )
    blit_image_fit(screen, bmo, img_rect, contain=True)

    status_bar = pygame.Rect(
        rect.x + 24, rect.bottom - 54, rect.width - 48, 36)
    pygame.draw.rect(screen, (242, 249, 255), status_bar, border_radius=18)
    pygame.draw.circle(
        screen, BLUE, (status_bar.x + 28, status_bar.centery), 9)
    draw_text(pet_message(), status_bar.x + 52, status_bar.y +
              8, fonts["small"], BLUE, status_bar.width - 70)


def draw_app_card(rect, label, icon_name, mouse_pos, enabled=True):
    hovered = rect.collidepoint(mouse_pos) and enabled

    fill = (255, 255, 255) if not hovered else (244, 251, 255)
    border = BLUE if hovered else BORDER

    draw_panel(rect, radius=22, fill=fill, border=border, shadow=True)

    icon = load_image(icon_name)

    circle_radius = min(rect.width, rect.height) // 3
    circle_radius = max(46, min(circle_radius, 72))

    circle_center = (
        rect.centerx,
        rect.y + int(rect.height * 0.36),
    )

    draw_soft_circle(circle_center, circle_radius, (229, 246, 255), 235)

    # The PNG itself already has padding, so the box needs to be large.
    icon_size = int(circle_radius * 1.75)

    icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
    icon_rect.center = circle_center

    blit_image_fit(screen, icon, icon_rect, contain=True)

    label_font = fonts["heading"] if rect.height >= 145 else fonts["body_bold"]

    label_rect = pygame.Rect(
        rect.x + 8,
        rect.bottom - 52,
        rect.width - 16,
        36,
    )

    draw_centered_text(label, label_rect, label_font, TEXT)


def draw_speed_card(rect, speed):
    draw_panel(rect, radius=24, fill=WHITE, border=BORDER_SOFT, shadow=True)

    draw_text("Speed", rect.x + 24, rect.y + 22, fonts["body_bold"], MUTED)

    try:
        speed_num = int(float(speed))
    except Exception:
        speed_num = 0

    if rect.height < 120:
        speed_font = fonts["speed_tiny"]
    elif rect.width < 250:
        speed_font = fonts["speed_small"]
    else:
        speed_font = fonts["speed"]

    speed_surface = speed_font.render(str(speed_num), True, TEXT)
    unit_surface = fonts["body_bold"].render("MPH", True, MUTED)

    number_y = rect.y + int(rect.height * 0.33)
    number_x = rect.centerx - speed_surface.get_width() // 2 - 12

    screen.blit(speed_surface, (number_x, number_y))

    unit_x = number_x + speed_surface.get_width() + 10
    unit_y = number_y + speed_surface.get_height() - unit_surface.get_height() - 10
    screen.blit(unit_surface, (unit_x, unit_y))

    bar_w = rect.width - 48
    bar_h = 10

    # Push the bar lower so it never crosses the number.
    bar_y = max(
        number_y + speed_surface.get_height() + 8,
        rect.bottom - 38,
    )

    # Safety clamp in case the card becomes short.
    bar_y = min(bar_y, rect.bottom - 24)

    bar = pygame.Rect(rect.x + 24, bar_y, bar_w, bar_h)

    pygame.draw.rect(screen, (218, 231, 242), bar, border_radius=bar_h // 2)

    progress = max(0, min(speed_num / 120, 1))
    fill = pygame.Rect(bar.x, bar.y, int(bar.width * progress), bar.height)

    if fill.width > 0:
        pygame.draw.rect(screen, BLUE, fill, border_radius=bar_h // 2)


def draw_obd_card(rect):
    status = status_details()

    draw_panel(rect, radius=22, fill=WHITE, border=BORDER_SOFT, shadow=True)

    draw_text("OBD Status", rect.x + 22, rect.y + 20,
              fonts["body_bold"], (73, 95, 88), rect.width - 44)

    inner = pygame.Rect(rect.x + 18, rect.y + 70,
                        rect.width - 36, rect.height - 92)
    inner_h = max(54, min(inner.height, 72))
    inner = pygame.Rect(inner.x, inner.y, inner.width, inner_h)

    pygame.draw.rect(screen, (224, 250, 246), inner, border_radius=16)

    icon_box = pygame.Rect(inner.x + 16, inner.centery - 18, 36, 36)
    pygame.draw.rect(screen, (208, 245, 240), icon_box, border_radius=8)
    pygame.draw.rect(screen, (77, 145, 152), icon_box,
                     width=2, border_radius=8)

    pygame.draw.rect(screen, (82, 140, 151), (icon_box.x + 7,
                     icon_box.y + 9, 22, 13), width=2, border_radius=3)
    for i in range(3):
        pygame.draw.circle(screen, (82, 140, 151),
                           (icon_box.x + 10 + i * 7, icon_box.y + 28), 2)

    check_center = (inner.x + 76, inner.centery)
    pygame.draw.circle(screen, status["color"], check_center, 14)
    if status["state"] == "connected":
        pygame.draw.lines(
            screen,
            WHITE,
            False,
            [
                (check_center[0] - 6, check_center[1]),
                (check_center[0] - 1, check_center[1] + 5),
                (check_center[0] + 8, check_center[1] - 7),
            ],
            3,
        )
    elif status["state"] == "connecting":
        pygame.draw.circle(screen, WHITE, check_center, 6, width=2)
    else:
        pygame.draw.line(
            screen, WHITE, (check_center[0] - 6, check_center[1] - 6), (check_center[0] + 6, check_center[1] + 6), 3)
        pygame.draw.line(
            screen, WHITE, (check_center[0] + 6, check_center[1] - 6), (check_center[0] - 6, check_center[1] + 6), 3)

    text_x = inner.x + 100
    draw_text(status["title"], text_x, inner.y + 14,
              fonts["body_bold"], TEXT, inner.right - text_x - 10)
    draw_text(status["message"], text_x, inner.y + 39,
              fonts["small"], MUTED, inner.right - text_x - 10)


def draw_weather_card(rect):
    draw_panel(rect, radius=22, fill=WHITE, border=BORDER_SOFT, shadow=True)

    sun_x = rect.x + 36
    sun_y = rect.centery
    pygame.draw.circle(screen, YELLOW, (sun_x, sun_y), 13)

    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = sun_x + int(math.cos(rad) * 20)
        y1 = sun_y + int(math.sin(rad) * 20)
        x2 = sun_x + int(math.cos(rad) * 27)
        y2 = sun_y + int(math.sin(rad) * 27)
        pygame.draw.line(screen, YELLOW, (x1, y1), (x2, y2), 2)

    draw_text("72°F", rect.x + 78, rect.y + 22,
              fonts["body_bold"], TEXT, rect.width - 92)
    draw_text("Sunny", rect.x + 78, rect.y + 48,
              fonts["small"], MUTED, rect.width - 92)


def draw_message_bar(rect):
    draw_panel(rect, radius=20, fill=(252, 254, 255),
               border=BORDER, shadow=True)

    pygame.draw.circle(screen, BLUE, (rect.x + 30, rect.centery), 7)
    draw_text(home_message(), rect.x + 56, rect.y + 19,
              fonts["body"], TEXT, rect.width - 110)

    # Right chevron.
    cx = rect.right - 34
    cy = rect.centery
    pygame.draw.line(screen, TEXT, (cx - 5, cy - 8), (cx + 4, cy), 3)
    pygame.draw.line(screen, TEXT, (cx + 4, cy), (cx - 5, cy + 8), 3)


def draw_bottom_nav(rect):
    draw_round_rect_alpha(screen, rect, (*BOTTOM_NAV, 245), 28)
    pygame.draw.rect(screen, BORDER_SOFT, rect, width=1, border_radius=28)

    items = [
        ("Home", "home"),
        ("Media", "media"),
        ("Apps", "apps"),
        ("Alerts", "alerts"),
        ("Vehicle", "vehicle"),
    ]

    slot_w = rect.width / len(items)

    for i, (label, kind) in enumerate(items):
        center_x = int(rect.x + slot_w * i + slot_w / 2)
        icon_y = rect.y + 28
        label_y = rect.y + 54

        active = i == 0
        color = BLUE if active else (62, 70, 84)

        if kind == "home":
            pygame.draw.polygon(screen, color, [
                (center_x - 12, icon_y + 7),
                (center_x, icon_y - 6),
                (center_x + 12, icon_y + 7),
            ])
            pygame.draw.rect(screen, color, pygame.Rect(
                center_x - 9, icon_y + 7, 18, 15), border_radius=3)

        elif kind == "media":
            pygame.draw.line(screen, color, (center_x - 3,
                             icon_y - 8), (center_x - 3, icon_y + 12), 3)
            pygame.draw.line(screen, color, (center_x + 9,
                             icon_y - 5), (center_x + 9, icon_y + 14), 3)
            pygame.draw.circle(screen, color, (center_x - 8, icon_y + 14), 5)
            pygame.draw.circle(screen, color, (center_x + 4, icon_y + 16), 5)

        elif kind == "apps":
            for row in range(3):
                for col in range(3):
                    pygame.draw.circle(
                        screen, color, (center_x - 10 + col * 10, icon_y - 5 + row * 10), 3)

        elif kind == "alerts":
            pygame.draw.arc(screen, color, pygame.Rect(
                center_x - 10, icon_y - 8, 20, 22), math.radians(200), math.radians(-20), 3)
            pygame.draw.line(screen, color, (center_x - 11,
                             icon_y + 11), (center_x + 11, icon_y + 11), 3)
            pygame.draw.circle(screen, color, (center_x, icon_y + 16), 3)

        elif kind == "vehicle":
            pygame.draw.rect(screen, color, pygame.Rect(
                center_x - 14, icon_y - 2, 28, 14), width=2, border_radius=5)
            pygame.draw.circle(screen, color, (center_x - 8, icon_y + 14), 3)
            pygame.draw.circle(screen, color, (center_x + 8, icon_y + 14), 3)

        label_surface = fonts["small"].render(label, True, color)
        label_rect = label_surface.get_rect(center=(center_x, label_y))
        screen.blit(label_surface, label_rect)


def launch_carplay():
    """
    Launches the CarPlay AppImage.

    poll() returns None while the program is still running, which prevents
    DashBuddy from opening multiple copies when the button is clicked twice.
    """
    global carplay_process

    if carplay_process is not None and carplay_process.poll() is None:
        print("[CarPlay] Already running")
        return

    if not os.path.exists(CARPLAY_PATH):
        print(f"[CarPlay] AppImage not found: {CARPLAY_PATH}")
        return

    try:
        carplay_process = subprocess.Popen(
            [CARPLAY_PATH],
            cwd=os.path.dirname(CARPLAY_PATH),
        )

        print("[CarPlay] Launched successfully")

    except PermissionError:
        print("[CarPlay] Permission denied.")
        print(f"Run: chmod +x {CARPLAY_PATH}")

    except Exception as error:
        print(f"[CarPlay] Failed to launch: {error}")

# =========================
# RESPONSIVE HOME LAYOUT
# =========================


def handle_mouse_click(mouse_position):
    global current_screen

    if current_screen != "home":
        return

    for screen_name, rect in click_targets.items():
        if rect is None:
            continue

        if not rect.collidepoint(mouse_position):
            continue

        if screen_name == "carplay":
            launch_carplay()
        else:
            current_screen = screen_name
            print(f"Opening screen: {screen_name}")

        return


def draw_placeholder_screen(width, height, title):
    draw_background(width, height)

    top_h = max(68, min(82, int(height * 0.12)))
    draw_top_bar(width, top_h)

    content_rect = pygame.Rect(
        40,
        top_h + 30,
        width - 80,
        height - top_h - 70,
    )

    draw_panel(
        content_rect,
        radius=28,
        fill=WHITE,
        border=BORDER,
        shadow=True,
    )

    title_rect = pygame.Rect(
        content_rect.x,
        content_rect.y + 60,
        content_rect.width,
        60,
    )

    draw_centered_text(
        title,
        title_rect,
        fonts["card_title"],
        TEXT,
    )

    message_rect = pygame.Rect(
        content_rect.x,
        content_rect.y + 130,
        content_rect.width,
        50,
    )

    draw_centered_text(
        "This screen is under construction.",
        message_rect,
        fonts["body"],
        MUTED,
    )

    back_rect = pygame.Rect(
        content_rect.x + 30,
        content_rect.y + 30,
        110,
        48,
    )

    pygame.draw.rect(screen, CARD_BLUE, back_rect, border_radius=16)
    pygame.draw.rect(
        screen,
        BORDER,
        back_rect,
        width=1,
        border_radius=16,
    )

    draw_centered_text(
        "← Home",
        back_rect,
        fonts["body_bold"],
        BLUE,
    )

    return back_rect


def draw_home_screen(width, height, mouse_pos, pet_data):

    # Clear positions from the previous frame.
    # The responsive layout will replace the visible ones below.
    for screen_name in click_targets:
        click_targets[screen_name] = None
    speed, rpm, coolant, dtc = safe_data()

    top_h = max(70, min(86, int(height * 0.12)))
    bottom_h = max(64, min(82, int(height * 0.115)))

    # Max content width keeps the layout from stretching too wide on laptops.
    max_content_w = 1280
    content_w = min(width - 40, max_content_w)
    margin_x = (width - content_w) // 2

    gap = max(14, int(content_w * 0.014))

    content_top = top_h + 24
    nav_rect = pygame.Rect(8, height - bottom_h - 8, width - 16, bottom_h)

    content_bottom = nav_rect.y - 14
    content_h = content_bottom - content_top

    message_h = 54
    main_h = content_h - message_h - gap

    if width >= 900:
        # Better proportions. Buddy no longer takes too much space.
        left_w = int(content_w * 0.31)
        right_w = int(content_w * 0.20)
        center_w = content_w - left_w - right_w - gap * 2

        left_x = margin_x
        center_x = left_x + left_w + gap
        right_x = center_x + center_w + gap

        buddy_rect = pygame.Rect(left_x, content_top, left_w, main_h)
        draw_buddy_panel(buddy_rect, pet_data)

        # App grid
        card_w = (center_w - gap * 2) // 3
        card_h = (main_h - gap) // 2

        app_cards = [
            ("CarPlay", "carplay", "carplay"),
            ("Trips", "trips", "trips"),
            ("Telemetry", "telemetry", "telemetry"),
            ("Settings", "settings", "settings"),
            ("Apps", "apps", "apps"),
            ("Media", None, "media"),
        ]

        for index, (label, icon, screen_name) in enumerate(app_cards):
            row = index // 3
            col = index % 3

            rect = pygame.Rect(
                center_x + col * (card_w + gap),
                content_top + row * (card_h + gap),
                card_w,
                card_h,
            )

            click_targets[screen_name] = rect

            if icon is None:
                draw_media_card(rect, mouse_pos)
            else:
                draw_app_card(rect, label, icon, mouse_pos)
        # Right status column
        speed_h = int(main_h * 0.30)
        obd_h = int(main_h * 0.36)
        weather_h = main_h - speed_h - obd_h - gap * 2

        speed_rect = pygame.Rect(right_x, content_top, right_w, speed_h)
        obd_rect = pygame.Rect(
            right_x, speed_rect.bottom + gap, right_w, obd_h)
        weather_rect = pygame.Rect(
            right_x, obd_rect.bottom + gap, right_w, weather_h)

        draw_speed_card(speed_rect, speed)
        draw_obd_card(obd_rect)

        if weather_rect.height >= 74:
            draw_weather_card(weather_rect)

        msg_rect = pygame.Rect(
            left_x,
            content_top + main_h + gap,
            left_w + gap + center_w,
            message_h,
        )
        draw_message_bar(msg_rect)

    elif width >= 760:
        left_w = int(content_w * 0.36)
        right_w = content_w - left_w - gap

        left_x = margin_x
        grid_x = left_x + left_w + gap

        buddy_rect = pygame.Rect(left_x, content_top, left_w, main_h)
        draw_buddy_panel(buddy_rect, pet_data)

        card_w = (right_w - gap) // 2
        card_h = (main_h - gap * 2) // 3

        app_cards = [
            ("CarPlay", "carplay", "carplay"),
            ("Trips", "trips", "trips"),
            ("Telemetry", "telemetry", "telemetry"),
            ("Settings", "settings", "settings"),
            ("Apps", "apps", "apps"),
            ("Media", None, "media"),
        ]

        for index, (label, icon, screen_name) in enumerate(app_cards):
            row = index // 2
            col = index % 2

            rect = pygame.Rect(
                grid_x + col * (card_w + gap),
                content_top + row * (card_h + gap),
                card_w,
                card_h,
            )

            # Save this card's current position for click detection.
            click_targets[screen_name] = rect

            if icon is None:
                draw_media_card(rect, mouse_pos)
            else:
                draw_app_card(rect, label, icon, mouse_pos)

        msg_rect = pygame.Rect(
            left_x,
            content_top + main_h + gap,
            content_w,
            message_h,
        )
        draw_message_bar(msg_rect)

    else:
        buddy_h = 170
        card_h = 110

        buddy_rect = pygame.Rect(margin_x, content_top, content_w, buddy_h)
        draw_buddy_panel(buddy_rect, pet_data)

        y = buddy_rect.bottom + gap
        card_w = (content_w - gap) // 2

        cards = [
            ("CarPlay", "carplay", "carplay"),
            ("Trips", "trips", "trips"),
            ("Telemetry", "telemetry", "telemetry"),
            ("Settings", "settings", "settings"),
        ]

        for index, (label, icon, screen_name) in enumerate(cards):
            row = index // 2
            col = index % 2

            rect = pygame.Rect(
                margin_x + col * (card_w + gap),
                y + row * (card_h + gap),
                card_w,
                card_h,
            )

            if rect.bottom < nav_rect.y - message_h - 10:
                click_targets[screen_name] = rect
                draw_app_card(rect, label, icon, mouse_pos)
            else:
                click_targets[screen_name] = None

        msg_rect = pygame.Rect(
            margin_x,
            nav_rect.y - message_h - 10,
            content_w,
            message_h,
        )
        draw_message_bar(msg_rect)

    draw_bottom_nav(nav_rect)


def draw_media_card(rect, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)

    draw_panel(
        rect,
        radius=22,
        fill=(244, 251, 255) if hovered else WHITE,
        border=BLUE if hovered else BORDER,
        shadow=True,
    )

    circle_radius = min(rect.width, rect.height) // 3
    circle_radius = max(46, min(circle_radius, 72))

    circle_center = (
        rect.centerx,
        rect.y + int(rect.height * 0.36),
    )

    draw_soft_circle(circle_center, circle_radius, (229, 246, 255), 235)

    cx, cy = circle_center
    color = BLUE

    scale = circle_radius / 58
    stem_h = int(42 * scale)
    gap = int(24 * scale)
    note_r = int(10 * scale)

    pygame.draw.line(screen, color, (cx - gap // 2, cy - stem_h // 2),
                     (cx - gap // 2, cy + stem_h // 2), max(4, int(5 * scale)))
    pygame.draw.line(screen, color, (cx + gap // 2, cy - stem_h // 3),
                     (cx + gap // 2, cy + stem_h // 2), max(4, int(5 * scale)))
    pygame.draw.line(screen, color, (cx - gap // 2, cy - stem_h // 2),
                     (cx + gap // 2, cy - stem_h // 3), max(4, int(5 * scale)))

    pygame.draw.circle(screen, color, (cx - gap // 2 -
                       8, cy + stem_h // 2), note_r)
    pygame.draw.circle(screen, color, (cx + gap // 2 -
                       8, cy + stem_h // 2 + 4), note_r)

    label_font = fonts["heading"] if rect.height >= 145 else fonts["body_bold"]

    label_rect = pygame.Rect(
        rect.x + 8,
        rect.bottom - 52,
        rect.width - 16,
        36,
    )

    draw_centered_text("Media", label_rect, label_font, TEXT)

# =========================
# MAIN PROGRAM
# =========================


def main():
    """
    Runs DashBuddy OS.

    The main loop:
    1. Reads keyboard, mouse, resize, and quit events.
    2. Updates the current screen.
    3. Draws the selected screen.
    4. Refreshes the display.
    """
    global screen
    global telemetry
    global current_screen

    running = True
    screen_buttons = {}
    recent_trips = get_recent_trips(limit=3)
    # Preload images once at startup.
    for key in ASSET_PATHS:
        load_image(key)

    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # =========================
        # EVENT HANDLING
        # =========================

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Escape returns home first.
                    # Pressing Escape on Home closes the program.
                    if current_screen == "home":
                        running = False
                    else:
                        current_screen = "home"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    if current_screen == "home":
                        handle_mouse_click(event.pos)

                    elif current_screen == "trips":
                        back_button = screen_buttons.get("back")
                        start_button = screen_buttons.get("start")
                        pause_button = screen_buttons.get("pause")
                        end_button = screen_buttons.get("end")

                        if (
                            back_button is not None
                            and back_button.collidepoint(event.pos)
                        ):
                            current_screen = "home"

                        elif (
                            start_button is not None
                            and start_button.collidepoint(event.pos)
                        ):
                            trip_manager.start_trip()
                            print("[Trip] Started")

                        elif (
                            pause_button is not None
                            and pause_button.collidepoint(event.pos)
                        ):
                            trip_manager.toggle_pause()

                            if trip_manager.trip_paused:
                                print("[Trip] Paused")
                            else:
                                print("[Trip] Resumed")

                        elif (
                            end_button is not None
                            and end_button.collidepoint(event.pos)
                        ):
                            finished_trip = trip_manager.end_trip()

                            if finished_trip is not None:
                                saved = save_trip(finished_trip)

                                if saved:
                                    recent_trips = get_recent_trips(limit=3)
                                    print("[Trip] Ended and saved")
                                else:
                                    print("[Trip] Ended but could not be saved")

                    else:
                        back_button = screen_buttons.get("back")

                        if (
                            back_button is not None
                            and back_button.collidepoint(event.pos)
                        ):
                            current_screen = "home"
            elif event.type == pygame.VIDEORESIZE:
                new_width = max(MIN_WIDTH, event.w)
                new_height = max(MIN_HEIGHT, event.h)

                screen = pygame.display.set_mode(
                    (new_width, new_height),
                    pygame.RESIZABLE,
                )

        # =========================
        # SCREEN DRAWING
        # =========================

        width, height = screen.get_size()
        screen_buttons = {}

        speed, rpm, coolant, dtc = safe_data()
        instant_mpg = safe_mpg()

        trip_manager.update(
            speed_mph=speed,
            rpm=rpm,
        )

        trip_data = trip_manager.get_data()
        trip_data["recent_trips"] = recent_trips
        pet_manager.update(
            speed=speed,
            rpm=rpm,
            hard_brakes=trip_data["hard_brakes"],
            fast_accelerations=trip_data["fast_accelerations"],
            trip_active=trip_data["trip_active"],
        )

        pet_data = pet_manager.get_data()

        if current_screen == "home":
            draw_background(width, height)

            draw_top_bar(
                width,
                max(68, min(82, int(height * 0.12))),
            )

            draw_home_screen(
                width,
                height,
                mouse_pos,
                pet_data
            )

        elif current_screen == "trips":
            screen_buttons = draw_trips_screen(
                surface=screen,
                width=width,
                height=height,
                fonts=fonts,
                trip_data=trip_data,
                mouse_pos=mouse_pos,
            )

        elif current_screen == "telemetry":
            screen_buttons = draw_telemetry_screen(
                surface=screen,
                width=width,
                height=height,
                fonts=fonts,
                mouse_pos=mouse_pos,
                speed=speed,
                rpm=rpm,
                coolant=coolant,
                dtc=dtc,
                connected=telemetry_connected,
                speed_history=trip_data.get("speed_history", []),
                instant_mpg=instant_mpg,
            )

        elif current_screen == "settings":
            screen_buttons["back"] = draw_placeholder_screen(
                width,
                height,
                "Settings",
            )

        elif current_screen == "apps":
            screen_buttons["back"] = draw_placeholder_screen(
                width,
                height,
                "Apps",
            )

        elif current_screen == "media":
            screen_buttons["back"] = draw_placeholder_screen(
                width,
                height,
                "Media",
            )

        elif current_screen == "carplay":
            screen_buttons["back"] = draw_placeholder_screen(
                width,
                height,
                "Apple CarPlay",
            )

        else:
            # Safety fallback in case current_screen contains
            # an invalid name.
            current_screen = "home"

        # This must remain inside the while loop.
        pygame.display.flip()

    # =========================
    # CLEAN SHUTDOWN
    # =========================

    try:
        if telemetry:
            telemetry.stop()
    except Exception as error:
        print(f"[Telemetry shutdown error] {error}")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
