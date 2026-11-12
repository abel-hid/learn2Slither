
import json
import random

from environment import Action

ACTIONS = list(Action)
INDEX = {action: i for i, action in enumerate(ACTIONS)}
ZEROS = [0.0] * len(ACTIONS)


class Agent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.99, learning=True, seed=None):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning = learning
        self.sessions = 0
        self.q = {}
        self.rng = random.Random(seed)


    def choose(self, state):
        """Epsilon-greedy while learning, pure greedy otherwise."""
        if self.learning and self.rng.random() < self.epsilon:
            return self.rng.choice(ACTIONS)
        values = self.q.get(state, ZEROS)
        best = max(values)
        ties = [i for i, v in enumerate(values) if v == best]
        return ACTIONS[self.rng.choice(ties)]


    def learn(self, state, action, reward, next_state, done):
        """Q(s,a) += alpha * (r + gamma * max Q(s',.) - Q(s,a))."""
        if not self.learning:
            return
        values = self.q.setdefault(state, [0.0] * len(ACTIONS))
        future = 0.0
        if not done:
            future = max(self.q.get(next_state, ZEROS))
        i = INDEX[action]
        target = reward + self.gamma * future
        values[i] += self.alpha * (target - values[i])

    def end_session(self):
        """Call once per finished game."""
        self.sessions += 1
        if self.learning:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


    def save(self, path):
        q_data = {}
        for state, values in self.q.items():
            key = json.dumps(state)
            q_data[key] = values

        data = {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "sessions": self.sessions,
            "q": q_data,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path):
        with open(path) as f:
            data = json.load(f)

        self.alpha = data["alpha"]
        self.gamma = data["gamma"]
        self.epsilon = data["epsilon"]
        self.epsilon_min = data["epsilon_min"]
        self.epsilon_decay = data["epsilon_decay"]
        self.sessions = data["sessions"]

        self.q = {}
        for key, values in data["q"].items():
            directions = []
            for direction in json.loads(key):
                directions.append(tuple(direction))
            state = tuple(directions)
            self.q[state] = values