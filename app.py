"""
Local Academic Tutor - Ollama Edition (Enhanced)
Minimal offline academic help for students. Zero cost, fully local.
"""

import sys
import json
from datetime import datetime
from typing import List
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "phi3:mini"
FAST_MODEL = "phi3:mini" # Fallback placeholder for 4-bit quantization
MAX_MEMORY = 4

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
        console.print(f"[bold red]❌ Error connecting to Ollama:[/bold red] {e}")
        console.print("   Make sure Ollama is running: [cyan]ollama serve[/cyan]")
        sys.exit(1)

def detect_query_type(question: str) -> str:
    """Detect question type for optimal response"""
    question_lower = question.lower()
    
    if any(kw in question_lower for kw in ['math', 'derive', 'solve', 'equation']):
        return 'math'
    elif any(kw in question_lower for kw in ['code', 'program', 'debug', 'algorithm']):
        return 'code'
    elif any(kw in question_lower for kw in ['explain', 'why', 'how', 'mechanism']):
        return 'detailed'
    else:
        return 'default'

def get_optimal_params(question: str) -> dict:
    """Get temperature and parameters based on question"""
    query_type = detect_query_type(question)
    
    params_map = {
        'math': {'temperature': 0.2, 'max_tokens': 300},
        'code': {'temperature': 0.1, 'max_tokens': 400},
        'detailed': {'temperature': 0.4, 'max_tokens': 500},
        'default': {'temperature': 0.3, 'max_tokens': 200}
    }
    
    return params_map.get(query_type, params_map['default'])

def ask(client, messages):
    try:
        # Get optimal parameters based on the last user question
        last_question = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "")
        params = get_optimal_params(last_question)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
            **params
        )
        
        full_text = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                console.print(text, end='', style="yellow")
                full_text += text
        
        console.print()
        return full_text if full_text else "No response"
    
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        return ""

def trim_memory(messages):
    if len(messages) <= MAX_MEMORY * 2 + 1:
        return messages
    return [messages[0]] + messages[-(MAX_MEMORY * 2):]

def export_conversation(messages):
    filename = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(messages, f, indent=2)
    console.print(f"[bold green]✔ Conversation exported to {filename}[/bold green]")

def handle_command(cmd, messages):
    command = cmd[1:].lower()
    if command == 'help':
        console.print(Panel(
            "[cyan]/help[/cyan] - Show available commands\n"
            "[cyan]/history[/cyan] - Display recent conversation\n"
            "[cyan]/clear[/cyan] - Clear conversation history\n"
            "[cyan]/export[/cyan] - Save conversation to file\n"
            "[cyan]/exit[/cyan] - Exit application",
            title="Commands", expand=False
        ))
        return messages
    elif command == 'history':
        for i, msg in enumerate(messages[1:], 1):
            if msg['role'] == 'user':
                console.print(f"[{i}] [green]You:[/green] {msg['content'][:60]}...")
            else:
                console.print(f"    [yellow]Tutor:[/yellow] {msg['content'][:60]}...")
        return messages
    elif command == 'clear':
        console.print("[yellow]Conversation cleared.[/yellow]")
        return [messages[0]]
    elif command == 'fast':
        global MODEL
        MODEL = FAST_MODEL
        console.print(f"[bold green]Switched to fast quantized model: {MODEL}[/bold green]")
        return messages
    elif command == 'batch':
        console.print("[cyan]Enter multiple questions separated by '|'. Example: What is DNA? | Solve 2x=4[/cyan]")
        batch_input = input("Batch: ").strip()
        if batch_input:
            questions = [q.strip() for q in batch_input.split('|') if q.strip()]
            handle_batch(questions)
        return messages
    elif command == 'export':
        export_conversation(messages)
        return messages
    elif command in ('exit', 'quit', 'q'):
        console.print("[bold yellow]Goodbye![/bold yellow]")
        sys.exit(0)
    else:
        console.print(f"[red]Unknown command:[/red] {cmd}")
        return messages

def handle_batch(questions: List[str]):
    """Process multiple questions sequentially"""
    client = OpenAI(base_url=OLLAMA_URL, api_key="not-needed")
    console.print(f"[yellow]Processing {len(questions)} questions sequentially...[/yellow]")
    
    for idx, q in enumerate(questions):
        console.print(f"\n[bold green]Q{idx+1}:[/bold green] {q}")
        console.print(f"[bold yellow]A{idx+1}:[/bold yellow] ", end="")
        ask(client, [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": q}])

def main():
    console.print(Panel("[bold cyan]Academic Tutor - Local & Free[/bold cyan]", expand=False))
    console.print(f"Model: {MODEL}")
    console.print("Commands: Type [cyan]/help[/cyan] to see options\n")
    
    client = connect()
    console.print("[bold green]✅ Connected to Ollama[/bold green]\n")
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    while True:
        try:
            console.print("[bold green]You:[/bold green] ", end="")
            question = input().strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[bold yellow]Goodbye![/bold yellow]")
            break
        
        if not question:
            continue
            
        if question.startswith('/'):
            messages = handle_command(question, messages)
            continue
        
        if question.lower() in ['exit', 'quit', 'q']:
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break
        
        messages.append({"role": "user", "content": question})
        messages = trim_memory(messages)
        
        console.print("\n[bold yellow]Tutor:[/bold yellow] ", end="")
        response = ask(client, messages)
        
        if response:
            messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
