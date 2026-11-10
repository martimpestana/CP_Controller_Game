"""Draws the game icon at 512 px. To rebuild icon.png and icon.ico after changing it:

    uv run --with pillow python railgame/assets/make_icon.py

(icon.ico holds the sizes Windows uses for shortcuts, from 16 to 256 px.)
"""
import os, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()
N = 512
s = pygame.Surface((N, N), pygame.SRCALPHA)
# Background: rounded square, night sky to sea.
bg = pygame.Surface((N, N), pygame.SRCALPHA)
for y in range(N):
    f = y / N
    c = (int(18 + 20 * f), int(30 + 30 * f), int(54 + 40 * f))
    pygame.draw.line(bg, c, (0, y), (N, y))
# Sea in the lower part with a sandy coast line.
pygame.draw.polygon(bg, (14, 60, 96), [(0, 360), (N, 300), (N, N), (0, N)])
pygame.draw.line(bg, (200, 176, 110), (0, 372), (N, 312), 8)
# Rails converging to the horizon.
hx, hy = 256, 250
for x0 in (120, 392):
    pygame.draw.line(bg, (200, 206, 214), (x0, N), (hx + (x0 - 256) * 0.12, hy), 10)
for i in range(7):
    t = (i / 7) ** 1.8
    y = hy + (N - hy) * t
    w = 40 + 260 * t
    pygame.draw.line(bg, (90, 80, 70), (256 - w * 0.62, y), (256 + w * 0.62, y), max(3, int(10 * t)))
mask = pygame.Surface((N, N), pygame.SRCALPHA)
pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, N, N), border_radius=96)
bg.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
s.blit(bg, (0, 0))
# Train front, seen head-on.
ink = (10, 12, 18)
body = pygame.Rect(146, 120, 220, 250)
pygame.draw.rect(s, ink, body.inflate(16, 16), border_radius=56)
pygame.draw.rect(s, (238, 240, 244), body, border_radius=50)
pygame.draw.rect(s, (200, 40, 45), (body.x, body.y + 168, body.w, 30))          # red band
pygame.draw.rect(s, (60, 66, 78), (body.x, body.y + 205, body.w, 45), border_bottom_left_radius=50, border_bottom_right_radius=50)
pygame.draw.rect(s, (30, 44, 66), (body.x + 22, body.y + 26, body.w - 44, 110), border_radius=22)  # windscreen
pygame.draw.polygon(s, (90, 130, 175), [(body.x + 40, body.y + 30), (body.x + 82, body.y + 30), (body.x + 52, body.y + 132), (body.x + 26, body.y + 132)])
for x in (body.x + 40, body.right - 40):                                         # headlights
    pygame.draw.circle(s, ink, (x, body.y + 183), 19)
    pygame.draw.circle(s, (255, 236, 150), (x, body.y + 183), 14)
pygame.draw.rect(s, ink, (body.centerx - 46, body.y + 6, 92, 16), border_radius=6)  # destination board
pygame.draw.rect(s, (255, 170, 40), (body.centerx - 40, body.y + 9, 80, 10), border_radius=4)
# Signal on the right: green light.
pygame.draw.rect(s, ink, (404, 150, 16, 210))
pygame.draw.rect(s, ink, (384, 96, 56, 100), border_radius=20)
pygame.draw.circle(s, (70, 20, 20), (412, 122), 16)
pygame.draw.circle(s, (60, 230, 120), (412, 170), 17)
glow = pygame.Surface((N, N), pygame.SRCALPHA)
pygame.draw.circle(glow, (60, 230, 120, 70), (412, 170), 34)
s.blit(glow, (0, 0))
here = os.path.dirname(os.path.abspath(__file__))
big = os.path.join(here, "icon512.png")
pygame.image.save(s, big)
from PIL import Image  # noqa: E402

im = Image.open(big)
im.resize((256, 256), Image.LANCZOS).save(os.path.join(here, "icon.png"))
im.save(os.path.join(here, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
os.remove(big)
