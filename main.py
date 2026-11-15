"""Learn2Slither entry point. Run it through the `snake` launcher:

    ./snake -sessions 10 -save models/10sess.txt -visual off
    ./snake -visual on -load models/100sess.txt -sessions 10 -dontlearn \
            -step-by-step
"""

import argparse
import os
import sys

from agent import Agent
from environment import Environment
from interpreter import Interpreter


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="snake", allow_abbrev=False,
        description="Snake controlled by a Q-learning agent.")
    parser.add_argument("-sessions", type=int, default=1,
                        help="number of training sessions (games)")
    parser.add_argument("-save", metavar="PATH",
                        help="save the learning state to this file")
    parser.add_argument("-load", metavar="PATH",
                        help="load a saved model before playing")
    parser.add_argument("-visual", choices=["on", "off"], default="on",
                        help="display board + terminal output (default: on)")
    parser.add_argument("-dontlearn", action="store_true",
                        help="exploit only: no learning, no exploration")
    parser.add_argument("-step-by-step", dest="step_by_step",
                        action="store_true",
                        help="wait for a key / Enter before every move")
    parser.add_argument("-speed", type=float, default=0.1,
                        help="seconds between moves when visual is on")
    parser.add_argument("-size", type=int, default=10,
                        help="board size (default: 10)")
    parser.add_argument("-maxsteps", type=int, default=2000,
                        help="step cap per session, avoids endless loops")
    parser.add_argument("-seed", type=int, default=None,
                        help="random seed (reproducible runs)")
    parser.add_argument("-lobby", action="store_true",
                        help="open the graphical lobby (menu, stats)")
    args = parser.parse_args(argv)
    if args.sessions < 1:
        parser.error("-sessions must be >= 1")
    if args.size < 4:
        parser.error("-size must be >= 4")
    if args.maxsteps < 1:
        parser.error("-maxsteps must be >= 1")
    return args


def make_viewer(args, env):
    """Graphical display, if requested and available (see gui.py)."""
    if args.visual == "off":
        return None
    try:
        from gui import Display
        return Display(env, args.speed, args.step_by_step)
    except Exception as err:  # no pygame, no screen, ...
        print(f"GUI unavailable ({err}): terminal output only.",
              file=sys.stderr)
        return None


def wait_for_step(viewer, args):
    """Pause / delay before a move. Returns False if the user quit."""
    if viewer is not None:
        return viewer.wait()
    if args.step_by_step:
        try:
            input("[Enter = next step, Ctrl+D = quit] ")
        except EOFError:
            return False
    return True


def run_session(env, interp, agent, viewer, args):
    """Play one game. Returns False if the user asked to quit."""
    verbose = args.visual == "on"
    env.reset()
    state = interp.state(env)
    while not env.done and env.steps < args.maxsteps:
        if viewer is not None:
            viewer.draw()
        if verbose:
            print(interp.render(env))
        if not wait_for_step(viewer, args):
            return False
        action = agent.choose(state)
        if verbose:
            print(f"{action.name}\n")
        result = env.step(action)
        reward = interp.reward(result.event)
        next_state = interp.state(env)
        agent.learn(state, action, reward, next_state, result.done)
        state = next_state
    if viewer is not None:
        viewer.draw()
    return True


def main(argv=None):
    args = parse_args(argv)
    if args.lobby:
        try:
            from lobby import run_lobby
        except ImportError as err:
            print(f"Lobby unavailable ({err})", file=sys.stderr)
            return 1
        return run_lobby(args)
    seed = args.seed
    env = Environment(size=args.size, seed=seed)
    interp = Interpreter()
    agent = Agent(learning=not args.dontlearn,
                  seed=None if seed is None else seed + 1)

    if args.load:
        try:
            agent.load(args.load)
        except (OSError, ValueError, KeyError) as err:
            print(f"Cannot load model '{args.load}': {err}", file=sys.stderr)
            return 1
        print(f"Load trained model from {args.load}")

    viewer = make_viewer(args, env)
    max_length = 0
    max_duration = 0
    progress_every = max(1, args.sessions // 10)

    try:
        for i in range(1, args.sessions + 1):
            keep_going = run_session(env, interp, agent, viewer, args)
            max_length = max(max_length, env.max_length)
            max_duration = max(max_duration, env.steps)
            if not keep_going:
                break
            agent.end_session()
            if args.visual == "on":
                print(f"Session {i}/{args.sessions}: length = "
                      f"{env.max_length}, duration = {env.steps}")
            elif i % progress_every == 0:
                print(f"[{i}/{args.sessions}] best length so far = "
                      f"{max_length}, epsilon = {agent.epsilon:.3f}")
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if viewer is not None:
            viewer.close()

    print(f"Game over, max length = {max_length}, "
          f"max duration = {max_duration}")
    if args.save:
        folder = os.path.dirname(args.save)
        if folder:
            os.makedirs(folder, exist_ok=True)
        agent.save(args.save)
        print(f"Save learning state in {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())