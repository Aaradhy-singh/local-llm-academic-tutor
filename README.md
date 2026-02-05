# Academic Tutor - Local Ollama Edition

A simple, offline academic tutor for students. Runs completely free on your local machine using Ollama.

## What It Does

- Answers academic questions (math, science, CS, logic)
- Rejects non-academic queries
- Maintains conversation context
- Runs 100% offline and free

## Setup

1. **Install Ollama**
   ```bash
   # Visit: https://ollama.ai/download
   ```

2. **Pull a model**
   ```bash
   ollama pull llama3.2
   ```

3. **Install Python dependencies**
   ```bash
   pip install openai
   ```

4. **Start Ollama**
   ```bash
   ollama serve
   ```

5. **Run the tutor**
   ```bash
   python app.py
   ```

## Usage

```
You: What is the derivative of x^2?

Tutor: Let me break this down step-by-step...
```

Type `exit` or `quit` to stop.

## Features

- **Zero cost** - runs locally
- **Simple** - single file, ~130 lines
- **Academic only** - built-in scope enforcement
- **Context aware** - remembers recent conversation
- **Easy to modify** - straightforward code

## Requirements

- Python 3.8+
- Ollama running locally
- `openai` Python package

## Architecture

Single file (`app.py`) with:
- Ollama connection via OpenAI-compatible API
- System prompt for academic scope
- Simple message buffer (last 6 messages)
- Streaming response output
- Clean error handling

No classes, no abstractions, no over-engineering.
