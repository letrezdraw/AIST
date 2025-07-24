# AIST - AI Assistant

> A modular, voice-activated AI assistant for Windows that runs locally on your machine.

AIST is AI assistant designed to provide a deeply integrated, conversational, and extensible AI companion that respects user privacy by performing all core processing on-device.

---

## ✨ Core Features

----
----
*   **Voice Activation**: Hands-free activation using a customizable wake word.
*   **Local AI Processing**: All intent recognition and chat functions are handled by a local LLM (`Mistral 7B`), ensuring privacy and offline functionality.
*   **Conversational Context**: Remembers the last few turns of a conversation to understand follow-up questions.
*   **Long-Term Memory (Learning)**:
    *   Can be taught specific facts using the "remember" or "learn" command.
    *   Automatically recalls and uses learned information when relevant.
*   **System Control**:
    *   Open any application on the system (e.g., "open notepad").
    *   Close running applications (e.g., "close notepad").
*   **Web Search**: Can open the default web browser to perform a Google search.
*   **Background Operation**: Runs as a persistent icon in the system tray.

---

## 🚀 Getting Started

### Prerequisites
*   Windows 10/11
*   Python 3.9+
*   A microphone
*   An NVIDIA GPU (highly recommended for good performance)

----
----
----
### Installation
1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd AIST
    ```
2.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
3.  **Download AI Model:**
    - Download a GGUF model like `mistral-7b-instruct-v0.2.Q4_K_M.gguf` from Hugging Face.
    - Place the `.gguf` file in the project's root directory.
4.  **Configure:**
    - Open `config.py` and ensure `MODEL_PATH` matches your model's filename.
    
## ▶️ Usage
Run the assistant from your terminal:
```sh
python main.py
```
The AIST icon will appear in your system tray. Say "hey assistant" followed by your command.

**Example Commands:**
*   *"hey assistant, what time is it?"*
*   *"hey assistant, open notepad."*
*   *"hey assistant, remember that my PIN is 1234."*
*   *"hey assistant, what is my PIN?"*

## 📚 Documentation
For a deep dive into the project's architecture, how it works, and a guide to adding new skills, please see the full **Project Documentation**.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

## 📄 License
This project is licensed under the MIT License.

