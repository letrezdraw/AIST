<div align="center">

```
    ___    _____ 
    / _ \  |_   _| 
 / /_\ \   | | 
  |  _  |   | |  
  | | | |  _| |_ 
   \_| |_/ \_____/ 
```

</div>

<h1 align="center">AIST - Autonomous Intelligent System Tasker</h1>

<div align="center">
  <strong>A modular, offline-first, voice-controlled AI assistant framework for Windows.</strong>
</div>

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-in--development-orange.svg)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Model Setup](#model-setup)
- [How to Run](#-how-to-run)
- [Usage Guide](#-usage-guide)
- [Technology Stack](#-technology-stack)
- [Roadmap](#-roadmap)

---

## 🚀 Overview

AIST is a modular, offline-first, voice-controlled AI assistant framework for Windows. It is designed to be a private and extensible platform, running entirely on your local machine. The core components (STT, TTS, LLM) operate without needing an internet connection, ensuring your data stays with you.

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🎙️ **Voice-Activated** | Control the assistant using natural voice commands with a stateful `DORMANT` -> `LISTENING` loop. |
| 🔒 **Offline & Private** | All core components (STT, TTS, LLM) run locally. No data is sent to the cloud. |
| 🧩 **Modular Design** | Easily swap components. The current stack uses Vosk, Piper, and `ctransformers`. |
| 🛠️ **Extensible Skills** | A dynamic skill discovery system is in place, ready for new capabilities to be added. |
| 🧠 **Persistent Memory** | Remembers facts and user preferences using a local SQLite database. |
| 📝 **Robust Logging** | Creates detailed, rotating logs for easy debugging and monitoring. |

## 🏛️ Architecture

AIST operates on a robust **client-server model** to ensure a responsive user experience, even while the AI is performing heavy processing.

1.  **Backend (`run_backend.py`)**: The **"Brain"**. This process loads the large language model (LLM) into memory and handles all AI processing and skill execution. It runs in its own console window.
2.  **Frontend (`main.py`)**: The **"Face"**. This lightweight process manages all user interaction: listening to the microphone, speaking responses, and managing the system tray icon.
3.  **IPC Channel**: The frontend and backend communicate through a fast, local Inter-Process Communication (IPC) channel, preventing the UI from freezing while the AI "thinks".

## ⚙️ Getting Started

Follow these steps to get AIST running on your local machine.

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- Git

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/letrezdraw/AIST
    cd AIST
    ```

2.  **Create and Activate a Virtual Environment**
    It is highly recommended to use a virtual environment to manage dependencies.
    ```powershell
    # Create the virtual environment
    python -m venv venv
    
    # Activate it
    .\venv\Scripts\activate
    
    # If you encounter an error, you may need to adjust your execution policy:
    # Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

3.  **Install Dependencies**
    Install all required Python packages from the `requirements.txt` file.
    ```bash
    # Use this more reliable method to install packages
    python -m pip install -r requirements.txt
    ```
    <details>
    <summary><strong>Optional: NVIDIA GPU Acceleration</strong></summary>
    
    For significantly better performance, you can install the CUDA-enabled version of `ctransformers`. First, ensure you have the NVIDIA CUDA Toolkit installed, then run:
    ```bash
    python -m pip uninstall ctransformers
    python -m pip install ctransformers[cuda]
    ```
    </details>

### Model Setup

AIST requires three different models to function. Download them and place them in the specified folders.

| Model Type | Recommendation | Location |
| :--- | :--- | :--- |
| **LLM (GGUF)** | [`Mistral-7B-Instruct-v0.2.Q4_K_M.gguf`](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf) | Place in the root `AIST` directory. |
| **TTS (Piper)** | `en_US-lessac-medium` | Create a `piper_voices` folder. Place both the `.onnx` and `.json` files inside. |
| **STT (Vosk)** | `vosk-model-en-us-0.22` | Create a `vosk_models` folder. Unzip and place the model's inner folder inside. |

**Important**: After downloading, ensure the `MODEL_PATH`, `PIPER_VOICE_MODEL`, and `VOSK_MODEL_PATH` variables in `config.py` match your downloaded file and folder names exactly.

## ▶️ How to Run

AIST requires two separate console windows to run. The `start_console.bat` script is provided for easy access to a terminal with the virtual environment pre-activated.

1.  **Start the Backend**: Open a console (or run `start_console.bat`), activate the venv, and run:
    ```bash
    python run_backend.py
    ```
    Wait for it to confirm that the AI model has loaded and the IPC server is listening.

2.  **Start the Frontend**: Open a **second** console (or run `start_console.bat` again), activate the venv, and run:
    ```bash
    python main.py
    ```
    The AIST icon will appear in your system tray, and the assistant will be active.

## 🗣️ Usage Guide

The assistant operates in two states. All control phrases can be customized in `config.py`.

- **`DORMANT`**: The assistant passively listens only for an **activation phrase** (e.g., "hey assist").
- **`LISTENING`**: Once activated, the assistant processes any command you give it.

You can return to the `DORMANT` state by saying a **deactivation phrase** (e.g., "assist pause").

To shut down, say an **exit phrase** (e.g., "assist exit"), right-click the system tray icon, or use the `Ctrl+Win+X` hotkey.

## 📦 Technology Stack

| Component | Technology |
| :--- | :--- |
| 🧠 **LLM Engine** | `ctransformers` |
| 👂 **Speech-to-Text** | `vosk` |
| 🗣️ **Text-to-Speech** | `piper-tts` |
| 🎤 **Audio I/O** | `pyaudio` |
| 🖼️ **GUI & Hotkeys** | `pystray`, `keyboard` |
| 💾 **Memory** | `sqlite3` |

## 🗺️ Roadmap

- [ ] **Full Skill Integration**: Wire the `dispatcher` into the backend to enable function calling.
- [ ] **Advanced OS Automation**: Add skills for controlling the mouse and keyboard (`pyautogui`).
- [ ] **API-Driven Skills**: Implement skills for weather, news, and other online services.
- [ ] **GUI Overlay**: Create a small, non-intrusive GUI to display text and status.
- [ ] **Packaged Application**: Bundle the project into a single `.exe` with an installer.

