import pygame
pygame.init()
try:
    print("Desktop sizes:", pygame.display.get_desktop_sizes())
except AttributeError:
    print("pygame.display.get_desktop_sizes() not found")
print("Display Info:", pygame.display.Info())
pygame.quit()
