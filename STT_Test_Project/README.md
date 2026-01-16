# Real-time Speech-to-Text Transcription Application

This is a desktop application that provides real-time speech-to-text transcription using OpenAI's Whisper model. It features a simple graphical user interface (GUI) for controlling the transcription process and viewing the output.

**Note:** This project is currently under development. The core functionality is in place, but we are actively working on improving its robustness, particularly in noisy environments.

## Features

*   **Real-time Transcription**: Captures audio from the microphone and transcribes it in near real-time.
*   **Whisper Integration**: Uses the powerful Whisper model for accurate transcriptions.
*   **Configurable**: Many aspects of the application can be configured through a `config.json` file.
*   **GUI Interface**: A simple and easy-to-use interface for starting/stopping the transcription and viewing the results.
*   **Logging**: Logs all important events and errors to an `app.log` file for easy debugging.

## Current Status and Known Issues

The application is functional, but can be overly sensitive to background noise, which can lead to incorrect transcriptions. We are currently working on a noise cancellation feature to address this. For more details on our current work, see [what_we_are_doing.md](what_we_are_doing.md).

## Setup and Usage

### Prerequisites

*   Python 3.10 or higher.
*   `ffmpeg` must be installed and available in the system's PATH, or placed in the project's root directory. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).

### Installation

1.  **Clone the repository or download the source code.**

2.  **Create a Python virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Ensure your microphone is connected and working.**

2.  **Run the application:**
    ```bash
    python app.py
    ```

3.  The first time you run the application, it will create a `config.json` file with default settings. You can edit this file to customize the application's behavior. See the [documentation.md](documentation.md) for a full explanation of the available settings.

4.  The application window will appear. It has controls to start and stop the transcription, and a separate window to show the transcribed text.

## Future Plans

We have many ideas for improving this application. For a full list of planned features, see [future_plans.md](future_plans.md).