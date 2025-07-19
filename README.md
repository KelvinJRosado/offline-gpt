# Offline-GPT

A standalone, cross-platform chat client for conversing with a local LLM (offline use). Built with Python, PySide6, and llama-cpp-python. Includes a modern UI, dark/light mode, and persistent chat history.

## Features

- Local LLM inference (Phi 3 mini bundled)
- Modern chat UI (PySide6)
- Dark/light mode toggle
- Persistent chat history (SQLite, 500MB configurable limit)
- Cross-platform: Windows, macOS, Linux
- Single-file executable via PyInstaller

## Setup (Development)

1. Clone the repo
2. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Download the Phi 3 mini model file:**
   ```bash
   mkdir -p models
   curl -L -o models/Phi-3-mini-4k-instruct-q4.gguf \
     https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
   ```
5. Run the app:
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
