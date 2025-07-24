# AIST - Your Personal AI Assistant for Windows

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
[![License: CC BY-NC-SA 4.0](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

AIST is a voice-controlled, conversational AI assistant that runs locally on your Windows machine. It's designed to be highly integrated with the OS, allowing you to perform tasks, get information, and have conversations, all with the power of your voice and the privacy of local processing.

## ✨ Features

-   **Voice-Controlled:** Fully operational via voice commands.
-   **Wake Word Activation:** Listens for "Hey Assistant" to start.
-   **Local & Private:** All AI processing is done on your machine using a local LLM. Nothing is sent to the cloud.
-   **GPU Accelerated:** Leverages your NVIDIA GPU for lightning-fast responses.
-   **Background Operation:** Runs silently in the system tray.
-   **Core Skills:**
    -   Open applications (`"Open notepad"`)
    -   Search the web (`"Search for the weather in Pune"`)
    -   Get the current time (`"What time is it?"`)
    -   Check system status (`"What's the CPU usage?"`, `"Check battery status"`)

## ⚙️ Installation

Follow these steps to get AIST running on your system.

### 1. Prerequisites

-   **Python:** Make sure you have Python 3.9 or newer installed. You can get it from python.org.
-   **Git:** You'll need Git to clone the repository. You can get it from git-scm.com.
-   **(Optional) NVIDIA GPU:** For the best performance, an NVIDIA GPU with CUDA support is recommended.

### 2. Setup Instructions

**1. Clone the Repository:**
Open a terminal or command prompt and run:
```bash
git clone https://github.com/letrezdraw/AIST.git
cd AIST
```

**2. Create a Virtual Environment:**
It's highly recommended to use a virtual environment to keep dependencies isolated.
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install Dependencies:**
Install all the required Python packages using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

**4. Download the AI Model:**
This project uses a local Large Language Model. You need to download it separately as it's too large for GitHub.

-   **Model:** `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
-   [**Download Link:**](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf) Click here to download from Hugging Face

**Important:** Place the downloaded `.gguf` file directly inside your `AIST` project folder.

**5. Configure the Assistant:**
Open the `config.py` file and ensure the `MODEL_PATH` matches the name of the file you just downloaded. It should already be correct by default.

## 🚀 Usage

Once everything is installed and configured, you can start the assistant by running:

```bash
python main.py
```

The assistant will start in the background, and you'll see its icon in the system tray. Say the wake word `"Hey Assistant"` to activate it.

## 🗺️ Project Roadmap

Here's what's planned for the future of AIST:

-   **Executable AI Assistant:** By default, it runs on Windows startup, but an `.exe` option is available for user preference.
-   **Smarter Intent Recognition:** Move from simple keywords to full LLM-based intent recognition for more natural commands.
-   **Enhanced User Feedback:** Add audio cues for different states (listening, processing).
-   **New Skills:** Real-time weather reports, system controls (volume, mute, lock, shutdown).
-   **Robust Logging:** For easier debugging and development.

## 🤝 Contributing

Contributions are welcome! If you have ideas for new skills or improvements, feel free to fork the repository, make your changes, and submit a pull request.

## 📜 License
This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](LICENSE.md).