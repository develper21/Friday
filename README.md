# Jean Max - Voice Assistant for Linux (Friday Edition)

A high-performance, intelligent voice assistant for Linux inspired by F.R.I.D.A.Y. / J.A.R.V.I.S.

## Core Features & Improvements

- **⚡ Ultra-Fast Speech Recognition**: Optimized `faster-whisper` (beam size 1 + CUDA + peak volume normalization) for instant command processing with high accuracy.
- **📱 Dynamic Linux App Finder & Control**: Automatically scans desktop applications (`/usr/share/applications`, `~/.local/share/applications`, Flatpak, Snap), parses `.desktop` entries (`Name`, `Exec`, `GenericName`, `Keywords`), and dynamically opens and closes ANY application installed on your system (like pressing Super/Windows key and typing).
- **⏸ Real-Time Voice Interruption**: Say **"Wait Jean"** or **"Stop Jean"** while Jean Max is speaking to instantly stop speech output and trigger the response:
  > *"What happening, i can hear tell me why are you stopping me ?"*
- **🌤 Weather Information**: Accurate weather details (temperature, humidity, wind speed, UV index, air quality index AQI) powered by free APIs without requiring API keys.
- **🔋 System & Battery Stats**: Voice queries for battery percentage, charging status, CPU usage, and RAM consumption.
- **🔊 System Audio Controls**: Increase, decrease, or mute system volume on Linux.
- **🌐 Web & Video Search**: Instantly search Google or YouTube via voice.
- **🕒 Time & Date**: Instant current time and date announcements.

## Usage

Run the assistant:
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python src/main.py
```

## Voice Commands

### Application Search & Control
- `"open chrome"` / `"open vs code"` / `"open calculator"` / `"open terminal"` / `"open spotify"`
- `"close chrome"` / `"close firefox"` / `"close spotify"`
- `"close all apps"`
- `"close all tabs"`

### Interruption
- `"wait jean"` / `"stop jean"` / `"jean stop"` / `"jean wait"` / `"wait a minute"` / `"hold on"`

### System & Device Info
- `"battery status"` / `"how much battery"`
- `"system status"` / `"cpu usage"` / `"ram usage"`
- `"what time is it"` / `"what is today's date"`
- `"volume up"` / `"volume down"` / `"mute volume"`

### Weather & Search
- `"weather"` / `"weather in Delhi"` / `"temperature in Mumbai"`
- `"search google for [query]"` / `"search youtube for [query]"`

### System Power
- `"power off"` / `"shut down"`
- `"restart"` / `"reboot"`

## Architecture

```
voice_assistant/
├── src/
│   ├── audio/          # Microphone input & VAD
│   ├── speech/         # Whisper STT & Edge TTS
│   ├── nlp/            # Intent parser & entity extraction
│   ├── controllers/    # Dynamic Desktop App Manager, Weather, Browser, System
│   ├── config/         # Config loader
│   ├── daemon.py       # Main Voice Assistant Orchestrator
│   └── main.py         # Entry point
├── config/
│   └── config.json
├── requirements.txt
└── README.md
```

