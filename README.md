# Learn2Slither

A snake that learns to play by itself through **reinforcement learning**
(Q-learning). It only sees what is in the 4 directions from its head, and
by trial and error it learns to eat green apples, avoid red apples, and stay
alive.

---

## Quick start

```sh
python3 -m venv .venv              # create a Python environment
. .venv/bin/activate               # activate it
pip install pygame flake8          # install the dependencies
chmod +x snake                     # make the launcher executable (once)
./snake -lobby                     # graphical lobby: pick a model, play, see stats
```

Requirements: Python 3.11+ and `pygame` 2.x. `flake8` is only needed to
check the code style. The launcher can also be run as `python3 snake ...`.

---

## Usage

```sh
# Train 10 sessions from scratch, no display, save the model
./snake -sessions 10 -save models/10sess.txt -visual off

# Watch a trained model, without learning, one move per key press
./snake -visual on -load models/100sess.txt -sessions 10 -dontlearn -step-by-step

# Best model on a bigger board
./snake -visual on -load models/10000sess.txt -dontlearn -size 15
```

| Option | Default | Meaning |
|---|---|---|
| `-sessions N` | 1 | Number of training sessions (games) to play |
| `-save PATH` | | Save the learning state (model) to this file at the end |
| `-load PATH` | | Load a model before playing |
| `-visual on/off` | on | Graphical board + terminal vision output |
| `-dontlearn` | off | Exploitation only: no Q-table update, no random moves |
| `-step-by-step` | off | Wait for a key (SPACE / Enter) before every move |
| `-speed S` | 0.1 | Seconds between two moves |
| `-size N` | 10 | Board size (N x N, minimum 4) |
| `-maxsteps N` | 2000 | Move limit per session (stops endless loops) |
| `-seed N` | | Random seed, for reproducible runs |
| `-lobby` | | Open the graphical lobby |

At the end of a run the program prints:

```
Game over, max length = 12, max duration = 55
Save learning state in models/10sess.txt
```

### Keys in the game window

| Key | Action |
|---|---|
| SPACE / Enter / Right | Next move (step-by-step mode) |
| S | Toggle step-by-step mode |
| + / - | Faster / slower |
| Q / Esc | Stop |

### What you see

- A blue snake with a tapered body, scales and a head with eyes that look
  where it is going and a flicking tongue. When it dies, its eyes turn
  into crosses and a **GAME OVER** banner appears.
- **Green apples** (good, +1 length) and **red apples** (bad, -1 length),
  drawn as real apples with a stem and a leaf.
- A checkerboard grass board, and a status bar with the length, the number
  of steps and the current speed or step mode.

Everything is drawn in code with anti-aliased shapes (`art.py`), so the
project needs no image files.

---

## The rules (environment)

- Board of 10 x 10 cells (changeable with `-size`).
- 2 green apples and 1 red apple, at random free cells.
- The snake starts with length 3, placed randomly and contiguously.
- Green apple: length + 1, a new green apple appears.
- Red apple: length - 1, a new red apple appears.
- **Game over** if the snake hits a wall, hits its own body, or its length
  drops to 0.

---

## How it works

The program follows the structure required by the subject:

```
        ┌──────────────┐
        │ ENVIRONMENT  │◄──────────── action ──────────┐
        └──────┬───────┘                               │
               │ board                                 │
        ┌──────▼───────┐   reward    ┌─────────────┐   │
        │ INTERPRETER  ├────────────►│    AGENT    ├───┘
        │              ├────────────►│  (Q-table)  │
        └──────────────┘   state     └─────────────┘
```

| File | Role |
|---|---|
| `environment.py` | The board: snake, apples, moves, collisions, game over |
| `interpreter.py` | Turns the board into the snake's **vision**, the **state**, and the **reward** |
| `agent.py` | Q-learning agent: chooses actions, updates the Q-table, save / load |
| `main.py` | Command line, training loop, statistics |
| `gui.py` | Pygame window showing the board |
| `lobby.py` | Bonus: lobby, configuration panel, results screen |
| `art.py` | Drawing helpers: the snake, the apples, fonts (shared by the board and the lobby) |
| `snake` | Launcher (`./snake ...`) |

### 1. Vision

The snake only sees the 4 lines going out from its head (up, left, down,
right) up to the wall. It is printed in the terminal before every move:

```
          W
          0
          G
          R
          0
W000000000HW
          S
          0
          W
UP
```

`W` wall, `H` head, `S` body, `G` green apple, `R` red apple, `0` empty.

### 2. State

The agent gets **only** this vision, never the full board. Each of the 4
directions is summarised as 3 numbers:

| Value | Meaning |
|---|---|
| danger | Distance to the first wall or body cell: `0` = next cell, `1` = 2 cells away, `2` = 3 or more |
| green | `1` if a green apple is visible in this direction, else `0` |
| red | `1` if a red apple is visible in this direction, else `0` |

So a state is 4 x (danger, green, red). The state does not depend on the
board size, which is why the same model can play on any board.

### 3. Actions

`UP`, `LEFT`, `DOWN`, `RIGHT`.

### 4. Rewards

| Event | Reward |
|---|---|
| Green apple | +10 |
| Red apple | -10 |
| Nothing eaten | -0.1 |
| Game over (wall, body, length 0) | -50 |

The small negative reward for an empty move pushes the snake to go find
food instead of wandering.

### 5. Q-learning

The agent keeps a **Q-table**: for every state seen, one value per action,
estimating how good that action is. After every move it is updated with:

```
Q(s, a) ← Q(s, a) + α · (r + γ · max Q(s', ·) − Q(s, a))
```

| Parameter | Value | Meaning |
|---|---|---|
| α (alpha) | 0.1 | Learning rate |
| γ (gamma) | 0.9 | How much future rewards count |
| ε (epsilon) | 1.0 → 0.01 | Chance of a random move (exploration) |
| ε decay | × 0.99 per session | Explores less and less over time |

**Exploration vs exploitation:** with probability ε the agent moves at
random to discover new things; otherwise it picks the action with the
highest Q-value. With `-dontlearn`, ε is ignored and the table is never
updated, which makes it possible to measure a model without changing it.

### 6. Models

A model is a JSON text file in `models/` holding the Q-table and the agent
parameters (α, γ, ε, number of sessions played). It can be loaded to
continue training or just to play.

---

## Trained models

Results of each model on 300 games, 10 x 10 board, `-dontlearn`:

| Model | Avg length | Reached 10+ | Best length |
|---|---|---|---|
| `1sess.txt` | 3.0 | 0% | 4 |
| `10sess.txt` | 3.0 | 0% | 5 |
| `100sess.txt` | 3.1 | 0% | 5 |
| `1000sess.txt` | 8.3 | 35% | 26 |
| `3000sess.txt` | 14.8 | 76% | 29 |
| `10000sess.txt` | **19.0** | **91%** | **42** |

`10000sess.txt` is the best model (its file records 20 000 sessions
played). Each model was trained by continuing from the previous one.

---

## Bonus

- **Higher length**: the best model ends a 10 x 10 game with an average
  length of 19 (75% of games reach 15, about half reach 20).
- **Lobby**: `./snake -lobby` opens an animated menu (a snake crawls along
  the bottom of the screen) to choose the model, number of sessions, board
  size, speed and learning on/off. After the games, a results screen shows
  the number of games, the average and best length, the % of games
  reaching 10, the durations, and a chart of the length per game with the
  goal of 10 marked.

  | Key | Lobby | Results screen |
  |---|---|---|
  | Up / Down | Select a setting | |
  | Left / Right | Change its value | |
  | Enter | Start playing | Back to the lobby |
  | Esc | Quit | Quit |
- **Board size**: `-size N` changes the board, and the same models still
  work because the state does not depend on the size:

| Board | 5x5 | 8x8 | 10x10 | 15x15 | 20x20 |
|---|---|---|---|---|---|
| Avg length (10000sess) | 10.2 | 16.2 | 19.0 | 26.6 | 32.5 |

---

## Code style

The code follows the flake8 norm:

```sh
flake8 --exclude .venv .
```
