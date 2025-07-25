# AIST - Autonomous Intelligent System Tasker

AIST is a modular, offline-first, voice-controlled AI assistant framework for Windows. It is designed to be a private and extensible platform, running entirely on your local machine. The core components (STT, TTS, LLM) operate without needing an internet connection, ensuring your data stays with you.

## Features

- **Voice-Activated**: Control the assistant using natural voice commands.
- **Stateful Interaction**: A DORMANT state for passively listening for a wake word, and a LISTENING state for actively processing commands.
- **Fully Offline**: Core functionalities run locally. No data is sent to the cloud.
- **Modular Architecture**: Easily swap components. The current implementation uses Vosk for Speech-to-Text and Piper for Text-to-Speech.
- **Extensible Skills**: Designed to be expanded with new capabilities (e.g., opening applications, web searches).
- **Persistent Memory**: Remembers facts and user preferences using a local SQLite database.

## Architecture

AIST operates on a robust client-server model to ensure a responsive user experience, even while the AI is processing.

- **Backend (`run_backend.py`)**: The "brain" of the assistant. This process loads the large language model (LLM) into memory and handles all the heavy AI processing and skill execution. It runs in its own console window.
- **Frontend (`main.py`)**: The "face" of the assistant. This lightweight process manages all user interaction: listening to the microphone (STT), speaking through your speakers (TTS), and managing the system tray icon.
- **IPC Communication**: The frontend and backend communicate through a fast, local Inter-Process Communication (IPC) channel, allowing them to work together seamlessly.

## Setup and Installation

Follow these steps to get AIST running on your machine.

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- Git

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd AIST
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate
```

### 3. Install Dependencies

Install all the required Python packages from the `requirements.txt` file.

```bash
# Use this more reliable method to install packages
python -m pip install -r requirements.txt
```

**Note on `ctransformers`**: The `requirements.txt` file installs the base version. For significantly better performance with an NVIDIA GPU, you can install the CUDA-enabled version. First, ensure you have the NVIDIA CUDA Toolkit installed, then run:
```bash
python -m pip uninstall ctransformers
python -m pip install ctransformers[cuda]
```

### 4. Download Models

AIST requires three different models to function. Download them and place them in the specified folders.

**A. Large Language Model (LLM)**
- **Format**: GGUF
- **Recommendation**: Download a model like `Mistral-7B-Instruct-v0.2.Q4_K_M.gguf`. You can find many options on Hugging Face.
- **Location**: Place the `.gguf` file in the root `AIST` directory.
- **Configuration**: Update the `MODEL_PATH` in `config.py` to match the exact filename of your downloaded model.

**B. Text-to-Speech Model (TTS)**
- **Source**: Piper Voices
- **Recommendation**: `en_US-lessac-medium.onnx` is a good starting point.
- **Location**: Create a `piper_voices` folder. Place both the `.onnx` file and its corresponding `.json` config file inside.
- **Configuration**: Ensure `PIPER_VOICE_MODEL` in `config.py` points to the `.onnx` file.

**C. Speech-to-Text Model (STT)**
- **Source**: Vosk Models
- **Recommendation**: Download `vosk-model-small-en-us-0.15`.
- **Location**: Create a `vosk_models` folder. Unzip the download and place the model folder (e.g., `vosk-model-small-en-us-0.15`) inside `vosk_models`.
- **Configuration**: Ensure `VOSK_MODEL_PATH` in `config.py` points to this inner folder.

## How to Run AIST

AIST requires two separate console windows to run.

1.  **Start the Backend**: Open a console, activate the virtual environment, and run:
    ```bash
    python run_backend.py
    ```
    Wait for it to confirm that the AI model has loaded.

2.  **Start the Frontend**: Open a **second** console, activate the virtual environment, and run:
    ```bash
    python main.py
    ```
    The AIST icon will appear in your system tray, and the assistant will be active.

## Usage

The assistant operates in two states:

- **DORMANT**: The assistant is passively listening for an activation phrase (e.g., "hey assist"). It will not process any other commands.
- **LISTENING**: Once activated, the assistant will process any command you give it. You can give multiple commands in a row.

**Control Phrases (customizable in `config.py`):**
- **Activation**: "hey assist", "assist start", etc.
- **Deactivation**: "assist pause" (returns the assistant to the DORMANT state).
- **Exit**: "assist exit" (shuts down the application).

You can also quit the application by right-clicking the system tray icon or using the `Ctrl+Win+X` hotkey.

## Technology Stack

- **LLM Engine**: `ctransformers`
- **Speech-to-Text**: `vosk`
- **Text-to-Speech**: `piper-tts`
- **Audio I/O**: `pyaudio`
- **GUI / Hotkeys**: `pystray`, `keyboard`