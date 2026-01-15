# AIST Project - Comprehensive Analysis
**Generated: January 15, 2026**

---

## 📋 Executive Summary

**AIST (Autonomous Intelligent System)** is a sophisticated, modular, offline-first AI assistant for Windows that operates on a robust **client-server architecture**. It combines local LLM (Large Language Model), Speech-to-Text (STT), and Text-to-Speech (TTS) engines to provide a completely privacy-respecting, voice-controlled assistant that runs entirely on your local machine.

**Current Status:** In active development with core functionality working. Recent fixes have stabilized the multi-process communication layer.

---

## 🏗️ Architecture Overview

### Multi-Process Design

AIST operates as **3 concurrent processes** launched by `start.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AIST Master Launcher (start.py)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Backend        │  │     Frontend     │  │      GUI     │  │
│  │  ("The Brain")   │  │   ("The Face")   │  │              │  │
│  │                  │  │                  │  │              │  │
│  │ run_backend.py   │  │    main.py       │  │    gui.py    │  │
│  │                  │  │                  │  │              │  │
│  │ • LLM Loading    │  │ • STT Engine     │  │ • Status UI  │  │
│  │ • Skill Manager  │  │ • TTS Output     │  │ • Logging    │  │
│  │ • IPC Server     │  │ • Hotkey Mgmt    │  │ • Commands   │  │
│  │ • Event Bus      │  │ • System Tray    │  │              │  │
│  └────────────┬─────┘  └────────┬─────────┘  └────────┬─────┘  │
│               │                 │                     │         │
│               └─────────────────┼─────────────────────┘         │
│                   IPC (ZeroMQ)  │                               │
│                                 │                               │
│         • Command Port 5555 (REQ/REP)                           │
│         • Event Bus Port 5556 (PUB/SUB)                         │
│         • Log Port 5558 (PUB/SUB)                               │
│         • Text Command Port 5557 (PULL)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Process Responsibilities

| Process | Module | Role | Key Tasks |
|---------|--------|------|-----------|
| **Backend** | `run_backend.py` | Brain | Loads LLM, manages skills, processes intents, IPC server |
| **Frontend** | `main.py` | Face | Listens to microphone, handles TTS, system tray, hotkeys |
| **GUI** | `gui.py` | Monitor | Displays status, logs, allows text input |

---

## 🧠 Core Logic Flow

### The AI-Driven Command Processing Loop

```
USER SPEAKS
    ↓
[Frontend - main.py]
    ↓
STT Engine (Vosk/Whisper)
    ↓
Transcribe to Text
    ↓
Send to Backend via IPC (Port 5555)
    ↓
[Backend - run_backend.py]
    ↓
command_dispatcher() [aist/skills/dispatcher.py]
    ├─ Check state: DORMANT vs LISTENING
    ├─ Check activation/deactivation phrases
    ├─ Fuzzy match fast-path intents
    └─ Ask LLM to determine user intent
    ↓
LLM Intent Recognition [aist/core/llm.py]
    ├─ Load conversation history
    ├─ Build system prompt with available skills
    ├─ Query LLM for decision (JSON response)
    └─ Parse LLM response for intent + parameters
    ↓
Skill Execution [aist/skills/dispatcher.py]
    ├─ Execute chosen skill (sandboxed subprocess)
    ├─ Fallback to chat if no skill matches
    └─ Summarize system output if needed
    ↓
Build Response JSON
    ├─ action: ACTIVATE/DEACTIVATE/EXIT/COMMAND
    ├─ speak: Text to say
    └─ intent: Matched intent info
    ↓
Send Response to Frontend via IPC
    ↓
[Frontend - main.py]
    ↓
Execute Action (state change)
    ↓
TTS Engine (Piper)
    ↓
Speak Response
    ↓
Wait for Next User Input
```

---

## 🗂️ Directory Structure & Key Files

```
AIST/
├── start.py                      # Master launcher for all 3 processes
├── run_backend.py                # Backend entry point
├── main.py                        # Frontend entry point
├── gui.py                         # GUI entry point
├── config.yaml                    # Configuration file
├── requirements.txt               # Python dependencies
│
├── aist/
│   ├── __init__.py
│   │
│   ├── core/                      # Core functionality
│   │   ├── llm.py                # LLM loading & interaction
│   │   ├── stt.py                # STT engine management
│   │   ├── tts.py                # TTS engine management
│   │   ├── audio.py              # PyAudio management
│   │   ├── conversation.py       # Conversation history
│   │   ├── memory.py             # SQLite memory system
│   │   ├── config_manager.py     # YAML config handling
│   │   ├── log_setup.py          # Logging configuration
│   │   ├── events.py             # PyPubSub event bus
│   │   ├── trigger_manager.py    # Hotkey management
│   │   │
│   │   └── ipc/                  # Inter-process communication
│   │       ├── protocol.py       # IPC message constants
│   │       ├── server.py         # Backend IPC server
│   │       ├── client.py         # Frontend IPC client
│   │       ├── event_bus.py      # Event broadcaster
│   │       └── gui.py            # GUI IPC utilities
│   │
│   ├── skills/                    # Skill system
│   │   ├── base.py               # Skill base class
│   │   ├── dispatcher.py         # Command routing logic
│   │   ├── skill_loader.py       # Skill discovery & loading
│   │   ├── memory_skill/         # Store/recall facts
│   │   ├── system_skill/         # System control
│   │   └── time_skill/           # Current time
│   │
│   ├── stt_providers/             # Speech-to-Text engines
│   │   ├── base.py               # Provider base class
│   │   ├── vosk_provider.py      # Vosk implementation
│   │   └── whisper_provider.py   # Whisper implementation
│   │
│   ├── tts_providers/             # Text-to-Speech engines
│   │   ├── base.py               # Provider base class
│   │   └── piper_provider.py     # Piper TTS
│   │
│   └── gui/
│       ├── main_window.py        # GUI application
│       └── __init__.py
│
├── data/
│   ├── models/
│   │   ├── llm/                  # LLM GGUF files
│   │   ├── stt/                  # STT models (Vosk)
│   │   └── tts/                  # TTS models (Piper)
│   ├── logs/                      # Log files
│   └── memory/                    # SQLite databases
│
└── [Documentation files]
    ├── README.md
    ├── Documentation.md
    ├── PROJECT_OVERVIEW.md
    ├── CHANGELOG.md
    ├── TODO.md
    └── config.template.yaml
```

---

## 🔌 Inter-Process Communication (IPC)

### ZeroMQ Socket Architecture

AIST uses **ZeroMQ (0MQ)** for fast, reliable inter-process communication:

| Channel | Type | Port | Purpose | Participants |
|---------|------|------|---------|--------------|
| **Command** | REQ/REP | 5555 | Synchronous commands | Frontend/GUI → Backend |
| **Event Bus** | PUB/SUB | 5556 | Asynchronous events | Backend → Frontend/GUI |
| **Log Broadcast** | PUB/SUB | 5558 | Real-time logs | Backend → GUI |
| **Text Commands** | PULL | 5557 | External text input | External Tools → Frontend |

### Message Format

**Command Request (Frontend → Backend):**
```json
{
  "type": "command",
  "payload": {
    "text": "user input text",
    "state": "DORMANT|LISTENING"
  }
}
```

**Response (Backend → Frontend):**
```json
{
  "action": "ACTIVATE|DEACTIVATE|EXIT|COMMAND",
  "speak": "Response text to speak",
  "intent": {
    "name": "intent_name",
    "params": { "key": "value" }
  }
}
```

**Event Broadcast (Backend → All Clients):**
```json
{
  "type": "event_type",
  "payload": { "key": "value" }
}
```

---

## 🧩 Skill System

### Architecture

Skills are **pluggable capabilities** that extend AIST's functionality. They use a decorator-based discovery system:

```python
@aist_skill
def open_application(app_name: str) -> str:
    """Opens a specified application by name or path."""
    os.startfile(app_name)
    return f"Opened {app_name}"
```

### Skill Execution Flow

1. **User Command** → Backend receives "open notepad"
2. **Dispatcher** → Asks LLM which skill to use
3. **LLM Response** → `{"function": "open_application", "parameters": {"app_name": "notepad"}}`
4. **Execution** → Skill runs in **sandboxed subprocess** (prevents crashes from affecting main process)
5. **Response** → Result sent back to user via TTS

### Available Skills

| Skill | File | Intents | Purpose |
|-------|------|---------|---------|
| **Memory** | `aist/skills/memory_skill/` | `store_memory`, `recall_memory` | Store & retrieve facts |
| **System** | `aist/skills/system_skill/` | `open_application` | System control |
| **Time** | `aist/skills/time_skill/` | `get_current_time` | Report current time |

### Skill Manager

- **Location:** `aist/skills/skill_loader.py`
- **Functionality:** Auto-discovers decorated functions, builds intent registry
- **Intent Registry:** Maps skill names to parameters for LLM use
- **Manifest Files:** Each skill has `skill.json` with metadata

---

## 🤖 Large Language Model (LLM)

### Configuration

- **Model:** Mistral-7B-Instruct-v0.2.Q4_K_M.gguf (quantized)
- **Framework:** ctransformers
- **Location:** `data/models/llm/`
- **GPU Support:** Configurable via `gpu_layers` in config.yaml
- **Prompting Strategy:**
  - Context window: 4096 tokens
  - Max new tokens: 150
  - Temperature: 0.3 (for chat), 0.0 (for structured tasks)
  - Conversation history: Last 5 exchanges

### LLM Usage Patterns

1. **Intent Recognition:** "What skill should I use?" (deterministic, temp=0.0)
2. **Chat Response:** "Answer this conversationally" (creative, temp=0.3)
3. **Output Summarization:** "Summarize this system command output for the user"

---

## 🎙️ Speech-to-Text (STT)

### Providers

| Provider | Speed | Accuracy | Offline | Usage |
|----------|-------|----------|---------|-------|
| **Vosk** | Fast | Medium | Yes | Default, lightweight |
| **Whisper** | Slower | High | Yes | Alternative, better accuracy |

### Vosk Provider Details

- **Model:** vosk-model-en-us-0.22
- **VAD (Voice Activity Detection):** Energy-based threshold
- **Grammar:** Dynamic grammar using activation/exit phrase lists
- **State Management:** Dormant recognizer (limited phrases) vs Listening recognizer (full speech)

### Configuration

```yaml
audio:
  stt:
    confidence_threshold: 0.85      # Min confidence for accepting transcription
    energy_threshold: 600            # VAD sensitivity (lower = more sensitive)
```

---

## 🗣️ Text-to-Speech (TTS)

### Provider

- **Engine:** Piper TTS
- **Voice:** en_US-lessac-medium
- **Model Files:** `.onnx` and `.json` in `data/models/tts/`
- **Quality:** High-quality, natural-sounding offline synthesis
- **Latency:** Reasonable for real-time conversation

---

## ⚙️ Configuration System

### config.yaml Sections

```yaml
assistant:
  activation_phrases: [list of wake-up phrases]
  exit_phrases: [list of shutdown phrases]
  deactivation_phrases: [list of sleep phrases]
  fuzzy_match_threshold: 85         # Similarity % for phrase matching
  skill_timeout: 5                  # Max seconds a skill can run
  conversation_history_length: 5    # Context exchanges to remember

ipc:
  command_port: 5555
  event_bus_port: 5556
  log_broadcast_port: 5558
  text_command_port: 5557

models:
  llm:
    path: "./data/models/llm/..."
    gpu_layers: 0                    # 0 = CPU only, higher = more GPU
    context_length: 4096
    max_new_tokens: 150
  tts:
    provider: "piper"
    piper_voice_model: "data/models/tts/..."
  stt:
    provider: "vosk"                 # or "whisper"
    vosk_model_path: "data/models/stt/..."
    whisper_model_name: "base.en"
    whisper_device: "cpu"            # or "cuda"

audio:
  stt:
    confidence_threshold: 0.85
    energy_threshold: 600            # VAD tuning for your environment

logging:
  folder: "data/logs"
  console_enabled: false

hotkeys:
  quit: "ctrl+win+x"                # Global application exit
```

---

## 📊 State Machine

AIST operates on a simple 2-state model:

```
┌──────────────┐                    ┌────────────┐
│   DORMANT    │                    │ LISTENING  │
│              │                    │            │
│ • Passive    │ ────activation───→ │ • Active   │
│   listening  │   phrase detected  │   listening│
│ • Low CPU    │                    │ • High CPU │
│ • Only hears │←──exit/pause       │ • Hears    │
│   wake words │   phrases          │   all      │
└──────────────┘                    └────────────┘
```

**State Constants:** Defined in `aist/core/ipc/protocol.py`

---

## 💾 Persistent Memory System

### Database

- **Type:** SQLite3
- **Location:** `data/memory/`
- **Purpose:** Store and retrieve user facts, preferences
- **Module:** `aist/core/memory.py`

### Skill Integration

Memory is used by the LLM when generating responses:
1. User command → Extract keywords
2. Query database for relevant facts
3. Include facts in LLM prompt context
4. LLM generates more informed response

---

## 📝 Logging System

### Architecture

- **Main Log:** `data/logs/aist.log` (rotating file handler)
- **Console Output:** Color-coded, human-readable status messages
- **Log Levels:** DEBUG, INFO, WARNING, ERROR
- **Components:** Each module has its own logger

### Log Setup

- **Frontend:** `setup_logging(is_frontend=True)` - Disables file logging, enables console
- **Backend:** `setup_logging(is_frontend=False)` - Full logging
- **GUI:** Subscribes to log events via IPC for real-time display

---

## 🛠️ Technology Stack

### Core Dependencies

| Category | Technology | Purpose |
|----------|-----------|---------|
| **LLM** | ctransformers | Local model inference |
| **STT** | vosk, openai-whisper | Speech recognition |
| **TTS** | piper-tts | Speech synthesis |
| **Audio** | pyaudio | Microphone/speaker I/O |
| **IPC** | pyzmq | Inter-process communication |
| **GUI** | customtkinter | Modern desktop UI |
| **System Integration** | pystray, keyboard | Tray icon, global hotkeys |
| **Config** | PyYAML | Configuration parsing |
| **Fuzzy Matching** | thefuzz | String similarity |
| **Pub/Sub** | pypubsub | Event system |

---

## ✅ Recent Fixes (August 2025)

### Resolved Issues

1. **Address in use (Port 5556):** Frontend no longer tries to bind; now subscribes to backend's event bus
2. **Skill Subprocess Crashes:** Console logging disabled for Windows child processes
3. **Hardcoded Whisper Model:** Now reads `whisper_model_name` from config
4. **GUI Status Updates:** Backend broadcasts initialization status via event bus
5. **IPC Protocol:** Centralized message type definitions in `protocol.py`
6. **Skill Manager Initialization:** Now initializes before IPC server starts accepting commands

### Improvements

- **Headless Components:** Backend/Frontend launch without console windows (Windows-only)
- **Better Error Handling:** More defensive checks in STT providers
- **Cleaner Architecture:** Separated Frontend/Backend concerns clearly

---

## 🚀 Current Status

### Working ✅

- ✅ Core multi-process architecture
- ✅ IPC communication (ZeroMQ)
- ✅ LLM inference (Mistral-7B)
- ✅ Vosk STT engine
- ✅ Piper TTS engine
- ✅ Skill discovery & execution (sandboxed)
- ✅ Memory system (SQLite)
- ✅ State machine (DORMANT/LISTENING)
- ✅ System tray integration
- ✅ Global hotkey registration
- ✅ Comprehensive logging
- ✅ Configuration system (YAML)

### In Progress 🔄

- 🔄 GUI enhancements (status indicators, real-time interaction)
- 🔄 Additional skills (weather, system control)
- 🔄 Whisper STT integration & testing

### Not Yet Implemented ❌

- ❌ Voice cloning
- ❌ Advanced OS automation (mouse/keyboard control)
- ❌ Web-based skills (weather, news)
- ❌ Packaged .exe distribution
- ❌ Multi-language support

---

## 📈 Recent Issues from Log Analysis

Based on log file review (`data/logs/aist.log`):

1. **System Operational:** System initialized and ran successfully
2. **Voice Input Works:** "hello bucket assist assist start" was recognized
3. **Graceful Shutdown:** Application handled Ctrl+C correctly
4. **PIL Import Warnings:** Non-critical, PIL plugins loading
5. **No Critical Errors:** No crashes or unhandled exceptions

### Log Timeline (2026-01-15 13:26:01 - 13:29:09)

- Initialization: ~40 seconds (LLM loading)
- Full operational: All components initialized
- Session duration: ~3 minutes
- Shutdown: Clean and orderly

---

## 🔮 Roadmap Priorities

### Tier 1: Immediate (Skills & Feedback)
- [ ] Implement additional system control skills
- [ ] Add audio cues (ding on wake word)
- [ ] Enhanced user feedback for skill results

### Tier 2: Expanding (New Capabilities)
- [ ] Weather skill with free API integration
- [ ] Volume/mute system control
- [ ] Lock/sleep/shutdown with confirmation
- [ ] Advanced memory integration

### Tier 3: Advanced (Polish & Distribution)
- [ ] GUI overlay with transcription display
- [ ] Packaged .exe with installer
- [ ] Voice customization/cloning
- [ ] Performance optimization

---

## 📚 Key Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Installation, usage, setup |
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Architecture for new developers |
| [Documentation.md](Documentation.md) | Detailed feature guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history & fixes |
| [TODO.md](TODO.md) | Development roadmap |
| [config.template.yaml](config.template.yaml) | Configuration reference |

---

## 🎯 Development Notes

### Adding a New Skill

1. Create file in `aist/skills/new_skill/`
2. Decorate function with `@aist_skill`
3. Write descriptive docstring (LLM reads this)
4. Create `skill.json` manifest
5. Skill is auto-discovered on next startup

### Debugging Tips

- Check `data/logs/aist.log` for detailed logs
- Use `config.logging.console_enabled: true` for real-time output
- Test individual components independently
- Verify model paths in `config.yaml`

### Performance Optimization

- Increase `gpu_layers` if you have NVIDIA GPU
- Use `whisper_device: "cuda"` for Whisper STT
- Adjust `energy_threshold` for your environment
- Consider smaller LLM model if hardware-constrained

---

## 📞 Contact & Support

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for contribution guidelines.

---

**Analysis Complete** | AIST v2.0 with Vosk Integration
