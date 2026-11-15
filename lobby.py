"""Simple lobby: ./snake -lobby

Pick the settings, play, see the statistics, come back to the lobby.
"""

import glob
from types import SimpleNamespace

import pygame

from agent import Agent
from environment import Environment
from gui import Display
from interpreter import Interpreter
from main import run_session

SIZE = (560, 420)
BG, FG, ACCENT = (20, 22, 30), (230, 232, 240), (72, 200, 150)


def settings():
    """Each row: [name, choices, selected index]."""
    models = sorted(glob.glob("models/*.txt"), key=lambda p: (len(p), p))
    return [
        ["Model", [None] + models, len(models)],
        ["Sessions", [1, 5, 10, 50, 100], 2],
        ["Board size", [5, 8, 10, 15, 20], 2],
        ["Speed (s/move)", [0.3, 0.1, 0.03, 0.0], 1],
        ["Learning", ["off", "on"], 0],
    ]


def text(screen, font, msg, pos, color=FG):
    screen.blit(font.render(msg, True, color), pos)


def wait_key():
    """Block until a key is pressed. Returns the key, or None on close."""
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            return None
        if event.type == pygame.KEYDOWN:
            return event.key


def menu(screen, font, rows):
    """Configuration panel. Returns the chosen values, or None to quit."""
    cur = 0
    while True:
        screen.fill(BG)
        text(screen, font, "LEARN2SLITHER", (40, 30), ACCENT)
        for i, (name, choices, sel) in enumerate(rows):
            value = choices[sel] if choices[sel] is not None else "new model"
            color = ACCENT if i == cur else FG
            text(screen, font, f"{name}:", (60, 100 + i * 45), color)
            text(screen, font, f"< {value} >", (260, 100 + i * 45), color)
        text(screen, font, "Arrows: choose   Enter: play   Esc: quit",
             (40, 370))
        pygame.display.flip()
        key = wait_key()
        if key in (None, pygame.K_ESCAPE):
            return None
        if key == pygame.K_RETURN:
            return [choices[sel] for _, choices, sel in rows]
        if key in (pygame.K_UP, pygame.K_DOWN):
            cur = (cur + (1 if key == pygame.K_DOWN else -1)) % len(rows)
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            step = 1 if key == pygame.K_RIGHT else -1
            rows[cur][2] = (rows[cur][2] + step) % len(rows[cur][1])


def play(model, sessions, size, speed, learning):
    """Run the games with the normal board display. Returns the stats."""
    agent = Agent(learning=(learning == "on"))
    if model:
        agent.load(model)
        agent.learning = learning == "on"
    env = Environment(size=size)
    viewer = Display(env, speed)
    args = SimpleNamespace(visual="on", step_by_step=False, maxsteps=1000)
    lengths, durations = [], []
    for _ in range(sessions):
        if not run_session(env, Interpreter(), agent, viewer, args):
            break
        agent.end_session()
        lengths.append(env.max_length)
        durations.append(env.steps)
    return lengths, durations


def results(screen, font, lengths, durations):
    """Statistics screen. Returns False to quit, True for the lobby."""
    n = len(lengths)
    lines = [
        f"Games played:     {n}",
        f"Best length:      {max(lengths)}",
        f"Average length:   {sum(lengths) / n:.1f}",
        f"Reached 10+:      {100 * sum(v >= 10 for v in lengths) // n}%",
        f"Longest game:     {max(durations)} moves",
    ]
    screen.fill(BG)
    text(screen, font, "RESULTS", (40, 30), ACCENT)
    for i, line in enumerate(lines):
        text(screen, font, line, (60, 100 + i * 45))
    text(screen, font, "Enter: back to lobby   Esc: quit", (40, 370))
    pygame.display.flip()
    key = wait_key()
    return key not in (None, pygame.K_ESCAPE)


def run_lobby(args=None):
    pygame.display.init()
    pygame.font.init()
    font = pygame.font.Font(None, 32)
    rows = settings()
    while True:
        screen = pygame.display.set_mode(SIZE)
        pygame.display.set_caption("Learn2Slither - Lobby")
        values = menu(screen, font, rows)
        if values is None:
            break
        try:
            lengths, durations = play(*values)
        except (OSError, ValueError, KeyError) as err:
            print(f"Cannot load model: {err}")
            continue
        screen = pygame.display.set_mode(SIZE)
        if lengths and not results(screen, font, lengths, durations):
            break
    pygame.quit()
    return 0
