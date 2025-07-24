# AIST Project Documentation

**Version: 1.0**

This document provides a comprehensive overview of the AI System Toolkit (AIST), a modular, voice-activated AI assistant. It details the project's architecture, features, setup, and future development roadmap.

---

## 1. Project Overview

AIST is a "Jarvis-like" AI assistant designed to run locally on a Windows machine. Its primary goal is to provide a deeply integrated, conversational, and extensible AI companion that respects user privacy by performing all core processing on-device.

The architecture is modular, separating concerns like speech recognition, language understanding, and skill execution into distinct components. This allows for easier maintenance, debugging, and expansion.

---

## 2. How It Works: The Core Loop

AIST operates on a continuous, event-driven loop. Understanding this flow is key to understanding the project.

1.  **Wake Word Detection (`core/stt.py`)**: The system constantly listens for the wake word ("hey assistant") in the background using the microphone. It ignores all other audio until the wake word is detected.

2.  **Command Listening (`core/stt.py`)**: Once activated, AIST listens for a single, specific command from the user. It has a timeout, so if nothing is said, it goes back to sleep (waiting for the wake word).

3.  **Memory Retrieval (`core/memory.py`)**: The user's command is used as a query to search the long-term memory (a ChromaDB vector database). Any relevant facts that AIST has previously learned are retrieved.

4.  **Intent Recognition (`core/llm.py` & `skills/dispatcher.py`)**: The user's command, along with the short-term conversation history and any relevant facts from long-term memory, are sent to the local Large Language Model (LLM). The LLM is prompted to return a structured JSON object identifying the user's intent (e.g., `{"command": "get_time", "parameters": {}}`).

5.  **Skill Dispatching (`skills/dispatcher.py`)**: The dispatcher receives the JSON intent. It uses a dictionary to map the `command` name to the appropriate Python function (the "skill").

6.  **Skill Execution (`skills/*.py`)**: The corresponding skill function is executed (e.g., `skill_get_time()`). The skill performs its task and **returns a string** as a result (e.g., "The current time is 3:45 PM.").

7.  **Response Generation (`main.py` & `core/tts.py`)**: The main loop receives the string response from the skill. It prints the response to the console and uses the Text-to-Speech (TTS) engine to speak the response aloud.

8.  **Context Update (`main.py`)**: The user's command and AIST's response are added to the short-term conversation history.

9.  **Return to Sleep**: The loop completes, and AIST goes back to step 1, waiting for the wake word again.

---

## 3. Features & Capabilities

### What AIST Can Do Now

*   **Voice Activation**: Hands-free activation using a customizable wake word.
*   **Local AI Processing**: All intent recognition and chat functions are handled by a local LLM (`Mistral 7B`), ensuring privacy and offline functionality.
*   **Conversational Context**: Remembers the last few turns of a conversation to understand follow-up questions.
*   **Long-Term Memory (Learning)**:
    *   Can be taught specific facts using the "remember" or "learn" command.
    *   Automatically recalls and uses learned information when relevant.
    *   Can list everything it has learned.
    *   Can be told to forget specific memories.
*   **System Control**:
    *   Open any application on the system (e.g., "open notepad").
    *   Close running applications (e.g., "close notepad").
    *   Report system status like CPU usage and battery level.
*   **Web Search**: Can open the default web browser to perform a Google search.
*   **Background Operation**: Runs as a persistent icon in the system tray.

### Future Roadmap

The following features are planned for future development to enhance AIST's capabilities:

*   **GUI Overlay**: A small, non-intrusive graphical interface to display text, status, and feedback, making the assistant feel more integrated.
*   **Advanced OS Automation**:
    *   Use `pyautogui` to control the mouse and keyboard.
    *   Enable skills like "take a screenshot," "type this for me," or "click the save button."
*   **API-Driven Skills**:
    *   **Weather**: Fetch and report real-time weather from an online API.
    *   **News**: Get the latest headlines.
    *   **Calendar/Email**: Integrate with Google Calendar or Outlook to manage events and read emails.
*   **Enhanced Voice Engine**:
    *   Integrate a higher-quality, more natural-sounding local TTS engine like `Coqui-TTS` or `piper-tts`.
    *   Explore voice cloning to allow AIST to speak with a custom voice.
*   **Multi-modal Input**: Accept text input from a GUI in addition to voice commands.
*   **Packaged Application**: Bundle the entire project into a single `.exe` file with an installer using `PyInstaller` and `Inno Setup` for easy distribution.

---

## 4. Tools & Technologies

AIST is built with a powerful stack of open-source Python libraries.

*   **Core AI**:
    *   `ctransformers`: Runs the quantized GGUF language model efficiently on CPU or GPU.
    *   `chromadb`: The vector database used for long-term memory.
    *   `sentence-transformers`: Creates the vector embeddings (numerical representations) of text for storage and retrieval in ChromaDB.
*   **Voice & Speech**:
    *   `pyttsx3`: The primary Text-to-Speech engine (using Windows SAPI5).
    *   `SpeechRecognition`: The primary Speech-to-Text engine (using the Google Speech Recognition API).
    *   `playsound`: For playing simple audio cues like the activation sound.
*   **System & Application**:
    *   `pystray` & `Pillow`: For creating and managing the system tray icon.
    *   `psutil`: For accessing system information like running processes, CPU, and battery.
*   **General Purpose**:
    *   `os`, `datetime`, `json`, `re`, `uuid`, `threading`: Standard Python libraries for core functionality.

---

## 5. Setup & Usage

1.  **Clone the Repository** and navigate into the project directory.
2.  **Install Dependencies** by running `pip install -r requirements.txt`.
3.  **Download the AI Model** (`mistral-7b-instruct-v0.2.Q4_K_M.gguf` is recommended) and place it in the project's root directory.
4.  **Configure `config.py`** to ensure `MODEL_PATH` matches the downloaded model's filename.
5.  **Run the Assistant** with `python main.py`.

---

## 6. How to Add a New Skill

The project is designed for easy extension. Follow these three steps to add a new capability:

**1. Create the Skill Function:**

*   In a relevant `skills/*.py` file, create a new function. It must accept a `parameters` dictionary and `return` a response string.

    ```python
    # In skills/system.py
    def skill_get_date(parameters):
        today = datetime.date.today().strftime("%B %d, %Y")
        return f"Today's date is {today}."
    ```

**2. Register the Skill:**

*   In `skills/dispatcher.py`, import your new function and add it to the `SKILLS` dictionary.

    ```python
    from skills.system import ..., skill_get_date

    SKILLS = {
        ...,
        "get_date": skill_get_date,
    }
    ```

**3. Teach the LLM:**

*   In `core/llm.py`, find the `get_intent_from_llm` function. Add the new command name (e.g., `"get_date"`) to the list of valid commands in the prompt. This allows the AI to recognize when to use your new skill.

    ```python
    # In the prompt string within get_intent_from_llm
    The "command" can be one of the following: [..., "learn_fact", "get_date", "chat"].
    ```