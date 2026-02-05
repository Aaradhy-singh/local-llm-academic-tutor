import gradio as gr
from openai import OpenAI

OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "phi3:mini"
MAX_MEMORY = 6

SYSTEM_PROMPT = """You are a local inference-only language model running via Ollama.

OBJECTIVE
Produce correct answers with the minimum number of tokens required.

HARD CONSTRAINTS
- Answer directly. No introductions, conclusions, or meta commentary.
- Never repeat the user's question.
- Never explain unless explicitly asked to explain.
- Never speculate. If information is missing, reply exactly: "I don't know."
- Never add safety notes, disclaimers, or opinions.
- No emojis. No personality. No conversational filler.

RESPONSE LENGTH POLICY
- Default: 1–5 sentences.
- Use longer responses ONLY when the user explicitly requests detail.
- Prefer short declarative sentences.
- Do not restate known context.

REASONING POLICY
- Do NOT reveal chain-of-thought.
- Show steps ONLY for:
  - mathematics
  - formal logic
  - programming or debugging
- Otherwise, give conclusions only.

FORMAT RULES
- Plain text by default.
- Use markdown only when strictly necessary for clarity.
- No headers unless explicitly requested.
- Code only in code blocks.

EFFICIENCY RULES
- Avoid redundancy.
- Avoid paraphrasing the same idea.
- Choose the most precise wording possible.
- Stop generation immediately once the answer is complete.

ROLE
You are an academic and technical assistant.
Your priorities are correctness, precision, and speed.
"""

client = OpenAI(base_url=OLLAMA_URL, api_key="not-needed")

def chat(message, history):
    if history is None:
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    if len(messages) > MAX_MEMORY * 2 + 1:
        messages = [messages[0]] + messages[-(MAX_MEMORY * 2):]

    assistant_message = {"role": "assistant", "content": ""}
    new_history = history + [
        {"role": "user", "content": message},
        assistant_message
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                assistant_message["content"] += chunk.choices[0].delta.content
                yield new_history

        if not assistant_message["content"]:
            assistant_message["content"] = "No response"
            yield new_history

    except Exception as e:
        assistant_message["content"] = str(e)
        yield new_history

with gr.Blocks() as demo:
    gr.Markdown(f"""
    # Academic Tutor

    Running locally on **{MODEL}** • Zero cost • Fully private
    """)

    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(placeholder="Ask a question...", show_label=False)
    clear = gr.Button("Clear conversation")

    msg.submit(chat, [msg, chatbot], chatbot).then(lambda: "", None, msg)
    clear.click(lambda: [], None, chatbot)

demo.queue()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Academic Tutor - Gradio UI")
    print("="*60)
    print(f"Model: {MODEL}")
    print("\nStarting web interface...")
    print("="*60 + "\n")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True,
        theme=gr.themes.Soft()
    )