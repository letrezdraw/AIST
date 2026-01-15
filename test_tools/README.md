# AIST Test Tools

Testing utilities for AIST conversation, STT, LLM, and TTS components.

## Files

### 1. `backend_stt.py` - Backend Server
Handles LLM inference, TTS, and optional voice input.
- Listens on IPC ports (15555/15556)
- Logs to `data/logs/test_backend.log`
- **Text-only mode (fast startup):**
  ```powershell
  python test_tools/backend_stt.py
  ```
- **Voice mode (with STT/microphone):**
  ```powershell
  python test_tools/backend_stt.py --voice
  ```

### 2. `frontend.py` - Frontend Console UI
Clean console interface for testing conversation.
- Sends text input to backend
- Displays responses in formatted output
- Shows configuration settings
- **Usage:**
  ```powershell
  python test_tools/frontend.py
  ```

### 3. `conversation.py` - Standalone Conversation Tester
Single-process conversation tester (no backend).
- Good for quick testing without IPC setup
- All components in one process
- **Text mode:**
  ```powershell
  python test_tools/conversation.py
  ```
- **Voice mode:**
  ```powershell
  python test_tools/conversation.py --voice
  ```

## Usage Scenarios

### Scenario 1: Text-Only Quick Test
Best for: Testing LLM responses, tuning settings
```powershell
# Terminal 1
python test_tools/backend_stt.py

# Terminal 2
python test_tools/frontend.py

# Type messages and see responses
```

### Scenario 2: Full Voice Test
Best for: Testing STT accuracy, energy thresholds, TTS
```powershell
# Terminal 1 - with voice support
python test_tools/backend_stt.py --voice

# Terminal 2
python test_tools/frontend.py

# Speak into microphone when prompted
```

### Scenario 3: Standalone Testing
Best for: Quick testing without setting up two terminals
```powershell
python test_tools/conversation.py
```

## Logging

### Backend Logs
- **File:** `data/logs/test_backend.log` (10MB rotating)
- **Console:** INFO level
- **File:** DEBUG level (detailed)

### View Logs in Real-time
```powershell
Get-Content data/logs/test_backend.log -Wait
```

Or in VS Code:
- Open `data/logs/test_backend.log`
- Auto-refreshes as new logs appear

## Configuration

All settings read from `config.yaml`:
- STT Model: `models.stt.whisper_model_name` (tiny.en, base.en, medium.en, etc.)
- Energy Threshold: `audio.stt.energy_threshold` (adjust for microphone sensitivity)
- TTS Provider: `models.tts.provider` (piper)
- LLM: `models.llm.path`

**To change settings:**
1. Edit `config.yaml`
2. Restart the backend
3. Frontend reconnects automatically

## Commands

### In Frontend
- `help` - Show available commands
- `settings` - Display current configuration
- `clear` - Clear screen
- `exit` - Quit application

### In Conversation Tester
- `help` - Show available commands
- `settings` - Display current configuration
- `history` - Show conversation history
- `exit` - Quit application

## Troubleshooting

### Backend won't start
- Check if ports 15555/15556 are free
- Run: `netstat -ano | findstr :15555`
- Kill processes using those ports if needed

### Frontend can't connect
- Make sure backend started first
- Wait 1-2 seconds before starting frontend
- Check firewall settings

### No STT input detected
- Increase `energy_threshold` in config.yaml (try 800-1000)
- Check microphone is plugged in and working
- Use `--voice` flag when starting backend

### TTS not speaking
- Check `models.tts.provider` is set to "piper" in config.yaml
- Verify speakers are connected and volume is on
- Check backend logs for TTS errors

### Slow LLM responses
- Check `gpu_layers` in config.yaml (0 = CPU, 50+ = GPU)
- Reduce `models.llm.max_new_tokens` if too verbose
- Check if other processes are using CPU/GPU

## Log Levels

Backend logs to file with DEBUG level:
- `[DEBUG]` - Detailed internal operations
- `[INFO]` - Important events and status
- `[WARNING]` - Non-critical issues
- `[ERROR]` - Failures (non-fatal)
- `[CRITICAL]` - Fatal errors

## Tips

1. **Start with text mode first** - Faster startup for initial testing
2. **Check logs often** - `data/logs/test_backend.log` shows what's happening
3. **Adjust energy threshold gradually** - Start at 700, increase by 100 if needed
4. **Use smaller LLM models** - `tiny.en` or `base.en` for faster responses
5. **Monitor GPU usage** - If hanging, reduce GPU layers or use CPU mode

## Architecture

```
Frontend (UI)          Backend (Processing)
   ↓                         ↓
IPC Port 15555 ← Text Input ← 
                → Responses →IPC Port 15556
                     ↓
              LLM ← Config
              TTS ← Config
              STT ← Config (optional)
```

- Frontend: Sends text input, displays responses
- Backend: Processes via LLM, outputs via TTS
- IPC: ZeroMQ for decoupled communication
- Config: YAML for live settings changes


