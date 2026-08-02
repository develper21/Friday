#!/bin/bash

# Voice Assistant Run Script

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Copy config to user config directory if not exists
CONFIG_DIR="$HOME/.config/voice_assistant"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    echo "Creating config directory..."
    mkdir -p "$CONFIG_DIR"
    cp config/config.json "$CONFIG_DIR/config.json"
    echo "Config created at $CONFIG_DIR/config.json"
    echo "Edit this file to configure your audio device"
fi

# Run the assistant daemon
echo "Starting Voice Assistant Daemon..."
python assistance/main.py
