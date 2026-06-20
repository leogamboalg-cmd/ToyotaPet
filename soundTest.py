import pygame

pygame.mixer.init()

sound = pygame.mixer.Sound("assets/sounds/fastSpeed.mp3")

sound.play()

input("Press Enter to exit...")
