
import math
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402
from pygame import gfxdraw  # noqa: E402

HEAD = (120, 205, 255)
TAIL = (40, 80, 195)
OUTLINE = (14, 28, 70)
SPOT = (28, 58, 150)
EYE = (250, 250, 245)
PUPIL = (12, 16, 26)
TONGUE = (240, 70, 105)
STEM = (105, 68, 38)
APPLES = {
    "green": ((150, 225, 70), (78, 155, 30), (38, 120, 55)),
    "red": ((235, 52, 62), (150, 20, 34), (72, 178, 78)),
}
FONT_NAMES = "segoeui,helveticaneue,helvetica,ubuntu,dejavusans,arial"
_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        pygame.font.init()
        _fonts[key] = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
    return _fonts[key]


def mix(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def disc(surf, color, center, radius):
    r = int(round(radius))
    if r < 1:
        return
    x, y = int(round(center[0])), int(round(center[1]))
    gfxdraw.filled_circle(surf, x, y, r, color)
    gfxdraw.aacircle(surf, x, y, r, color)


def polygon(surf, color, points):
    points = [(int(round(x)), int(round(y))) for x, y in points]
    gfxdraw.filled_polygon(surf, points, color)
    gfxdraw.aapolygon(surf, points, color)


def shadow(surf, center, width, height, alpha=70):
    w, h = max(2, int(width)), max(2, int(height))
    blob = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(blob, (0, 0, 0, alpha), blob.get_rect())
    surf.blit(blob, (center[0] - w / 2, center[1] - h / 2))


def leaf_points(base, tip, width):
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy) or 1
    px, py = -dy / length, dx / length
    left, right = [], []
    for i in range(9):
        t = i / 8
        w = math.sin(math.pi * t) * width
        x, y = base[0] + dx * t, base[1] + dy * t
        left.append((x + px * w, y + py * w))
        right.append((x - px * w, y - py * w))
    return left + right[::-1]


def draw_apple(surf, center, size, kind="red"):
    body, dark, leaf = APPLES[kind]
    cx, cy = center[0], center[1] + size * 0.06
    r = size * 0.32
    shadow(surf, (cx, cy + r * 0.95), r * 2.1, r * 0.55)
    for color, shift, scale in ((dark, 0, 1.0), (body, -r * 0.08, 0.9)):
        x, y = cx + shift, cy + shift
        disc(surf, color, (x - r * 0.3, y - r * 0.1), r * 0.78 * scale)
        disc(surf, color, (x + r * 0.3, y - r * 0.1), r * 0.78 * scale)
        disc(surf, color, (x, y + r * 0.12), r * 0.82 * scale)
    disc(surf, (255, 255, 255, 120), (cx - r * 0.55, cy - r * 0.25),
         r * 0.2)
    disc(surf, (255, 255, 255, 80), (cx - r * 0.72, cy + r * 0.08),
         r * 0.1)
    stem_top = (cx + r * 0.16, cy - r * 1.15)
    pygame.draw.line(surf, STEM, (cx, cy - r * 0.5), stem_top,
                     max(2, int(size / 14)))
    base = (cx + r * 0.1, cy - r * 0.92)
    tip = (base[0] + r * 0.8, base[1] - r * 0.38)
    polygon(surf, leaf, leaf_points(base, tip, r * 0.22))
    pygame.draw.aaline(surf, mix(leaf, (0, 0, 0), 0.35), base, tip)


def draw_snake(surf, points, size, direction=(0, -1), tongue=True,
               dead=False):
    if not points:
        return
    last = max(len(points) - 1, 1)

    def radius(i):
        return size * (0.4 - 0.13 * i / last)

    def color(i):
        return mix(HEAD, TAIL, i / last)

    samples = []
    for i in range(len(points) - 1, 0, -1):
        a, b = points[i], points[i - 1]
        steps = max(1, int(math.dist(a, b) / (size * 0.12)))
        for k in range(steps):
            t = k / steps
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            samples.append((p, i - t))
    for p, i in samples:
        disc(surf, OUTLINE, p, radius(i) + max(1.5, size * 0.04))
    for p, i in samples:
        disc(surf, color(i), p, radius(i))
    for i in range(2, len(points), 2):
        disc(surf, mix(color(i), SPOT, 0.6), points[i], radius(i) * 0.42)
    for p, i in samples:
        off = radius(i) * 0.25
        disc(surf, mix(color(i), (255, 255, 255), 0.22),
             (p[0] - off, p[1] - off), radius(i) * 0.45)
    draw_head(surf, points[0], size, direction, tongue, dead)


def draw_head(surf, center, size, direction, tongue, dead):
    hx, hy = center
    norm = math.hypot(*direction) or 1
    dx, dy = direction[0] / norm, direction[1] / norm
    px, py = -dy, dx
    r = size * 0.44
    if tongue and not dead:
        width = max(2, int(size / 18))
        start = (hx + dx * r, hy + dy * r)
        fork = (start[0] + dx * size * 0.26, start[1] + dy * size * 0.26)
        pygame.draw.line(surf, TONGUE, start, fork, width)
        for side in (1, -1):
            end = (fork[0] + (dx + px * side) * size * 0.09,
                   fork[1] + (dy + py * side) * size * 0.09)
            pygame.draw.line(surf, TONGUE, fork, end, width)
    snout = (hx + dx * r * 0.3, hy + dy * r * 0.3)
    edge = max(1.5, size * 0.04)
    disc(surf, OUTLINE, center, r + edge)
    disc(surf, OUTLINE, snout, r * 0.85 + edge)
    disc(surf, HEAD, center, r)
    disc(surf, HEAD, snout, r * 0.85)
    disc(surf, mix(HEAD, (255, 255, 255), 0.35),
         (hx - r * 0.3, hy - r * 0.3), r * 0.28)
    for side in (1, -1):
        ex = hx + dx * r * 0.28 + px * r * 0.48 * side
        ey = hy + dy * r * 0.28 + py * r * 0.48 * side
        if dead:
            s = r * 0.2
            width = max(2, int(size / 16))
            pygame.draw.line(surf, PUPIL, (ex - s, ey - s), (ex + s, ey + s),
                             width)
            pygame.draw.line(surf, PUPIL, (ex - s, ey + s), (ex + s, ey - s),
                             width)
            continue
        disc(surf, OUTLINE, (ex, ey), r * 0.29)
        disc(surf, EYE, (ex, ey), r * 0.25)
        pupil = (ex + dx * r * 0.09, ey + dy * r * 0.09)
        disc(surf, PUPIL, pupil, r * 0.14)
        disc(surf, EYE, (pupil[0] - r * 0.05, pupil[1] - r * 0.05),
             r * 0.05)
