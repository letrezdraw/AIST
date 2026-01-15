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

<h1 align="center">AIST - Autonomous Intelligent System</h1>

<div align="center">
  <strong>A modular, offline-first, voice-controlled AI assistant framework for Windows.</strong>
</div>

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)
![Status](https://img.shields.io/badge/status-in--development-orange.svg)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

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
| 🧠 **AI-Driven Intent** | Uses a local LLM to understand user intent, not just keywords. |
| 🔒 **Offline & Private** | All core components (STT, TTS, LLM) run locally. No data is sent to the cloud. |
| 🎙️ **Stateful Voice Activation** | Hands-free activation and control with a `DORMANT` <-> `LISTENING` state machine. |
| 🧩 **Pluggable STT** | Choose your Speech-to-Text engine. Defaults to the lightweight `Vosk` and supports the high-accuracy `Whisper` AI. |
| 🛠️ **Foundation for Skills** | A dynamic skill discovery system is in place, ready for new capabilities to be added. |
| 💾 **Persistent Memory** | Remembers facts and user preferences using a local SQLite database. |
| 🖥️ **Clean Console UI** | Provides clear, color-coded status updates in the console for monitoring, while keeping low-level logs in a separate file. |

## 🏛️ Architecture

AIST operates on a robust **client-server model** to ensure a responsive user experience, even while the AI is performing heavy processing.

1.  **Backend (`run_backend.py`)**: The **"Brain"**. This process loads the large language model (LLM) into memory and handles all AI processing and skill execution. It runs in its own console window.
2.  **Frontend (`main.py`)**: The **"Face"**. This lightweight process manages all user interaction: listening to the microphone, speaking responses, and managing the system tray icon.
3.  **IPC Channel**: The frontend and backend communicate through a fast, local Inter-Process Communication (IPC) channel, preventing the UI from freezing while the AI "thinks".
4.  **Event Bus**: Internally, the frontend components (STT, TTS, UI) are decoupled and communicate via a `PyPubSub` message bus, making the system robust and extensible.

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
    <summary><strong>Optional: NVIDIA GPU Acceleration (Highly Recommended)</strong></summary>
    
    For a massive performance boost with both the LLM and the Whisper STT provider, you can install CUDA-enabled libraries.
    
    1.  **Ensure you have the NVIDIA CUDA Toolkit installed.**
    2.  **Install CUDA-enabled PyTorch:** Go to the PyTorch website and generate the correct `pip` command for your system's CUDA version.
    3.  **Install CUDA-enabled ctransformers:**
    ```bash
    python -m pip uninstall ctransformers
    python -m pip install ctransformers[cuda]
    ```
    After installation, remember to set `gpu_layers` for the LLM and `whisper_device: "cuda"` in your `config.yaml`.
    </details>

### Model Setup

AIST uses local models for its core functionality. The STT models are handled differently depending on the provider you choose in your configuration.

| Model Type | Recommendation | Location |
| :--- | :--- | :--- |
| **LLM (GGUF)** | `Mistral-7B-Instruct-v0.2.Q4_K_M.gguf` | `data/models/llm/` |
| **TTS (Piper)** | `en_US-lessac-medium` | `data/models/tts/` (Place both `.onnx` and `.json` files here) |
| **STT (Vosk)** | `vosk-model-en-us-0.22` | `data/models/stt/` (Place the model's inner folder here). **Required only if using the `vosk` provider.** |
| **STT (Whisper)**| *N/A* | The Whisper provider will automatically download the selected model on its first run. |

4.  **Configure AIST**
    AIST now uses a `config.yaml` file for all settings.
    ```bash
    # Copy the template to create your own configuration file
    copy config.template.yaml config.yaml
    ```
    Open `config.yaml` in a text editor. Verify the model paths and choose your desired STT provider (`vosk` or `whisper`). You can also customize hotkeys, activation phrases, and more.

## ▶️ How to Run

Starting AIST is simple. Just double-click the `start_aist.bat` file in the project's root directory.

This will open a main "Launcher" console window, which will then automatically:
1.  Activate the Python virtual environment.
2.  Launch the Backend, Frontend, and GUI, each in its own separate console window.

To shut down the application, use the system tray icon or the global hotkey (`Ctrl+Win+X`).

<details>
<summary><strong>Running Manually (for Development)</strong></summary>

If you prefer to run the components manually for debugging:

1.  Open three separate consoles (e.g., by running `start_console.bat` multiple times).
2.  In each console, activate the virtual environment: `.\venv\Scripts\activate`
3.  In the respective consoles, run `python run_backend.py`, `python main.py`, and `python run_gui.py`.
</details>

## 🗣️ Usage Guide

The assistant operates in two states, with the backend deciding when to switch based on your speech.

- **`DORMANT`**: The assistant is passively listening. It will only respond if it understands you are trying to activate it (e.g., by saying "hey assist").
- **`LISTENING`**: Once activated, the assistant processes any command you give it.

You can return to the `DORMANT` state by saying a **deactivation phrase** (e.g., "assist pause").

To shut down, say an **exit phrase** (e.g., "assist exit"), right-click the system tray icon, or use the global hotkey (default: `Ctrl+Win+X`).

## 📦 Technology Stack

| Component | Technology |
| :--- | :--- |
| 🧠 **LLM Engine** | `ctransformers` |
| 👂 **Speech-to-Text** | `Vosk` (lightweight) or `Whisper` (high-accuracy) |
| 🗣️ **Text-to-Speech** | `piper-tts` |
| 🎤 **Audio I/O** | `pyaudio` |
| 🖼️ **GUI & Hotkeys** | `pystray`, `keyboard` |
| 💾 **Memory** | `sqlite3` |

## 🗺️ Roadmap

The project has a detailed, phased development plan focused on creating a best-in-class AI assistant framework. Key goals include implementing a message bus architecture for scalability, building a powerful and secure skill ecosystem, and polishing the user experience with a GUI and pluggable AI providers.

For a complete vision and breakdown of upcoming epics, see the full Project Roadmap.
