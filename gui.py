import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

from art import draw_apple, draw_snake, font, mix  # noqa: E402

LIGHT = (40, 62, 46)
DARK = (33, 52, 39)
FRAME = (16, 22, 20)
BAR = (17, 21, 27)
TEXT = (232, 236, 240)
MUTED = (135, 145, 158)
ACCENT = (90, 200, 255)
ALERT = (255, 95, 95)

STATUS_HEIGHT = 64
MIN_WIDTH = 420
QUIT = "quit"
STEP = "step"


class Display:
    def __init__(self, env, speed=0.1, step_by_step=False):
        pygame.display.init()
        pygame.font.init()
        self.env = env
        self.speed = max(0.0, speed)
        self.step_by_step = step_by_step
        self.cell = max(14, min(64, 640 // env.size))
        self.board = env.size * self.cell
        self.width = max(self.board, MIN_WIDTH)
        self.left = (self.width - self.board) // 2
        self.screen = pygame.display.set_mode(
            (self.width, self.board + STATUS_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.background = self.make_background()
        self.direction = (0, -1)
        self.clock = pygame.time.Clock()
        self.closed = False

    def make_background(self):
        surf = pygame.Surface((self.width, self.board))
        surf.fill(FRAME)
        for row in range(self.env.size):
            for col in range(self.env.size):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                surf.fill(color, (self.left + col * self.cell,
                                  row * self.cell, self.cell, self.cell))
        return surf

    def center(self, cell):
        row, col = cell
        return (self.left + col * self.cell + self.cell / 2,
                row * self.cell + self.cell / 2)

    def draw(self):
        if self.closed:
            return
        self.render()
        if self.env.done:
            self.pause(min(self.speed * 3, 0.5))

    def render(self):
        env = self.env
        self.screen.blit(self.background, (0, 0))
        for cell in env.green_apples:
            draw_apple(self.screen, self.center(cell), self.cell, "green")
        for cell in env.red_apples:
            draw_apple(self.screen, self.center(cell), self.cell, "red")
        if len(env.snake) > 1:
            (r0, c0), (r1, c1) = env.snake[0], env.snake[1]
            self.direction = (c0 - c1, r0 - r1)
        points = [self.center(cell) for cell in env.snake]
        draw_snake(self.screen, points, self.cell, self.direction,
                   tongue=env.steps % 4 < 2, dead=env.done)
        if env.done:
            self.draw_game_over()
        self.draw_status()
        pygame.display.flip()

    def draw_game_over(self):
        veil = pygame.Surface((self.board, self.board), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 90))
        self.screen.blit(veil, (self.left, 0))
        label = font(max(22, self.board // 10), True).render(
            "GAME OVER", True, ALERT)
        box = label.get_rect(center=(self.width // 2, self.board // 2))
        pygame.draw.rect(self.screen, BAR, box.inflate(36, 16),
                         border_radius=14)
        pygame.draw.rect(self.screen, mix(BAR, ALERT, 0.5),
                         box.inflate(36, 16), 2, border_radius=14)
        self.screen.blit(label, box)

    def draw_status(self):
        env = self.env
        top = self.board
        self.screen.fill(BAR, (0, top, self.width, STATUS_HEIGHT))
        pygame.draw.line(self.screen, mix(BAR, ACCENT, 0.5),
                         (0, top), (self.width, top))
        x = self.stat("LENGTH", len(env.snake), 14, top + 8)
        x = self.stat("STEPS", env.steps, x, top + 8)
        if env.done:
            self.chip("GAME OVER", ALERT, x, top + 9)
        elif self.step_by_step:
            self.chip("STEP MODE", ACCENT, x, top + 9)
        else:
            self.chip(f"{self.speed:.2f}s / move", ACCENT, x, top + 9)
        hints = font(14).render(
            "SPACE step    S step mode    +/- speed    Q quit", True, MUTED)
        self.screen.blit(hints, (14, top + 40))

    def stat(self, name, value, x, y):
        label = font(12, True).render(name, True, MUTED)
        number = font(20, True).render(str(value), True, TEXT)
        self.screen.blit(label, (x, y + 9))
        self.screen.blit(number, (x + label.get_width() + 6, y + 1))
        return x + label.get_width() + number.get_width() + 22

    def chip(self, text, color, x, y):
        label = font(13, True).render(text, True, color)
        rect = pygame.Rect(x, y, label.get_width() + 20, 24)
        pygame.draw.rect(self.screen, mix(BAR, color, 0.18), rect,
                         border_radius=12)
        pygame.draw.rect(self.screen, mix(BAR, color, 0.55), rect, 1,
                         border_radius=12)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def wait(self):
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
            self.render()
        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.speed = 0.0 if self.speed < 0.01 else self.speed * 0.7
            self.render()
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed = min(2.0, max(0.02, self.speed) * 1.4)
            self.render()
        return None

    def close(self):
        pygame.quit()
