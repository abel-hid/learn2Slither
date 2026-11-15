"""Small lobby: choose the settings with the keyboard, play, see results.

Start it with:  ./snake -lobby
Keys: Up/Down select, Left/Right change, Enter start, Esc quit.
"""

import glob
from types import SimpleNamespace

from agent import Agent
from environment import Environment
from gui import Display
from interpreter import Interpreter
from main import run_session
import pygame

SIZE = (560, 400)
BG, FG, ACCENT = (20, 22, 30), (230, 232, 240), (72, 200, 150)


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
    return str(value)


def write(screen, font, msg, pos, color=FG):
    screen.blit(font.render(msg, True, color), pos)


def menu(screen, font, rows, pos):
    """Returns the chosen values, or None to quit."""
    row = 0
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                return None
            if event.key == pygame.K_RETURN:
                return [r[1][p] for r, p in zip(rows, pos)]
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = 1 if event.key == pygame.K_DOWN else -1
                row = (row + step) % len(rows)
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = 1 if event.key == pygame.K_RIGHT else -1
                pos[row] = (pos[row] + step) % len(rows[row][1])
        screen.fill(BG)
        write(screen, font, "Learn2Slither", (40, 30), ACCENT)
        for i, (name, values) in enumerate(rows):
            marker = "> " if i == row else "  "
            line = f"{marker}{name}: {show(values[pos[i]])}"
            write(screen, font, line, (40, 100 + i * 40),
                  ACCENT if i == row else FG)
        write(screen, font, "Up/Down select   Left/Right change",
              (40, 330))
        write(screen, font, "Enter start   Esc quit", (40, 360))
        pygame.display.flip()
        clock.tick(30)


def play(values):
    """Runs the sessions with the normal display. Returns the stats."""
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


def results(screen, font, lengths, durations):
    """Shows the statistics. Returns False to quit, True for the lobby."""
    count = len(lengths)
    reach = 100 * sum(1 for v in lengths if v >= 10) / count
    lines = [
        f"Games: {count}",
        f"Average length: {sum(lengths) / count:.1f}",
        f"Best length: {max(lengths)}    Reached 10+: {reach:.0f}%",
        f"Average duration: {sum(durations) / count:.0f}    "
        f"Longest: {max(durations)}",
    ]
    top = max(max(lengths), 10)
    base, height = 340, 140
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                return event.key != pygame.K_ESCAPE
        screen.fill(BG)
        write(screen, font, "Results", (40, 30), ACCENT)
        for i, line in enumerate(lines):
            write(screen, font, line, (40, 80 + i * 32))
        pygame.draw.rect(screen, FG, (30, base - height, 500, height), 1)
        goal = base - height * 10 / top
        pygame.draw.line(screen, ACCENT, (30, goal), (530, goal))
        if count > 1:
            points = [(30 + 500 * i / (count - 1), base - height * v / top)
                      for i, v in enumerate(lengths)]
            pygame.draw.lines(screen, FG, False, points, 2)
        write(screen, font, "Length per game (green line = 10)", (30, 352))
        write(screen, font, "Enter: lobby   Esc: quit", (30, 374))
        pygame.display.flip()


def run_lobby(args=None):
    pygame.display.init()
    pygame.font.init()
    font = pygame.font.Font(None, 30)
    rows = options()
    pos = [0, 2, 2, 1, 0]
    if args is not None and args.size in rows[2][1]:
        pos[2] = rows[2][1].index(args.size)
    while True:
        pygame.display.set_caption("Learn2Slither")
        screen = pygame.display.set_mode(SIZE)
        values = menu(screen, font, rows, pos)
        if values is None:
            break
        lengths, durations = play(values)
        screen = pygame.display.set_mode(SIZE)
        if lengths and not results(screen, font, lengths, durations):
            break
        rows = options()
        pos[0] = min(pos[0], len(rows[0][1]) - 1)
    pygame.quit()
    return 0