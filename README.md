# Offline-GPT

A standalone, cross-platform chat client for conversing with a local LLM (offline use). Built with Python, PySide6, and llama-cpp-python. Includes a modern UI, dark/light mode, and persistent chat history.

## Features

- Local LLM inference (TinyLlama 1.1B bundled)
- Modern chat UI (PySide6)
- Dark/light mode toggle
- Persistent chat history (SQLite, 500MB configurable limit)
- Cross-platform: Windows, macOS, Linux
- Single-file executable via PyInstaller

## Setup (Development)

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python -m offline_gpt
   ```

## Packaging

To build a standalone executable:

```bash
pyinstaller offline_gpt/__main__.py --onefile
```

## Testing

Run unit tests with:

```bash
pytest
```

## Configuration

Settings (e.g., chat history storage limit) are stored in `config.json`.
