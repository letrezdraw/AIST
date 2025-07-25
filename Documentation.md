# AIST Project Documentation

**Version: 2.0 (Vosk Integration)**

This document provides a comprehensive overview of the Autonomous Intelligent System Tasker (AIST), a modular, voice-activated AI assistant. It details the project's architecture, features, setup, and future development roadmap.

---

## 1. Project Overview

AIST is a "Jarvis-like" AI assistant designed to run locally on a Windows machine. Its primary goal is to provide a deeply integrated, conversational, and extensible AI companion that respects user privacy by performing all core processing on-device. The core components (Speech-to-Text, Text-to-Speech, and the Large Language Model) operate without needing an internet connection.

The architecture is modular, separating concerns like speech recognition, language understanding, and skill execution into distinct components. This allows for easier maintenance, debugging, and future expansion.

---

## 2. Architecture: A Client-Server Model

AIST operates on a robust client-server model to ensure a responsive user experience, even while the AI is processing a complex request.

- **Backend (`run_backend.py`)**: The "brain" of the assistant. This process loads the large language model (LLM) into memory and handles all the heavy AI processing and skill execution. It runs in its own console window and waits for commands.

- **Frontend (`main.py`)**: The "face" of the assistant. This lightweight process manages all user interaction: listening to the microphone (STT), speaking through your speakers (TTS), and managing the system tray icon.

- **IPC Communication**: The frontend and backend are separate processes and communicate through a fast, local Inter-Process Communication (IPC) channel. This allows the frontend to remain responsive while the backend "thinks".

---

## 2. How It Works: The Core Loop

AIST operates on a continuous, state-driven loop within the frontend (`main.py`). Understanding this flow is key to understanding the project.

1.  **DORMANT State (`main.py`)**: The assistant starts in a `DORMANT` state. In this mode, the `listen_generator` from `core/stt.py` is active, but the main loop only checks the transcribed text for an **activation phrase** (e.g., "hey assist"). All other speech is ignored.

2.  **Activation**: When an activation phrase is detected, the state machine switches to `LISTENING`. The assistant speaks an acknowledgment ("I'm listening.") and is now ready for commands.

3.  **LISTENING State (`main.py`)**: In this state, the `listen_generator` continues to provide transcribed text. The main loop now checks the text for three possibilities in order:
    a. **Exit Phrase**: Checks for a phrase like "assist exit" to shut down the application.
    b. **Deactivation Phrase**: Checks for a phrase like "assist pause" to return to the `DORMANT` state.
    c. **Command**: If neither of the above is found, the text is treated as a command.

4.  **Command Processing (IPC)**: The command string is sent from the frontend to the backend via the IPC channel.

5.  **LLM Inference (`core/llm.py` on backend)**: The backend receives the command, retrieves any relevant facts from memory, and sends the complete prompt to the Large Language Model for processing.

6.  **Response Communication (IPC)**: The LLM's text response is sent from the backend back to the frontend.

7.  **Speaking the Response (`core/tts.py` on frontend)**: The frontend receives the response text and uses the Text-to-Speech engine to speak it aloud. The loop continues in the `LISTENING` state, ready for the next command.

---

## 3. Features & Capabilities

### Current Features

*   **Stateful Voice Activation**: Hands-free activation using customizable phrases. The assistant remains active for multiple commands until explicitly paused.
*   **Offline-First Core**: The STT (Vosk), TTS (Piper), and LLM (`ctransformers`) all run locally, ensuring privacy and offline functionality.
*   **Conversational AI**: Engages in natural conversation using a local Large Language Model.
*   **Persistent Memory**: Uses a local SQLite database (`core/memory.py`) to store and recall user-specific facts and preferences (e.g., microphone calibration settings).
*   **Background Operation**: Runs as a persistent icon in the system tray.
*   **Robust Logging**: Creates a detailed, rotating log file (`AIST_data/aist.log`) for easy debugging.

### Future Roadmap

The following features are planned for future development to enhance AIST's capabilities:

*   **Skill System**: The highest priority is to build a skill dispatcher that allows the LLM to execute Python functions. This will enable capabilities like:
    *   Opening/closing applications.
    *   Reporting system status (CPU, battery).
    *   Performing web searches.
*   **GUI Overlay**: A small, non-intrusive graphical interface to display text, status, and feedback, making the assistant feel more integrated.
*   **Advanced OS Automation**:
    *   Use `pyautogui` to control the mouse and keyboard.
    *   Enable skills like "take a screenshot," "type this for me," or "click the save button."
*   **API-Driven Skills**:
    *   Fetch and report real-time weather, news, or other online information.
*   **Enhanced Voice Engine**:
    *   Integrate a higher-quality, more natural-sounding local TTS engine like `Coqui-TTS`.
    *   Explore voice cloning to allow AIST to speak with a custom voice.
*   **Packaged Application**: Bundle the entire project into a single `.exe` file with an installer using `PyInstaller` and `Inno Setup` for easy distribution.

---

## 4. Tools & Technologies

- **LLM Engine**: `ctransformers`
- **Speech-to-Text**: `vosk`
- **Text-to-Speech**: `piper-tts`
- **Audio I/O**: `pyaudio`
- **GUI / Hotkeys**: `pystray`, `keyboard`
- **Database**: `sqlite3` (built-in)

---

## 5. Setup & Usage

Please refer to the `README.md` file for detailed, step-by-step installation and setup instructions.

---

## 6. How to Add a New Skill

While a full skill system is not yet implemented, the architecture is designed for it. Here is the planned approach for adding new skills:

**1. Create the Skill Function:**

*   Create a new file in the `skills/` directory (e.g., `system_skills.py`).
*   Define a simple Python function that performs the desired action and returns a string result.

    ```python
    # In skills/system_skills.py
    def open_application(app_name: str) -> str:
        try:
            os.startfile(app_name)
            return f"Successfully opened {app_name}."
        except Exception as e:
            return f"Sorry, I could not open {app_name}. Error: {e}"
    ```

**2. Create a Skill Dispatcher:**

*   A new file, `skills/dispatcher.py`, will be created.
*   This file will contain a dictionary mapping skill names to their functions and descriptions. This information will be used to generate a prompt for the LLM.

**3. Teach the LLM to Recognize the Skill:**

*   The backend's `IPCServer` will be modified. When it receives a command, it will first ask the LLM to perform "function calling" or "tool selection."
*   It will provide the LLM with the list of available skills and their descriptions from the dispatcher.
*   The LLM will respond with a structured format (like JSON) indicating which skill to use and what parameters to pass (e.g., `{"skill": "open_application", "parameters": {"app_name": "notepad"}}`).
*   The backend will then execute the chosen function and return the result to the user.