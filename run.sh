#!/bin/bash
# Simple wrapper to start AlphaSnobAI bot
# Usage: ./run.sh

cd "$(dirname "$0")"

# Check if config exists
if [ ! -f "config/config.yaml" ]; then
    echo "Configuration not found. Running setup..."
    python3 cli.py setup
    exit $?
fi

# Start bot in interactive mode
python3 cli.py start --interactive
