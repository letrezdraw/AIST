# AIST Project Roadmap

## 🚀 Vision Statement

AIST aims to be the definitive open-source AI assistant framework for the privacy-conscious user and the creative developer. Our goal is to surpass existing alternatives by delivering a system that is more modular, intelligent, performant, and secure. We will achieve this through a relentless focus on a robust architecture, a world-class developer experience, and cutting-edge AI capabilities. This document outlines the strategic roadmap to realize that vision.

---

## 🧭 Guiding Principles

These philosophies will guide every architectural decision and feature implementation:

* **Offline-First & Privacy-Centric:** All core functionality must operate without an internet connection. User data is sacred and stays on the user's device.
* **Extremely Modular:** "Everything is a plugin." Core services like STT, TTS, and even the conversation engine will be swappable components.
* **Developer-First Experience:** Creating new skills and contributing to the core should be simple, intuitive, and well-documented.
* **User-Empowering:** The user should have maximum control over their data, configuration, and experience.
* **Performant & Resourceful:** The system must be responsive and efficient on standard consumer hardware.

---

## 🗺️ Development Phases

### Phase 1: The Scalable Foundation (Target: Q3 2025)
*Goal: Rebuild the core of AIST to be robust, scalable, and maintainable, setting the stage for all future development.*

#### **Epic 1.1: The Message Bus Architecture**
> **Why:** To achieve true decoupling and scalability, we are moving from a direct client-server model to a fully event-driven architecture. This is the #1 prerequisite for a large-scale system, inspired by the stability of frameworks like Mycroft.
>
> **Key Tasks:**
> - [ ] Research and select a lightweight, thread-safe message bus library (e.g., `PyPubSub`).
> - [ ] Define a strict event naming convention in `core/events.py` (e.g., `stt.transcribed`, `llm.response.ready`, `skill.execute`).
> - [ ] Refactor all existing components (STT, TTS, Main, Backend) to communicate exclusively through publishing and subscribing to messages on the bus.
>
> **✅ Success Criteria:** The frontend and backend processes have zero direct code dependency on each other; they only know about the message bus. The system functions identically to the user but is now architecturally superior.

#### **Epic 1.2: Centralized & Dynamic Configuration**
> **Why:** To empower users and simplify deployment, all hardcoded settings will be externalized into a user-friendly configuration file.
>
> **Key Tasks:**
> - [ ] Implement a `ConfigManager` class in `core/config.py` that loads settings from `AIST_data/config.yaml`.
> - [ ] Create a `config.template.yaml` file with extensive comments explaining every possible configuration option.
> - [ ] Replace every hardcoded path, model name, activation phrase, hotkey, and setting in the entire codebase with a call to the `ConfigManager`.
> - [ ] **(Stretch Goal):** Implement hot-reloading: the system should detect changes to `config.yaml` and reload relevant services without a full restart.
>
> **✅ Success Criteria:** The assistant's voice, language model, activation phrase, and performance settings can be changed by editing the YAML file and restarting the service.

#### **Epic 1.3: The Test-Driven Development Framework**
> **Why:** To ensure stability, reliability, and code quality at scale, we will adopt a Test-Driven Development (TDD) approach for all new features.
>
> **Key Tasks:**
> - [ ] Integrate `pytest` and configure it with code coverage reporting (`pytest-cov`).
> - [ ] Create a `tests/` directory with `unit/` and `integration/` subdirectories.
> - [ ] Write unit tests for all existing non-I/O utility functions, achieving >80% code coverage on those modules.
> - [ ] Write foundational integration tests that simulate sending a message on the bus and asserting that the correct component responds as expected.
>
> **✅ Success Criteria:** A testing suite can be run via a single command (`./run_tests.sh` or `pytest`) and all tests pass, providing a safety net for all future development.

---

### Phase 2: The World-Class Skill Ecosystem (Target: Q4 2025)
*Goal: Design and build a skill system that is more powerful, flexible, and easier for developers to use than any competitor.*

#### **Epic 2.1: The Unified Skill API**
> **Why:** To provide a simple yet powerful interface for developers to create skills. This API will be the cornerstone of the AIST ecosystem.
>
> **Key Tasks:**
> - [ ] Define the `core.skills.BaseSkill` class with a clear lifecycle: `__init__`, `initialize` (receives the message bus instance), `register_intents`, `execute(payload)`, and `shutdown`.
> - [ ] Create a `skill.json` manifest file required for every skill, defining its name, version, author, and dependencies.
> - [ ] Develop a `SkillManager` service that discovers, validates, and loads all valid skills from the `skills/` directory at startup.
>
> **✅ Success Criteria:** A developer can create a new "Hello World" skill by creating one folder containing a `skill.json` and one `__init__.py` file.

#### **Epic 2.2: The Hybrid Intent Parser**
> **Why:** To achieve unparalleled intent recognition by combining the speed and reliability of classic parsing with the raw intelligence of modern LLMs.
>
> **Key Tasks:**
> - [ ] **Stage 1 (Fast Path):** The `register_intents` method will allow skills to claim simple keywords or regular expressions. The `SkillManager` will use these for instant, unambiguous command routing.
> - [ ] **Stage 2 (LLM Function Calling):** If no fast-path match is found, the system will construct a detailed prompt for the LLM, including the command and a list of all available skills and their descriptions (from `skill.json`). The LLM's role is to return a structured JSON object like `{"skill": "weather_skill", "parameters": {"city": "Pune"}}`.
> - [ ] Implement robust JSON parsing and validation for the LLM's output to handle potential errors gracefully.
>
> **✅ Success Criteria:** The system can successfully route both simple commands ("open notepad") and complex commands ("remind me to call mom when I leave work") to the correct skill with the correct parameters.

#### **Epic 2.3: The Resilient Skill Runner**
> **Why:** To ensure system stability and security, even when running poorly written or malicious third-party skills.
>
> **Key Tasks:**
> - [ ] The `SkillManager` will run each skill in its own sandboxed process using Python's `multiprocessing` library.
> - [ ] Implement a strict timeout for skill execution to prevent infinite loops from freezing the system.
> - [ ] Any crash or unhandled exception within a skill process will be caught and logged by the `SkillManager` without affecting the core AIST services.
>
> **✅ Success Criteria:** A skill that enters an infinite loop or crashes does not impact the responsiveness or stability of the rest of the assistant.

---

### Phase 3: The Superior Experience (Target: Q1 2026)
*Goal: To polish AIST into a product that feels more alive, intelligent, and user-friendly than any other open-source assistant.*

#### **Epic 3.1: The Pluggable Provider Architecture**
> **Why:** To offer ultimate flexibility, allowing users to easily swap out core AI components. This makes AIST a true framework, not just an application.
>
> **Key Tasks:**
> - [ ] Create abstract base classes for each core service: `BaseSTTProvider`, `BaseTTSProvider`, `BaseLLMProvider`.
> - [ ] Refactor the existing `Vosk`, `Piper`, and `ctransformers` integrations into concrete provider classes that inherit from these bases.
> - [ ] The `ConfigManager` will dynamically load the provider specified in `config.yaml`.
> - [ ] Write clear documentation on how a developer can create and contribute a new provider (e.g., for OpenAI Whisper or Coqui TTS).
>
> **✅ Success Criteria:** A user can switch their STT engine from `Vosk` to `Whisper` by changing one line in the config file.

#### **Epic 3.2: The Contextual Conversation Engine**
> **Why:** To move beyond simple command-response and enable natural, flowing dialogue that remembers the recent past.
>
> **Key Tasks:**
> - [ ] Create a `ConversationManager` service that stores a rolling history of the last N user/AI exchanges.
> - [ ] This history will be automatically formatted and prepended to all prompts sent to the LLM Provider.
> - [ ] Create a `core.memory` skill that can be triggered to use the LLM to summarize the current conversation history and store salient facts in the long-term SQLite database.
>
> **✅ Success Criteria:** The assistant can successfully answer follow-up questions (e.g., User: "Who is the CEO of Microsoft?" -> AIST: "Satya Nadella." -> User: "Where was he born?" -> AIST: "Hyderabad, India.").

#### **Epic 3.3: The Polished GUI Overlay**
> **Why:** A visual interface provides critical real-time feedback and makes the assistant feel significantly more professional and integrated into the OS.
>
> **Key Tasks:**
> - [ ] Select a GUI framework (`Flet` for modern simplicity, `PyQt` for power and customizability).
> - [ ] Design and build a minimal, clean UI that shows the assistant's state (`Listening`, `Thinking`, `Speaking`), the real-time transcription, and final responses.
> - [ ] The GUI will run as its own component process, subscribing to the message bus for all its information.
>
> **✅ Success Criteria:** The user can visually see what the assistant is doing at all times, dramatically improving the user experience.

---

### Phase 4: The Next Frontier (Beyond Q1 2026)
*Goal: To introduce next-generation features that put AIST in a class of its own.*

- [ ] **Proactive Intelligence:** Develop a "trigger" system where skills can be activated by system events (time, location, application launch), not just voice.
- [ ] **Multi-Modal Interaction:** Create skills that can understand more than just voice, such as reading text from a screenshot (Vision) or the clipboard.
- [ ] **The AIST Skill Store:** Build a command-line interface and eventually a web UI for users to easily discover, install, and manage third-party skills.
- [ ] **Packaged Installer:** Create a professional Windows installer using `Inno Setup` that handles dependencies, model downloads, and setup, providing a one-click installation experience.

