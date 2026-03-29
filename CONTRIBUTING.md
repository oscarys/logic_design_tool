# Contributing to VHDL Design Tool

Thank you for your interest in contributing! This document explains how to get involved.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vhdl-tool.git
   cd vhdl-tool
   ```
3. **Set up** a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```
4. **Run** the app to verify everything works:
   ```bash
   python main.py
   ```

## How to Contribute

### Reporting Bugs
- Open an issue on GitHub
- Include your OS, Python version, and PyQt6 version
- Include the full traceback if the app crashed
- Describe the steps to reproduce

### Suggesting Features
- Open an issue labelled `enhancement`
- Describe the use case — especially for classroom use

### Adding a Language
The i18n system makes adding a new language straightforward:

1. Copy `i18n/en.py` to `i18n/xx.py` (where `xx` is the language code)
2. Translate all string values (keep the keys unchanged)
3. Add the language to `_SUPPORTED` and `_LANG_NAMES` in `i18n/__init__.py`
4. Add `actionLangXx` to `ui/main_window.ui` and wire it in `main_window.py`

### Submitting a Pull Request
1. Create a branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Verify the app starts and the affected feature works
4. Run a quick syntax check: `python -m py_compile **/*.py`
5. Commit with a clear message: `git commit -m 'Add French translation'`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request — describe what changed and why

## Code Style

- Python 3.10+ type hints where practical
- PyQt6 — no PyQt5 compatibility concerns
- UI structure in `.ui` files (Qt Designer format), logic in Python
- Translatable strings via `tr("key")` — never hardcode user-visible text
- No external dependencies beyond PyQt6

## Project Architecture

See `README.md` for the full directory structure. Key principles:

- **`widgets/`** — PyQt6 widgets, no business logic
- **`generators/`** — pure Python, no Qt imports, no side effects
- **`simulation/`** — pure Python FSM engine, no Qt imports
- **`i18n/`** — no Qt at module level (lazy imports only)
- **`project/`** — JSON serialisation, Qt only for QSettings
