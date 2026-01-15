# AIST Changelog

## August 14, 2025 Update

This update addresses several issues and introduces new features related to application initialization and inter-process communication.

### What's New & Working:

*   **GUI Initialization Status:** The GUI now receives and displays real-time initialization status for the LLM, TTS, STT, and Skills components. This provides better visibility into the backend's startup process.
    *   Status updates include component name, initialization status (initialized/failed), and relevant details like provider or error messages.
*   **Modular Initialization Status Broadcasting:** Backend components (LLM, TTS, STT, Skills) now broadcast their initialization status via a dedicated event bus, allowing the GUI to subscribe and update its display.
*   **IPC Protocol Definition:** A new `aist/core/ipc/protocol.py` file has been introduced to centralize IPC message type definitions, improving code clarity and maintainability.

### Fixed Issues:

*   **Frontend `Address in use` Error (Port 5556):** The Frontend (`main.py`) no longer attempts to bind to the event bus port (5556), resolving the `zmq.error.ZMQError: Address in use` conflict with the Backend. The Frontend now correctly subscribes to events.
*   **Skill Crashing in Sandboxed Processes:** The issue causing skills (e.g., `time_skill`, `memory_skill`) to crash with `OSError: [Errno 22] Invalid argument` has been addressed. Console logging is now disabled for child processes on Windows, preventing conflicts with standard output streams.
*   **Hardcoded Whisper Model Name:** The `aist/stt_providers/whisper_provider.py` file no longer hardcodes the Whisper model name to "tiny.en". It now correctly reads the `whisper_model_name` from `config.yaml`.

### Known Issues / Not Working (Requires Further Investigation):

*   **Whisper STT Model Loading Error:** While the hardcoded model name issue was fixed, the `OSError: [Errno 22] Invalid argument` during Whisper STT model loading might still persist if the underlying problem is related to corrupted model files, download paths, or system permissions. This requires further testing and potential manual intervention (e.g., clearing Whisper cache, checking permissions).
*   **Frontend `initialize_tts_engine()` TypeError:** The `main.py` (Frontend) is still attempting to call `initialize_tts_engine()` without the `event_broadcaster` argument, leading to a `TypeError`. This needs to be resolved by either:
    *   Creating separate initialization functions for the Frontend that do not require the `event_broadcaster`.
    *   Modifying the existing `initialize_tts_engine` (and `initialize_stt_engine`) to handle being called without the `event_broadcaster` (e.g., by providing a default `None` or a dummy broadcaster).
    *   The current approach of passing `event_broadcaster` to `initialize_llm`, `initialize_tts_engine`, `initialize_stt_engine`, and `SkillManager`'s `__init__` is intended for the Backend only. The Frontend should not be calling these functions in a way that expects an `event_broadcaster` to be passed.

---
**Note:** This changelog reflects the changes made and observed during the recent debugging and feature implementation process.
