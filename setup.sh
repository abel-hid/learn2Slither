#!/bin/sh
# Create the Python environment for Learn2Slither.
# Usage:  ./setup.sh   then   . .venv/bin/activate
set -e
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
    echo "Using uv"
    uv sync
else
    echo "uv not found, using python3 -m venv + pip"
    python3 -m venv .venv
    .venv/bin/pip install --quiet --upgrade pip
    .venv/bin/pip install --quiet "pygame>=2.6.1" "flake8>=7.0"
fi

# make sure the launchers are executable with Unix line endings
sed -i.bak 's/\r$//' snake train.sh && rm -f snake.bak train.sh.bak
chmod +x snake train.sh

.venv/bin/python -c "import pygame" >/dev/null
echo
echo "Environment ready. Activate it with:"
echo "    . .venv/bin/activate"
echo "Then run for example:"
echo "    ./snake -lobby"
echo "    ./snake -visual on -load models/100sess.txt -dontlearn -step-by-step"
