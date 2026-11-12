

import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame 

BACKGROUND = (240, 240, 240)
GRID = (0, 0, 0)
SNAKE = (0, 0, 255)
HEAD = (0, 0, 140)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BAR = (30, 30, 30)
TEXT = (230, 230, 230)
ALERT = (255, 120, 120)

STATUS_HEIGHT = 48
QUIT = "quit"
STEP = "step"


class Display:
    def __init__(self, env, speed=0.1, step_by_step=False):
        pygame.display.init()
        pygame.font.init()
        self.env = env
        self.speed = max(0.0, speed)
        self.step_by_step = step_by_step
        self.cell = max(14, min(48, 640 // env.size))
        self.width = env.size * self.cell
        self.screen = pygame.display.set_mode((self.width, self.width + STATUS_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.font = pygame.font.Font(None, 22)
        self.clock = pygame.time.Clock()
        self.closed = False


    def draw(self):
        if self.closed:
            return
        self._render()
        if self.env.done:
            self.pause(min(self.speed * 3, 0.5))

    def _render(self):
        env = self.env
        self.screen.fill(BACKGROUND, (0, 0, self.width, self.width))
        for cell in env.green_apples:
            self._fill(cell, GREEN)
        for cell in env.red_apples:
            self._fill(cell, RED)
        for i, cell in enumerate(env.snake):
            self._fill(cell, HEAD if i == 0 else SNAKE)
        for i in range(env.size + 1):
            p = min(i * self.cell, self.width - 1)
            pygame.draw.line(self.screen, GRID, (p, 0), (p, self.width))
            pygame.draw.line(self.screen, GRID, (0, p), (self.width, p))
        self._draw_status()
        pygame.display.flip()

    def _fill(self, cell, color):
        row, col = cell
        rect = (col * self.cell + 1, row * self.cell + 1,
                self.cell - 1, self.cell - 1)
        pygame.draw.rect(self.screen, color, rect)

    def _draw_status(self):
        env = self.env
        top = self.width
        self.screen.fill(BAR, (0, top, self.width, STATUS_HEIGHT))
        mode = "STEP" if self.step_by_step else f"{self.speed:.2f}s/move"
        line = f"Length {len(env.snake)}  Steps {env.steps}  {mode}"
        color = TEXT
        if env.done:
            line += "  GAME OVER"
            color = ALERT
        help_line = "SPACE step  S step-mode  +/- speed  Q quit"
        self.screen.blit(self.font.render(line, True, color), (8, top + 6))
        self.screen.blit(self.font.render(help_line, True, TEXT),
                         (8, top + 26))


    def wait(self):
        """Delay before the next move, or block for a key in step mode."""
        if self.closed:
            return False
        deadline = time.monotonic() + self.speed
        while True:
            for event in pygame.event.get():
                action = self.handle(event)
                if action == QUIT:
                    return False
                if action == STEP and self.step_by_step:
                    return True
            if not self.step_by_step and time.monotonic() >= deadline:
                return True
            self.clock.tick(60)

    def pause(self, seconds):
        """Short pause that keeps the window responsive."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not self.closed:
            for event in pygame.event.get():
                self.handle(event)
            self.clock.tick(60)

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.closed = True
            return QUIT
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_q, pygame.K_ESCAPE):
            self.closed = True
            return QUIT
        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT):
            return STEP
        if event.key == pygame.K_s:
            self.step_by_step = not self.step_by_step
            self._render()
        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.speed = 0.0 if self.speed < 0.01 else self.speed * 0.7
            self._render()
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed = min(2.0, max(0.02, self.speed) * 1.4)
            self._render()
        return None

    def close(self):
        pygame.quit()