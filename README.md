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

JeanMax has been refactored with modern design patterns for better maintainability and extensibility.

### New Architecture (Recommended)

```
Friday/
├── core/                    # Core business logic
│   ├── interfaces/          # Abstract interfaces for all services
│   ├── di/                  # Dependency injection container
│   ├── events/              # Event bus for loose coupling
│   ├── observable/          # Observer pattern for state management
│   └── plugins/             # Plugin system for extensibility
├── services/                # Service layer implementations
│   ├── audio/               # Audio & VAD services
│   ├── speech/              # STT & TTS services
│   ├── nlp/                 # Neural engine & intent parser
│   └── controllers/         # Application, system, weather controllers
├── infrastructure/          # Infrastructure layer
│   └── storage/             # Repository pattern for data access
├── plugins/                 # Extensible plugins
├── assistance/              # Voice assistant modules
│   ├── daemon.py            # Original daemon (legacy)
│   └── daemon_refactored.py # New refactored daemon
├── config/                  # Configuration files
├── data/                    # Training data & storage
└── doc/                     # Documentation
```

### Architecture Features

- **Dependency Injection**: Loose coupling between components via DI container
- **Event-Driven**: Components communicate via event bus instead of direct calls
- **Service Layer**: Business logic separated from infrastructure
- **Repository Pattern**: Data access abstraction for easy testing
- **Plugin System**: Extensible architecture for adding new features
- **Observable Pattern**: State management with change notifications

### Migration Status

**✅ Migration Complete** - New architecture is now the default.

**Old Architecture** (Preserved for reference):
- `assistance/daemon_legacy.py` - Original monolithic daemon (backup)

**New Architecture** (Active):
- `assistance/daemon.py` - Refactored daemon with DI & events (now active)
- `core/` - Interfaces, DI container, event bus, plugin system
- `services/` - Service implementations wrapping original code
- `infrastructure/` - Repository layer for data access

### Running the Assistant

**Default (New Architecture)**:
```bash
./run.sh
```

**Using Legacy Daemon** (if needed):
```bash
source venv/bin/activate
python -c "from assistance.daemon_legacy import VoiceAssistantDaemon; from assistance.config.settings import ConfigLoader; daemon = VoiceAssistantDaemon(ConfigLoader().load()); daemon.run()"
```

### Development

**Adding New Features**:
1. Create interface in `core/interfaces/`
2. Implement service in `services/`
3. Register in `core/di/service_config.py`
4. Use in `daemon_refactored.py`

**Creating Plugins**:
1. Implement `IPlugin` interface
2. Place in `plugins/` directory
3. Load via `PluginManager`

