# AIST Project Overview

This document provides a high-level overview of the AIST project architecture and key components, intended to bootstrap understanding for new developers or assistants.

## 1. Project Purpose

AIST is a modular, offline-first AI assistant for Windows. It features a voice-activated interface, a graphical user interface (GUI), and a skill-based architecture for extensibility.

## 2. High-Level Architecture

The application operates on a multi-process, client-server model. The main `start.py` script acts as a master launcher for three separate, concurrent processes:

1.  **Backend ("The Brain"):** `run_backend.py`
    *   This is the core of the assistant.
    *   It hosts the AI/LLM model, manages the skill system, and handles the main application logic.
    *   It runs an IPC server to listen for commands from clients.

2.  **Frontend ("The Face"):** `main.py`
    *   This process handles all user-facing interactions.
    *   It manages microphone input, performs Speech-to-Text (STT), and handles Text-to-Speech (TTS) output.
    *   It runs as a system tray application and manages global hotkeys.

3.  **GUI (Graphical User Interface):** `gui.py`
    *   A `customtkinter`-based visual client.
    *   It connects to the backend to display logs, show the status of different components (LLM, STT, TTS), and visualize the AI's state.
    *   It allows for sending text-based commands to the backend.

## 3. How to Run the Application

The application should be started from an activated Python virtual environment.

```bash
python start.py
```

This will launch the three components in separate console windows (as per the current configuration for debugging).

## 4. Inter-Process Communication (IPC)

Components communicate via a custom IPC system built with **ZeroMQ (`pyzmq`)**.

*   **Command Channel:** The frontend and GUI send commands to the backend over a `REP/REQ` socket (defaulting to port `5555`).
*   **Event Bus:** The backend broadcasts events (like state changes or initialization status) to all clients over a `PUB/SUB` socket (defaulting to port `5556`). This is used to keep the GUI updated.

## 5. Core Concepts

### Configuration (`config.yaml`)

This is a critical file for configuring the application. Key settings include:
*   **Model Paths:** Paths to the LLM, TTS, and STT models are defined here. **Incorrect paths are a common source of startup errors.** Local model paths should be specified with a relative prefix (e.g., `./model.gguf`) to distinguish them from Hugging Face repository IDs.
*   **Activation Phrases:** Phrases that wake the assistant from its `DORMANT` state.
*   **IPC Ports:** Ports for the communication channels.

### State Machine

The assistant operates on a simple state machine, primarily switching between two states:
*   **`STATE_DORMANT`**: Passively listening only for activation phrases.
*   **`STATE_LISTENING`**: Actively listening for commands and processing them.

These states are defined as constants in `aist/core/ipc/protocol.py`.

### Skills (`aist/skills/`)

The assistant's capabilities are extended through skills.
*   **Discovery:** Skills are located in subdirectories within `aist/skills/`.
*   **Dispatching (`dispatcher.py`):** When a command is received in the `LISTENING` state, the `command_dispatcher` decides how to handle it. It may take a "fast path" for simple commands or use the LLM to determine the user's intent and route to the appropriate skill.
*   **Execution:** Skills are executed in sandboxed sub-processes to prevent a faulty skill from crashing the entire backend.

## 6. Key Files Summary

*   `start.py`: Master launcher. The main entry point to run the application.
*   `config.yaml`: Main configuration file.
*   `run_backend.py`: Entry point for the backend process.
*   `main.py`: Entry point for the frontend (STT/TTS, tray icon) process.
*   `gui.py`: Entry point for the GUI process.
*   `aist/core/ipc/server.py`: Defines the `IPCServer` that runs in the backend.
*   `aist/core/ipc/client.py`: Defines the `IPCClient` used by the frontend and GUI.
*   `aist/core/ipc/protocol.py`: Defines constants for IPC and state management.
*   `aist/core/llm.py`: Handles loading and interacting with the LLM.
*   `aist/skills/dispatcher.py`: Contains the core logic for routing user commands to skills or chat.
