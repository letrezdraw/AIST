# AIST Status Update - 2025-08-14

This document summarizes the recent changes, fixes, and current status of the AIST project.

## Fixes

- **`ZMQError: Address in use`**: Resolved the issue where multiple components (frontend and backend) were trying to bind to the same ZeroMQ port (5556). The architecture has been clarified:
    - The **backend (`run_backend.py`)** is now the sole owner of the `EventBroadcaster`, which publishes events.
    - The **frontend (`main.py`)** and **GUI (`gui.py`)** now use clients or subscribers to connect to the backend's event bus, rather than creating their own broadcasters.

- **`TypeError: strings only, not <class 'bytes'>`**: Fixed a bug in the GUI's log listener (`aist/gui/main_window.py`) where a subscription topic was being incorrectly encoded to bytes before being passed to `setsockopt_string`.

- **`TypeError: missing 1 required positional argument: 'event_broadcaster'`**: Corrected function calls in `main.py` to `initialize_tts_engine` and `initialize_stt_engine` to pass the required `event_broadcaster` argument.

- **`AttributeError: 'NoneType' object has no attribute 'intents'`**: Resolved a critical error in the skill dispatcher (`aist/skills/dispatcher.py`). The `skill_manager` was not being initialized before the IPC server started accepting commands.
    - `run_backend.py` now calls `initialize_skill_manager` at startup to ensure all skills and their intents are loaded before any commands are processed.

- **`Exception: Failed to process waveform`**: Added a defensive check in the VOSK STT provider (`aist/stt_providers/vosk_provider.py`) to prevent crashes when the audio stream provides empty data.

## What's New & Working

- **Headless Component Launch**: The `start.py` script has been updated to launch the backend and frontend components in the background (without console windows) on Windows, reducing screen clutter. The main launcher window still provides control over the entire application.
- **Robust Initialization**: The fixes above should lead to a more stable and reliable startup sequence. The GUI will now correctly receive and display initialization status updates from the backend components.

## What's Not Working / In Progress

- **GUI Enhancements**: The core request to overhaul the GUI is the next major task. The current GUI is functional for displaying initialization status but needs to be updated to include:
    - A transition from the "Initializing..." view to the main "AI Interaction" view.
    - LED status indicators for components (LLM, TTS, STT, Skills).
    - An indicator for the AI's current state (e.g., DORMANT, LISTENING).
    - A text input for sending commands to the AI.
    - A closing animation.

## Next Steps

1.  **Implement the new GUI design** as per the user's detailed request.
2.  **Thoroughly test** the application to ensure all the recent fixes work together as expected.
3.  **Continue to monitor logs** for any new or recurring issues.
