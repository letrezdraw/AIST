# AIST Project To-Do List

This file tracks the development progress of the AIST assistant.

## ✅ Already Done

-   [x] **Core Conversational Loop:** Established the fundamental Listen -> Think -> Speak cycle.
-   [x] **Local LLM Integration:** Running `mistral-7b-instruct` locally via `ctransformers`.
-   [x] **Voice I/O:** Implemented Text-to-Speech (`pyttsx3`) and Speech-to-Text (`speech_recognition`).
-   [x] **Wake Word Activation:** Assistant runs in the background and activates on "hey assistant".
-   [x] **Modular Codebase:** Refactored the project into a clean structure (`core/`, `skills/`).
-   [x] **GPU Acceleration:** Enabled GPU offloading for the LLM for faster responses.
-   [x] **Background Process:** Application runs silently with a system tray icon (`pystray`).
-   [x] **Basic Skill Dispatcher:** Created a dispatcher using regular expressions to route commands.
-   [x] **Initial Skill Set:**
    -   `skill_open_application`: Open applications like Notepad.
    -   `skill_search_web`: Search Google for a query.
    -   `skill_get_time`: Report the current time.
    -   `skill_get_system_info`: Report CPU and Battery status using `psutil`.

## 🚀 To-Do in Future

### Tier 1: Core Improvements
-   [ ] **LLM-based Intent Recognition:**
    -   [ ] Design a prompt that makes the LLM return structured JSON (`{'command': '...', 'parameters': {...}}`).
    -   [ ] Rework the `command_dispatcher` to parse this JSON instead of using regex. This will make it much smarter and more flexible.
-   [ ] **Enhanced User Feedback:**
    -   [ ] Add audio cues (e.g., a "ding" sound on wake word detection, another for command processing).
    -   [ ] Provide more specific spoken feedback for errors (e.g., "I couldn't find an application named Notepad").
-   [ ] **Robust `open_application` Skill:**
    -   [ ] Improve the skill to search for common application paths (e.g., in Program Files) if the `start` command fails.

### Tier 2: New Skills
-   [ ] **Weather Skill:**
    -   [ ] Integrate with a free weather API (like OpenWeatherMap) to get and report real-time weather.
-   [ ] **System Control Skills:**
    -   [ ] Adjust system volume.
    -   [ ] Mute/unmute the system.
    -   [ ] Lock, sleep, or shut down the computer (with confirmation).

### Tier 3: Advanced Features
-   [ ] **Logging:**
    -   [ ] Implement a logging system to write errors and key events to a file for easier debugging.