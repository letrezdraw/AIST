# Contributing to AIST

First off, thank you for considering contributing to AIST! It's people like you that make open source such a great community. We welcome any and all contributions, from bug reports to new features.

To ensure a smooth process, please review the following guidelines.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/letrezdraw/AIST/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/letrezdraw/AIST/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements

- Open a new issue with the "enhancement" label.
- Clearly describe the proposed enhancement and the motivation for it. Explain why this enhancement would be useful to AIST users.

### Pull Requests

1.  Fork the repository and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  Ensure the test suite passes (`pytest`).
4.  Make sure your code lints (`flake8` or `black`).
5.  Issue that pull request!

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests liberally after the first line.

### Python Styleguide

- All Python code must adhere to PEP 8.
- We use `black` for code formatting and `flake8` for linting.
- Use type hints for all function signatures.

## Development Setup

1.  Follow the installation instructions in `README.md` to set up your virtual environment.
2.  Install the development dependencies:
    ```bash
    python -m pip install -r requirements-dev.txt
    ```
    *(Note: We will create this `requirements-dev.txt` file as part of the TDD epic, which will contain `pytest`, `black`, `flake8`, etc.)*

Thank you for your contribution!