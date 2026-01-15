# AIST Project Documentation

**Version: 2.0 (Vosk Integration)**

This document provides a comprehensive, in-depth overview of the Autonomous Intelligent System (AIST). It details the project's architecture, core logic, features, and future development roadmap.

---

## 1. 🚀 Project Overview

AIST is a sophisticated AI assistant designed to run locally on a Windows machine. Its primary goal is to provide a deeply integrated, conversational, and extensible AI companion that respects user privacy by performing all core processing on-device. The core components (Speech-to-Text, Text-to-Speech, and the Large Language Model) operate without needing an internet connection.

The architecture is modular, separating concerns like speech recognition, language understanding, and skill execution into distinct components. This allows for easier maintenance, debugging, and future expansion.

---

## 2. 🏛️ Architecture: A Client-Server Model

AIST operates on a robust client-server model to ensure a responsive user experience, even while the AI is processing a complex request.

-   **Backend (`run_backend.py`)**: The **"Brain"** of the assistant. This process loads the large language model (LLM) into memory and handles all the heavy AI processing and skill execution. It runs in its own console window and waits for commands.

-   **Frontend (`main.py`)**: The **"Face"** of the assistant. This lightweight process manages all user interaction: listening to the microphone (STT), speaking through your speakers (TTS), and managing the system tray icon.

-   **IPC Communication**: The frontend and backend are separate processes and communicate through a fast, local Inter-Process Communication (IPC) channel. This allows the frontend to remain responsive while the backend "thinks".

---

## 3. ⚙️ How It Works: The AI-Driven Core Loop

AIST's core logic is driven by the LLM in the backend, which performs **intent recognition**. The frontend is a "dumb client" that simply follows the backend's instructions.

1.  **Listening**: The frontend (`main.py`) continuously listens for speech. When the user pauses, the transcribed text is captured.

2.  **Request to Backend (IPC)**: The frontend sends a JSON request to the backend (`run_backend.py`) containing the transcribed text and the assistant's current state (e.g., `DORMANT` or `LISTENING`).

3.  **Intent Recognition (LLM)**: The backend's `command_dispatcher` receives the request. It constructs a detailed prompt for the LLM, asking it to analyze the user's text *in the context of the current state*. The LLM decides the user's intent (e.g., `activate`, `deactivate`, `get_current_time`, `chat`).

4.  **Skill Execution**: Based on the LLM's decision, the dispatcher either executes a specific skill, generates a chat response, or identifies a state-change command.

5.  **Response to Frontend (IPC)**: The backend sends a JSON response back to the frontend. This response contains two key pieces of information:
    -   `action`: A command for the frontend (e.g., `ACTIVATE`, `DEACTIVATE`, `EXIT`, `COMMAND`).
    -   `speak`: The exact text the assistant should say.

6.  **Action and Speech**: The frontend receives the JSON response. It speaks the provided text and changes its internal state if instructed to by the `action` command. The loop then repeats, waiting for the next user input.


---

## 4. ✨ Features & Capabilities

### Current Features

| Feature | Description |
| :--- | :--- |
| 🧠 **AI-Driven Intent** | Uses a local LLM to understand the user's intent, not just keywords. |
| 🔒 **Offline-First Core** | The STT (Vosk), TTS (Piper), and LLM (`ctransformers`) all run locally, ensuring privacy and offline functionality. |
| 🎙️ **Stateful Voice Activation** | Hands-free activation and control with a `DORMANT` <-> `LISTENING` conversational loop. |
| 💬 **Conversational AI** | Engages in natural conversation using a local Large Language Model. |
| 💾 **Persistent Memory** | Uses a local SQLite database (`aist/core/memory.py`) to store and recall user-specific facts and preferences. |
| 🖥️ **Background Operation** | Runs as a persistent icon in the system tray with a global exit hotkey. |
| 📝 **Robust Logging** | Creates a detailed, rotating log file (`data/logs/aist.log`) for easy debugging. |

### Future Roadmap

The following features are planned for future development to enhance AIST's capabilities:

*   [ ] **Full Skill Integration**: The highest priority is to build a skill dispatcher that allows the LLM to execute Python functions. This will enable capabilities like:
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

## 5. 📦 Tools & Technologies

| Component | Technology |
| :--- | :--- |
| 🧠 **LLM Engine** | `ctransformers` |
| 👂 **Speech-to-Text** | `vosk` |
| 🗣️ **Text-to-Speech** | `piper-tts` |
| 🎤 **Audio I/O** | `pyaudio` |
| 🖼️ **GUI & Hotkeys** | `pystray`, `keyboard` |
| 💾 **Database** | `sqlite3` (built-in) |

---

## 6. 🛠️ Setup & Usage

Please refer to the `README.md` file for detailed, step-by-step installation and setup instructions.

---

## 7. 🧩 How to Add New Skills

The foundation for a powerful skill system is already in place. The `aist/skills/dispatcher.py` uses the LLM to select an action, and the `aist/skills/skill_loader.py` can already discover skills. Here is how you would add and use a new skill within the current architecture:

**1. Create the Skill File:**

*   Create a new Python file in the `aist/skills/` directory (e.g., `system.py`).
*   Import the `@aist_skill` decorator and apply it to your function. The function's docstring is crucial, as it's what the LLM uses to understand the skill's purpose.

    ```python
    # In aist/skills/system.py
    import os
    from .skill_loader import aist_skill

    @aist_skill
    def open_application(app_name: str) -> str:
        """Opens a specified application by its name or path."""
        try:
            os.startfile(app_name)
            return f"Successfully opened {app_name}."
        except Exception as e:
            return f"Sorry, I could not open {app_name}. Error: {e}"
    ```

**2. Automatic Discovery:**

*   The `skill_loader.py` automatically finds any function decorated with `@aist_skill` when the application starts.
*   It builds a list of available tools and their descriptions (from the docstrings) and provides this to the `dispatcher.py`.

**3. LLM-Powered Execution:**

*   When you give a command like "assist, open notepad for me", the `dispatcher` sends your command and the list of available skills to the LLM.
*   The LLM, understanding the context, will respond with a JSON object like: `{"skill": "open_application", "parameters": {"app_name": "notepad.exe"}}`.
*   The dispatcher then parses this JSON, finds the `open_application` function in its list of `AVAILABLE_SKILLS`, and executes it with the provided parameters. The string returned by the skill is then sent to the frontend to be spoken.
