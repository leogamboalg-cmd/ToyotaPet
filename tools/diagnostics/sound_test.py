from pathlib import Path

import pygame


ROOT_DIR = Path(__file__).resolve().parents[2]
SOUND_FILE = ROOT_DIR / "assets" / "sounds" / "high_speed.mp3"

pygame.mixer.init()

sound = pygame.mixer.Sound(str(SOUND_FILE))

sound.play()

input("Press Enter to exit...")
