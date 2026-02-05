"""
Local Academic Tutor - Ollama Edition
Minimal offline academic help for students. Zero cost, fully local.

Setup:
    pip install openai
    ollama pull llama3.2
    ollama serve
    python app.py
"""

import sys
from openai import OpenAI

OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "phi3:mini"
MAX_MEMORY = 6

SYSTEM_PROMPT = """You are a local AI assistant running entirely on the user’s machine via Ollama.

Primary objective:
Produce correct, concise, high-signal answers with minimal latency.

Operational rules:
- Answer directly. No preambles.
- Do not repeat the question.
- Do not add filler, politeness, or commentary.
- Do not explain unless explanation is explicitly required.
- Prefer short sentences.
- Prefer lists only when they reduce length.
- Avoid speculation. If uncertain, say “I don’t know.”
- Correct factual errors plainly.

Reasoning:
- Use internal reasoning silently.
- Show steps only when solving math, logic, or code debugging.
- Otherwise, output conclusions only.

Style constraints:
- No emojis.
- No motivational language.
- No disclaimers.
- No moralizing.
- No roleplay unless explicitly requested.
- Neutral, technical tone.

Behavioral constraints:
- Stay on-topic.
- Do not drift into unrelated explanations.
- Do not invent facts.
- Do not argue with the user.
- Do not ask follow-up questions unless clarification is strictly required.

Performance constraints:
- Optimize for fast response over verbosity.
- Prefer deterministic answers.
- Avoid creative rewriting unless explicitly requested.

You are an academic and technical assistant.
Your job is correctness, clarity, and speed."""


def connect():
    try:
        client = OpenAI(base_url=OLLAMA_URL, api_key="not-needed")
        return client
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        sys.exit(1)


def ask(client, messages):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
            temperature=0.3
        )
        
        full_text = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end='', flush=True)
                full_text += text
        
        print()
        return full_text if full_text else "No response"
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return ""


def trim_memory(messages):
    if len(messages) <= MAX_MEMORY + 1:
        return messages
    return [messages[0]] + messages[-MAX_MEMORY:]


def main():
    print("="*60)
    print("  Academic Tutor - Local & Free")
    print("="*60)
    print(f"Model: {MODEL}")
    print("Commands: 'exit' or 'quit' to stop\n")
    
    client = connect()
    print("✅ Connected to Ollama\n")
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break
        
        if question.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        messages.append({"role": "user", "content": question})
        messages = trim_memory(messages)
        
        print("\nTutor: ", end='', flush=True)
        response = ask(client, messages)
        
        if response:
            messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
