# Project TODO List

## ✅ Completed Features

- [x] Set up initial project structure with directories for UI, backend (LLM), database, and config
- [x] Create requirements.txt with pinned versions for PySide6, llama-cpp-python, and other dependencies
- [x] Implement basic PySide6 app skeleton with modern chat UI, dark/light mode toggle, and message send/receive interface
- [x] Integrate llama-cpp-python for local LLM inference using Phi 3 mini GGUF model
- [x] Set up SQLite database for chat history with a configurable 100 MB storage limit and deletion logic
- [x] Add configuration system (default to .json) for storage limit and future settings
- [x] Create README with usage and development instructions
- [x] Add multi-conversation support with sidebar navigation
- [x] Implement conversation management (create, delete, clear)
- [x] Add storage usage progress bar with color-coded thresholds
- [x] Implement markdown rendering in chat bubbles
- [x] Add loading indicators and proper async LLM responses
- [x] Fix full response capture (no more truncated responses)
- [x] Add structured logging to /logs directory
- [x] Implement proper conversation context preservation

## 🔄 In Progress

- [x] Add pytest skeleton for unit testing

## 🚀 Future Enhancements

- [ ] Add code syntax highlighting for code blocks
- [ ] Implement conversation export/import functionality
- [ ] Add keyboard shortcuts for common actions
- [ ] Implement conversation search functionality
- [ ] Add model switching capability
- [ ] Implement conversation tagging/categorization
- [ ] Add conversation sharing via links/files
- [ ] Implement conversation templates/prompts
- [ ] Add voice input/output capabilities
- [ ] Implement conversation analytics and insights
