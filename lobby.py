
import glob
import math
import os
from types import SimpleNamespace

from agent import Agent
from art import draw_apple, draw_snake, font, mix, polygon
from environment import Environment
from gui import Display
from interpreter import Interpreter
from main import run_session
import pygame

SIZE = (820, 600)
TOP, BOTTOM = (13, 17, 28), (8, 34, 31)
TEXT = (236, 240, 246)
MUTED = (132, 144, 160)
DIM = (70, 80, 96)
ACCENT = (90, 200, 255)
GREEN = (120, 225, 100)
KEYCAP = (36, 44, 58)


def options():
    models = sorted(glob.glob("models/*.txt"), key=lambda p: (len(p), p))
    return [
        ("Model", [None] + models),
        ("Sessions", [1, 5, 10, 50, 100, 500]),
        ("Board size", [5, 8, 10, 15, 20]),
        ("Speed (s per move)", [0.5, 0.15, 0.04, 0.0]),
        ("Learning", [True, False]),
    ]


def show(value):
    if value is None:
        return "new model"
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, str):
        return os.path.basename(value)
    return str(value)

def make_background():
    w, h = SIZE
    surf = pygame.Surface(SIZE)
    for y in range(h):
        pygame.draw.line(surf, mix(TOP, BOTTOM, y / h), (0, y), (w, y))
    tile = pygame.Surface((40, 40), pygame.SRCALPHA)
    tile.fill((255, 255, 255, 6))
    for y in range(0, h, 40):
        for x in range(0, w, 40):
            if (x + y) // 40 % 2 == 0:
                surf.blit(tile, (x, y))
    return surf


def panel(screen, rect, radius=18, alpha=16):
    card = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(card, (255, 255, 255, alpha), card.get_rect(),
                     border_radius=radius)
    pygame.draw.rect(card, (255, 255, 255, 34), card.get_rect(), 1,
                     border_radius=radius)
    screen.blit(card, rect.topleft)


def blit_center(screen, label, center):
    screen.blit(label, label.get_rect(center=center))


_titles = {}


def make_title(left, right):
    big = font(66, True)
    a = big.render(left, True, TEXT)
    b = big.render(right, True, ACCENT)
    w, h = a.get_width() + b.get_width(), a.get_height()
    pad = 30
    glow = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    glow.blit(big.render(left + right, True, ACCENT), (pad, pad))
    size = glow.get_size()
    glow = pygame.transform.smoothscale(glow, (size[0] // 6, size[1] // 6))
    glow = pygame.transform.smoothscale(glow, size)
    glow.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
    glow.blit(a, (pad, pad))
    glow.blit(b, (pad + a.get_width(), pad))
    return glow


def title(screen, left, right, y):
    key = (left, right)
    if key not in _titles:
        _titles[key] = make_title(left, right)
    blit_center(screen, _titles[key], (SIZE[0] // 2, y))


def arrow(screen, color, center, way, size=8):
    cx, cy = center
    polygon(screen, color, [(cx + way * size, cy),
                            (cx - way * size * 0.6, cy - size),
                            (cx - way * size * 0.6, cy + size)])


def keycaps(screen, items, y):
    parts = []
    for key, action in items:
        k = font(15, True).render(key, True, TEXT)
        a = font(15).render(action, True, MUTED)
        parts.append((k, a, k.get_width() + 20 + 8 + a.get_width()))
    gap = 28
    x = (SIZE[0] - sum(p[2] for p in parts) - gap * (len(parts) - 1)) / 2
    for k, a, width in parts:
        cap = pygame.Rect(int(x), y, k.get_width() + 20, 28)
        pygame.draw.rect(screen, mix(KEYCAP, (0, 0, 0), 0.5),
                         cap.move(0, 3), border_radius=7)
        pygame.draw.rect(screen, KEYCAP, cap, border_radius=7)
        pygame.draw.rect(screen, DIM, cap, 1, border_radius=7)
        blit_center(screen, k, cap.center)
        screen.blit(a, (cap.right + 8, cap.centery - a.get_height() // 2))
        x += width + gap


def slither(screen, t, y):
    count, gap, wave, length = 22, 14, 12, 45
    span = SIZE[0] + count * gap + 160
    head = (t * 110) % span - 60
    points = []
    for i in range(count):
        x = head - i * gap
        points.append((x, y + wave * math.sin(x / length)))
    slope = wave / length * math.cos(head / length)
    draw_snake(screen, points, 30, (1, slope), tongue=int(t * 3) % 3 != 0)


def decorations(screen, t):
    draw_apple(screen, (92, 78 + 5 * math.sin(t * 2)), 70, "red")
    draw_apple(screen, (728, 78 + 5 * math.sin(t * 2 + 1.6)), 70, "green")
    slither(screen, t, SIZE[1] - 42)


def draw_menu(screen, background, rows, pos, current, t):
    screen.blit(background, (0, 0))
    decorations(screen, t)
    title(screen, "LEARN2", "SLITHER", 78)
    blit_center(screen, font(18).render(
        "A snake that learns to survive with Q-learning", True, MUTED),
        (SIZE[0] // 2, 128))
    row_h = 56
    box = pygame.Rect(150, 162, 520, row_h * len(rows) + 24)
    panel(screen, box)
    for i, (name, values) in enumerate(rows):
        top = box.y + 12 + i * row_h
        middle = top + row_h // 2
        on = i == current
        if on:
            glow = pygame.Surface((box.w - 24, row_h - 6), pygame.SRCALPHA)
            alpha = int(34 + 14 * math.sin(t * 4))
            pygame.draw.rect(glow, (*ACCENT, alpha), glow.get_rect(),
                             border_radius=12)
            pygame.draw.rect(glow, (*ACCENT, 150), glow.get_rect(), 1,
                             border_radius=12)
            screen.blit(glow, (box.x + 12, top + 3))
        label = font(21, on).render(name, True, TEXT if on else MUTED)
        screen.blit(label, (box.x + 34, middle - label.get_height() // 2))
        cx = box.right - 140
        value = font(21, True).render(show(values[pos[i]]), True,
                                      ACCENT if on else TEXT)
        blit_center(screen, value, (cx, middle - 5))
        color = ACCENT if on else DIM
        shift = 3 * math.sin(t * 6) if on else 0
        arrow(screen, color, (cx - 100 - shift, middle - 5), -1)
        arrow(screen, color, (cx + 100 + shift, middle - 5), 1)
        dots = len(values)
        for d in range(dots):
            dx = cx + (d - (dots - 1) / 2) * 10
            dot = color if d == pos[i] else mix(DIM, TOP, 0.4)
            pygame.draw.circle(screen, dot, (int(dx), middle + 16), 2)
    keycaps(screen, [("Up / Down", "select"), ("Left / Right", "change"),
                     ("Enter", "play"), ("Esc", "quit")], box.bottom + 24)


def menu(screen, background, rows, pos):
    current = 0
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                return None
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return [r[1][p] for r, p in zip(rows, pos)]
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = 1 if event.key == pygame.K_DOWN else -1
                current = (current + step) % len(rows)
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = 1 if event.key == pygame.K_RIGHT else -1
                pos[current] = (pos[current] + step) % len(rows[current][1])
        draw_menu(screen, background, rows, pos, current,
                  pygame.time.get_ticks() / 1000)
        pygame.display.flip()
        clock.tick(60)



def play(values):
    model, sessions, size, speed, learning = values
    env = Environment(size=size)
    agent = Agent(learning=learning)
    if model:
        try:
            agent.load(model)
        except (OSError, ValueError, KeyError) as err:
            print(f"Cannot load model '{model}': {err}")
            return [], []
        agent.learning = learning
        print(f"Load trained model from {model}")
    args = SimpleNamespace(visual="on", step_by_step=False, maxsteps=2000)
    viewer = Display(env, speed, False)
    interp = Interpreter()
    lengths, durations = [], []
    for _ in range(sessions):
        if not run_session(env, interp, agent, viewer, args):
            break
        agent.end_session()
        lengths.append(env.max_length)
        durations.append(env.steps)
    print(f"Game over, max length = {max(lengths, default=0)}, "
          f"max duration = {max(durations, default=0)}")
    return lengths, durations



def draw_chart(screen, rect, lengths):
    panel(screen, rect)
    screen.blit(font(15, True).render("LENGTH PER GAME", True, MUTED),
                (rect.x + 20, rect.y + 14))
    area = pygame.Rect(rect.x + 48, rect.y + 44, rect.w - 70, rect.h - 70)
    top = max(12, math.ceil(max(lengths) / 4) * 4)
    for k in range(5):
        y = area.bottom - area.h * k / 4
        pygame.draw.line(screen, mix(TOP, DIM, 0.5), (area.x, y),
                         (area.right, y))
        tick = font(13).render(f"{top * k / 4:.0f}", True, MUTED)
        screen.blit(tick, (area.x - 10 - tick.get_width(),
                           y - tick.get_height() // 2))
    goal = area.bottom - area.h * 10 / top
    for x in range(area.x, area.right, 14):
        pygame.draw.line(screen, GREEN, (x, goal),
                         (min(x + 7, area.right), goal), 2)
    screen.blit(font(13, True).render("- - goal 10", True, GREEN),
                (rect.right - 84, rect.y + 16))
    count = len(lengths)
    points = [(area.x + area.w * i / max(count - 1, 1),
               area.bottom - area.h * v / top)
              for i, v in enumerate(lengths)]
    if count > 1:
        fill = pygame.Surface(SIZE, pygame.SRCALPHA)
        pygame.draw.polygon(fill, (*ACCENT, 45), points + [
            (area.right, area.bottom), (area.x, area.bottom)])
        screen.blit(fill, (0, 0))
        pygame.draw.lines(screen, ACCENT, False, points, 3)
    pygame.draw.circle(screen, TEXT, points[-1], 5)
    pygame.draw.circle(screen, ACCENT, points[-1], 3)


def draw_results(screen, background, cards, extra, lengths, t):
    screen.blit(background, (0, 0))
    decorations(screen, t)
    title(screen, "YOUR ", "RESULTS", 70)
    width, gap = 170, 16
    x = (SIZE[0] - 4 * width - 3 * gap) // 2
    for name, value, color in cards:
        rect = pygame.Rect(x, 120, width, 92)
        panel(screen, rect, 16)
        blit_center(screen, font(13, True).render(name, True, MUTED),
                    (rect.centerx, rect.y + 24))
        blit_center(screen, font(34, True).render(value, True, color),
                    (rect.centerx, rect.y + 58))
        x += width + gap
    draw_chart(screen, pygame.Rect(46, 228, SIZE[0] - 92, 236), lengths)
    blit_center(screen, font(16).render(extra, True, MUTED),
                (SIZE[0] // 2, 482))
    keycaps(screen, [("Enter", "back to lobby"), ("Esc", "quit")], 504)


def results(screen, background, lengths, durations):
    count = len(lengths)
    reach = 100 * sum(1 for v in lengths if v >= 10) / count
    cards = [
        ("GAMES", str(count), TEXT),
        ("AVERAGE LENGTH", f"{sum(lengths) / count:.1f}", TEXT),
        ("BEST LENGTH", str(max(lengths)), ACCENT),
        ("REACHED 10+", f"{reach:.0f}%", GREEN),
    ]
    extra = (f"Average duration {sum(durations) / count:.0f} moves    "
             f"Longest game {max(durations)} moves")
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                return event.key != pygame.K_ESCAPE
        draw_results(screen, background, cards, extra, lengths,
                     pygame.time.get_ticks() / 1000)
        pygame.display.flip()
        clock.tick(60)


def run_lobby(args=None):
    pygame.display.init()
    pygame.font.init()
    rows = options()
    pos = [0, 2, 2, 1, 0]
    if args is not None and args.size in rows[2][1]:
        pos[2] = rows[2][1].index(args.size)
    background = make_background()
    while True:
        pygame.display.set_caption("Learn2Slither")
        screen = pygame.display.set_mode(SIZE)
        values = menu(screen, background, rows, pos)
        if values is None:
            break
        lengths, durations = play(values)
        pygame.display.set_caption("Learn2Slither - Results")
        screen = pygame.display.set_mode(SIZE)
        if lengths and not results(screen, background, lengths, durations):
            break
        rows = options()
        pos[0] = min(pos[0], len(rows[0][1]) - 1)
    pygame.quit()
    return 0
