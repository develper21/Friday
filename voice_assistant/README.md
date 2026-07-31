# Voice Assistant

A simple voice-controlled assistant for Linux that can:
- Open and close applications
- Close all applications at once
- Close all browser tabs
- Power off or restart the system

## Features

- **Voice Recognition**: Uses Whisper (faster-whisper) for speech-to-text
- **Command Parsing**: Rule-based NLP for intent detection
- **Application Control**: Open/close Linux applications via voice
- **Browser Control**: Close all browser tabs
- **System Control**: Power off, restart, lock screen
- **Configurable**: JSON-based configuration

## Requirements

- Python 3.8+
- Linux system
- Microphone
- CUDA GPU (optional, for faster Whisper)

## Installation

1. Clone the repository:
```bash
cd voice_assistant
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure audio device:
```bash
# Edit config/config.json
# Set "device" to your microphone device name
```

## Usage

Run the assistant:
```bash
python src/main.py
```

Or use the run script:
```bash
./run.sh
```

## Voice Commands

### Application Control
- "open chrome" - Open Chrome browser
- "close firefox" - Close Firefox
- "close all apps" - Close all applications

### Browser Control
- "close all tabs" - Close all browser tabs

### System Control
- "power off" - Shutdown system (10 second delay)
- "restart" - Restart system (10 second delay)

## Supported Applications

- Chrome (google-chrome)
- Firefox
- Terminal (gnome-terminal)
- VSCode (code)
- Files (nautilus)
- Settings (gnome-control-center)
- Calculator (gnome-calculator)
- Music (spotify)
- Discord
- Telegram
- VLC

## Configuration

Edit `config/config.json`:

```json
{
  "audio": {
    "device": "USB Audio Device",
    "sample_rate": 16000,
    "vad_enabled": true,
    "vad_aggressiveness": 2
  },
  "speech": {
    "model_size": "base",
    "device": "cuda",
    "compute_type": "int8",
    "language": "en"
  },
  "shutdown_delay": 10
}
```

## Architecture

```
voice_assistant/
├── src/
│   ├── audio/          # Audio input and VAD
│   ├── speech/         # Speech recognition (Whisper)
│   ├── nlp/            # Command parsing
│   ├── controllers/    # App, browser, system control
│   ├── config/         # Configuration loader
│   ├── daemon.py       # Main orchestrator
│   └── main.py         # Entry point
├── config/
│   └── config.json
├── requirements.txt
└── README.md
```

## Troubleshooting

### Microphone not detected
- Check audio device name: `python3 -c "import sounddevice as sd; print(sd.query_devices())"`
- Update `device` in config.json

### Whisper model not loading
- Ensure CUDA is available if using GPU
- Try changing `device` to "cpu" in config.json

### Applications not opening
- Ensure applications are installed on your system
- Check the command mapping in `src/controllers/app_manager.py`

## License

MIT License
