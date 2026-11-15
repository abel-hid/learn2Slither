
import random
from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    UP = (-1, 0)
    LEFT = (0, -1)
    DOWN = (1, 0)
    RIGHT = (0, 1)


class Event(Enum):
    NOTHING = "nothing"
    GREEN_APPLE = "green_apple"
    RED_APPLE = "red_apple"
    HIT_WALL = "hit_wall"
    HIT_SELF = "hit_self"
    ZERO_LENGTH = "zero_length"
              

GAME_OVER_EVENTS = {Event.HIT_WALL, Event.HIT_SELF, Event.ZERO_LENGTH}


@dataclass
class StepResult:
    event: Event
    done: bool


class Environment:
    def __init__(self, size=10, n_green=2, n_red=1, seed=None):
        self.size = size
        self.n_green = n_green
        self.n_red = n_red
        self.rng = random.Random(seed)
        self.snake = []
        self.green_apples = []
        self.red_apples = []
        self.steps = 0
        self.max_length = 0
        self.done = False
        self.reset()


    def reset(self):
        """Start a new training session (game)."""
        self.snake = self.spawn_snake(3)
        self.green_apples = []
        self.red_apples = []
        for _ in range(self.n_green):
            self.spawn_apple(self.green_apples)
        for _ in range(self.n_red):
            self.spawn_apple(self.red_apples)
        self.steps = 0
        self.max_length = len(self.snake)
        self.done = False

    def step(self, action):
        """Move the snake one cell and report what happened."""
        if self.done:
            raise RuntimeError("Game is over, call reset() first.")
        self.steps += 1

        row, col = self.snake[0]
        d_row, d_col = action.value
        new_head = (row + d_row, col + d_col)

        if not self.in_bounds(new_head):
            return self.finish(Event.HIT_WALL)

        event = Event.NOTHING
        delta = 0
        if new_head in self.green_apples:
            event, delta = Event.GREEN_APPLE, 1
        elif new_head in self.red_apples:
            event, delta = Event.RED_APPLE, -1


        new_len = len(self.snake) + delta
        if new_len == 0:
            return self.finish(Event.ZERO_LENGTH)

        body = [new_head]
        for cell in self.snake:
            body.append(cell)
        while len(body) > new_len:
            body.pop()

        if body.count(new_head) > 1:
            return self.finish(Event.HIT_SELF)
        self.snake = body
        if event is Event.GREEN_APPLE:
            self.green_apples.remove(new_head)
            self.spawn_apple(self.green_apples)
        elif event is Event.RED_APPLE:
            self.red_apples.remove(new_head)
            self.spawn_apple(self.red_apples)

        self.max_length = max(self.max_length, len(self.snake))
        return StepResult(event, False)


    def finish(self, event):
        self.done = True
        return StepResult(event, True)

    def in_bounds(self, cell):
        return 0 <= cell[0] < self.size and 0 <= cell[1] < self.size

    def neighbors(self, cell):
        for action in Action:
            nxt = (cell[0] + action.value[0], cell[1] + action.value[1])
            if self.in_bounds(nxt):
                yield nxt

    def free_cells(self):
        taken = set(self.snake)
        taken.update(self.green_apples)
        taken.update(self.red_apples)

        free = []
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) not in taken:
                    free.append((r, c))
        return free

    def spawn_apple(self, apple_list):
        free = self.free_cells()
        if free:
            apple_list.append(self.rng.choice(free))

    def spawn_snake(self, length):
        while True:
            body = [(self.rng.randrange(self.size), self.rng.randrange(self.size))]
            while len(body) < length:
                options = []
                for action in Action:
                    nxt = (body[-1][0] + action.value[0], body[-1][1] + action.value[1])
                    if self.in_bounds(nxt) and nxt not in body:
                        options.append(nxt)
                if not options:
                    break
                body.append(self.rng.choice(options))
            if len(body) == length:
                return body


def main():
    env = Environment(size=10, n_green=1, n_red=1, seed=42)
    while not env.done:
        action = random.choice(list(Action))
        result = env.step(action)
        print(f"Action: {action}, Result: {result}, Snake: {env.snake}")


if __name__ == "__main__":
    main()