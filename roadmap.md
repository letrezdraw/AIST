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
> **Key Tasks (Frontend):**
> - [x] Research and select a lightweight, thread-safe message bus library (`PyPubSub`).
> - [x] Define a strict event naming convention in `core/events.py`.
> - [x] Refactor frontend components (STT, TTS, Main) to communicate exclusively through the message bus.
>
> **✅ Success Criteria:** The frontend components are fully decoupled. The system is robust and ready for a GUI overlay.

#### **Epic 1.2: Centralized & Dynamic Configuration (DONE)**
> **Why:** To empower users and simplify deployment, all hardcoded settings will be externalized into a user-friendly configuration file.
>
> **Key Tasks:**
> - [x] Implement a `ConfigManager` class in `core/config_manager.py` that loads settings from `config.yaml`.
> - [x] Create a `config.template.yaml` file with extensive comments explaining every possible configuration option.
> - [x] Replace every hardcoded path, model name, activation phrase, hotkey, and setting in the entire codebase with a call to the `ConfigManager`.
> - [ ] **(Stretch Goal):** Implement hot-reloading: the system should detect changes to `config.yaml` and reload relevant services without a full restart.
>
> **✅ Success Criteria:** The assistant's voice, language model, STT provider, activation phrases, and performance settings can be changed by editing the YAML file and restarting the service.

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
> - [x] Define the `core.skills.BaseSkill` class with a clear lifecycle: `__init__`, `initialize`, `register_intents`.
> - [x] Create a `skill.json` manifest file required for every skill, defining its name, version, author, and dependencies.
> - [x] Develop a `SkillManager` service that discovers, validates, and loads all valid skills from the `skills/` directory at startup.
>
> **✅ Success Criteria:** A developer can create a new "Current Time" skill by creating one folder containing a `skill.json` and one `__init__.py` file. The system correctly loads and executes it.

#### **Epic 2.2: The Hybrid Intent Parser**
> **Why:** To achieve unparalleled intent recognition by combining the speed and reliability of classic parsing with the raw intelligence of modern LLMs.
>
> **Key Tasks:**
> - [x] **Stage 1 (Fast Path):** The `dispatcher` uses fuzzy matching on registered intent phrases for instant, unambiguous command routing.
> - [x] **Stage 2 (LLM Function Calling):** If no fast-path match is found, the system constructs a detailed prompt for the LLM, describing all available skills and their parameters. The LLM's role is to return a structured JSON object like `{"function": "store_memory", "parameters": {"fact": "my pin is 1234"}}`.
> - [x] Implemented robust JSON parsing and validation for the LLM's output to handle potential errors gracefully.
>
> **✅ Success Criteria:** The system can successfully route both simple commands ("what time is it") and complex, parameterized commands ("remember that my pin is 1234") to the correct skill with the correct parameters.

#### **Epic 2.3: The Resilient Skill Runner**
> **Why:** To ensure system stability and security, even when running poorly written or malicious third-party skills.
>
> **Key Tasks:**
> - [x] The dispatcher now runs each skill in its own sandboxed process using Python's `multiprocessing` library.
> - [x] Implemented a strict, configurable timeout for skill execution to prevent infinite loops from freezing the system.
> - [x] Any crash or unhandled exception within a skill process is caught and logged, allowing the core AIST services to continue running unaffected.
>
> **✅ Success Criteria:** A skill that enters an infinite loop or crashes does not impact the responsiveness or stability of the rest of the assistant.

---

### Phase 3: The Superior Experience (Target: Q1 2026)
*Goal: To polish AIST into a product that feels more alive, intelligent, and user-friendly than any other open-source assistant.*

#### **Epic 3.1: The Pluggable Provider Architecture**
> **Why:** To offer ultimate flexibility, allowing users to easily swap out core AI components. This makes AIST a true framework, not just an application.
>
> **Key Tasks (STT):**
> - [x] Create abstract base class `BaseSTTProvider`.
> - [x] Refactor the existing `Vosk` integration into a concrete provider class.
> - [x] Implement a new, high-accuracy `Whisper` provider.
> - [x] The `ConfigManager` dynamically loads the STT provider specified in `config.yaml`.
>
> **Key Tasks (TTS):**
> - [x] Create abstract base class `BaseTTSProvider`.
> - [x] Refactor the existing `Piper` integration into a concrete provider class.
> - [x] The `ConfigManager` dynamically loads the TTS provider specified in `config.yaml`.
>
> **✅ Success Criteria:** A user can switch their STT and TTS engines by changing one line in the config file, making the core AI services fully modular.

#### **Epic 3.2: The Contextual Conversation Engine**
> **Why:** To move beyond simple command-response and enable natural, flowing dialogue that remembers the recent past.
>
> **Key Tasks:**
> - [x] Create a `ConversationManager` service that stores a rolling history of the last N user/AI exchanges.
> - [x] This history is automatically passed to the LLM, enabling contextual conversations.
> - [ ] **(Next):** Create a `core.memory` skill that can be triggered to use the LLM to summarize the current conversation history and store salient facts in the long-term SQLite database.
>
> **✅ Success Criteria:** The assistant can successfully answer follow-up questions (e.g., User: "Who is the CEO of Microsoft?" -> AIST: "Satya Nadella." -> User: "Where was he born?" -> AIST: "Hyderabad, India.").

#### **Epic 3.3: The Polished GUI Overlay**
> **Why:** A visual interface provides critical real-time feedback and makes the assistant feel significantly more professional and integrated into the OS.
>
> **Key Tasks:**
> - [x] Select a GUI framework (`Flet`) and create the initial UI structure.
> - [x] Implement an inter-process event bus using ZMQ PUB/SUB sockets.
> - [x] Connect the GUI to the event bus to display real-time state and conversation.
>
> **✅ Success Criteria:** The user can visually see what the assistant is doing at all times, dramatically improving the user experience.

---

### Phase 4: The Next Frontier (Beyond Q1 2026)
*Goal: To introduce next-generation features that put AIST in a class of its own.*

- [ ] **Proactive Intelligence:** Develop a "trigger" system where skills can be activated by system events (time, location, application launch), not just voice.
- [ ] **Multi-Modal Interaction:** Create skills that can understand more than just voice, such as reading text from a screenshot (Vision) or the clipboard.
- [ ] **The AIST Skill Store:** Build a command-line interface and eventually a web UI for users to easily discover, install, and manage third-party skills.
- [ ] **Packaged Installer:** Create a professional Windows installer using `Inno Setup` that handles dependencies, model downloads, and setup, providing a one-click installation experience.
