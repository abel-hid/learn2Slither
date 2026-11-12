

from environment import Action, Environment, Event

WALL = "W"
HEAD = "H"
BODY = "S"
GREEN = "G"
RED = "R"
EMPTY = "0"

DEFAULT_REWARDS = {
    Event.GREEN_APPLE: 10.0,
    Event.RED_APPLE: -10.0,
    Event.NOTHING: -0.1,
    Event.HIT_WALL: -50.0,
    Event.HIT_SELF: -50.0,
    Event.ZERO_LENGTH: -50.0,
}


class Interpreter:
    def __init__(self, rewards=None):
        self.rewards = dict(DEFAULT_REWARDS)
        if rewards:
            self.rewards.update(rewards)

    def reward(self, event):
        return self.rewards[event]

    def vision(self, env):
        body = set(env.snake[1:])
        rays = {}
        for action in Action:
            row, col = env.snake[0]
            ray = []
            while True:
                row += action.value[0]
                col += action.value[1]
                if not (0 <= row < env.size and 0 <= col < env.size):
                    ray.append(WALL)
                    break
                cell = (row, col)
                if cell in body:
                    ray.append(BODY)
                elif cell in env.green_apples:
                    ray.append(GREEN)
                elif cell in env.red_apples:
                    ray.append(RED)
                else:
                    ray.append(EMPTY)
            rays[action] = ray
        return rays

    def render(self, env):
        rays = self.vision(env)
        left = rays[Action.LEFT]
        indent = " " * len(left)
        lines = [indent + c for c in reversed(rays[Action.UP])]
        lines.append("".join(reversed(left)) + HEAD + "".join(rays[Action.RIGHT]))
        lines += [indent + c for c in rays[Action.DOWN]]
        return "\n".join(lines)


    def state(self, env):
        rays = self.vision(env)
        return tuple(self.encode(rays[action]) for action in Action)

    @staticmethod
    def encode(ray):
        distance = next(i + 1 for i, c in enumerate(ray) if c in (WALL, BODY))
        bucket = min(distance, 3) - 1 # bucket 0 = 1 step, bucket 1 = 2 steps, bucket 2 = 3+ steps
        return (bucket, int(GREEN in ray), int(RED in ray))


if __name__ == "__main__":
    env = Environment(seed=1)
    interp = Interpreter()
    print(interp.render(env))
    print(interp.state(env))