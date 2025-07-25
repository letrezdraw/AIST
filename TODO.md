# AIST Project To-Do List

This file tracks the development progress and future roadmap for the AIST assistant.

## ✅ Completed Milestones

-   **Core Architecture:**
    -   [x] Established a robust client-server model with IPC for a responsive UI.
    -   [x] Created a clean, modular codebase (`core/`, `skills/`).
-   **Voice & Language Stack:**
    -   [x] Upgraded Speech-to-Text to the high-performance **Vosk** engine.
    -   [x] Implemented high-quality, offline Text-to-Speech with **Piper**.
    -   [x] Integrated a local LLM via `ctransformers` with GPU acceleration support.
-   **Application & User Experience:**
    -   [x] Implemented a stateful `DORMANT` <-> `LISTENING` conversational loop.
    -   [x] Deployed as a background process with a system tray icon and global exit hotkey.
    -   [x] Integrated a comprehensive, file-based logging system for easy debugging.
-   **Foundation for Extensibility:**
    -   [x] Built a dynamic skill discovery system (`skill_loader.py`).
    -   [x] Implemented a persistent memory system using SQLite (`core/memory.py`).
    -   [x] Designed a powerful, LLM-based skill dispatcher (`skills/dispatcher.py`).

## 🚀 Next Steps & Roadmap

### Tier 1: Activating Skills (Immediate Priority)
-   [ ] **Wire the Skill Dispatcher:**
    -   [ ] Modify the `IPCServer` in the backend to call the `command_dispatcher`.
    -   [ ] Pass the LLM's skill selection and parameters to the correct skill function.
    -   [ ] Send the skill's string result back to the frontend for TTS.
-   [ ] **Implement Basic System Skills:**
    -   [ ] Re-implement `open_application` using the new `@aist_skill` decorator.
    -   [ ] Re-implement `get_system_info` (CPU, battery) as a skill.
-   [ ] **Enhanced User Feedback:**
    -   [ ] Add audio cues (e.g., a "ding" sound on wake word detection, another for command processing).
    -   [ ] Provide more specific spoken feedback for skill errors.

### Tier 2: Expanding Capabilities
-   [ ] **Weather Skill:**
    -   [ ] Integrate with a free weather API (like OpenWeatherMap) to get and report real-time weather.
-   [ ] **System Control Skills:**
    -   [ ] Adjust system volume.
    -   [ ] Mute/unmute the system.
    -   [ ] Lock, sleep, or shut down the computer (with confirmation).
-   [ ] **Memory Integration:**
    -   [ ] Create skills for the LLM to `add_fact` and `retrieve_relevant_facts` from its own memory.

### Tier 3: Advanced Features
-   [ ] **GUI Overlay:**
    -   [ ] Design a small, non-intrusive GUI to display transcribed text and assistant status.
-   [ ] **Packaged Application:**
    -   [ ] Bundle the entire project into a single `.exe` with an installer using `PyInstaller`.