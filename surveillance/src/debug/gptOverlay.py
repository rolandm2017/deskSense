import pygame
import os
import subprocess
import time

# Ensure pygame runs in a transparent window
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
pygame.init()

# Get screen dimensions
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h

# Transparent overlay window
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.NOFRAME | pygame.SRCALPHA)
pygame.display.set_caption("Overlay")

# Set overlay as always-on-top
subprocess.Popen(["xprop", "-name", "Overlay", "-f", "_NET_WM_WINDOW_TYPE",
                 "8a", "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_NOTIFICATION"])

# Load font
font = pygame.font.SysFont(None, 100)  # Large font


def get_active_window():
    """Fetch the active window title"""
    try:
        output = subprocess.check_output(
            "xdotool getactivewindow getwindowname", shell=True).decode().strip()
        return output if output else "Unknown"
    except Exception:
        return "Unknown"


running = True
clock = pygame.time.Clock()

while running:
    screen.fill((0, 0, 0, 0))  # Fully transparent

    # Get active window name
    active_window = get_active_window()

    # Render text
    overlay_text = font.render(active_window, True, (0, 255, 0))  # Green text
    screen.blit(overlay_text, (50, 50))  # Position top-left

    pygame.display.update()
    clock.tick(1)  # Refresh every second

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
