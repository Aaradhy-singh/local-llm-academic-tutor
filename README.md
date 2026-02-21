Academic Tutor - Local Ollama Edition
A simple, offline academic tutor for students. Runs completely free on your local machine using Ollama.

What It Does
Answers academic questions (math, science, CS, logic)
Rejects non-academic queries
Maintains conversation context
Runs 100% offline and free
Setup
Install Ollama

# Visit: https://ollama.ai/download
Pull a model

ollama pull llama3.2
Install Python dependencies

pip install openai
Start Ollama

ollama serve
Run the tutor

python app.py
Usage
You: What is the derivative of x^2?

Tutor: Let me break this down step-by-step...
Type exit or quit to stop.

Features
Zero cost - runs locally
Simple - single file, ~130 lines
Academic only - built-in scope enforcement
Context aware - remembers recent conversation
Easy to modify - straightforward code
Requirements
Python 3.8+
Ollama running locally
openai Python package
Architecture
Single file (app.py) with:

Ollama connection via OpenAI-compatible API
System prompt for academic scope
Simple message buffer (last 6 messages)
Streaming response output
Clean error handling
No classes, no abstractions, no over-engineering.
