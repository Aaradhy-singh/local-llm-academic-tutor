"""
Enhanced Academic Tutor with UI, Speed, and Output improvements
"""

import gradio as gr
from openai import OpenAI
import json
from datetime import datetime
from typing import Optional
import asyncio
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import os

# ============ CONFIGURATION ============
SETTINGS_FILE = 'tutor_settings.json'

DEFAULT_CONFIG = {
    'ollama_url': 'http://localhost:11434/v1',
    'model': 'phi3:mini',
    'max_memory': 4,
    'temperature': 0.3,
    'buffer_size': 256,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_settings(config):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

CONFIG = load_settings()

# ============ ENHANCED SYSTEM PROMPTS ============
SYSTEM_PROMPTS = {
    'default': """You are a local inference-only language model running via Ollama.

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
""",
    
    'detailed': """You are an educational assistant providing comprehensive explanations.
- Break complex topics into steps
- Use clear, structured formatting
- Include examples when helpful
- Explain the "why" behind concepts
- Provide detailed rationale and context where appropriate.
""",
    
    'fast': """Answer quickly and concisely.
- Provide only the essential answer
- Minimize explanation unless asked
- Use short sentences
- Get to the point immediately
- Limit your responses to the absolute minimum necessary words.
"""
}

# ============ CORE ENHANCED FUNCTIONS ============

class EnhancedTutor:
    def __init__(self, config=CONFIG):
        self.config = config
        self.client = OpenAI(
            base_url=config['ollama_url'],
            api_key="not-needed"
        )
        self.conversation_history = []
        self.session_metadata = {
            'created': datetime.now().isoformat(),
            'messages_count': 0,
            'performance_metrics': []
        }
    
    def detect_query_type(self, question: str) -> str:
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
    
    def get_optimal_params(self, question: str) -> dict:
        """Get temperature and parameters based on question"""
        query_type = self.detect_query_type(question)
        
        params_map = {
            'math': {'temperature': 0.2, 'max_tokens': 300},
            'code': {'temperature': 0.1, 'max_tokens': 400},
            'detailed': {'temperature': 0.4, 'max_tokens': 500},
            'default': {'temperature': 0.3, 'max_tokens': 200}
        }
        
        return params_map.get(query_type, params_map['default'])
    
    def format_system_prompt(self, mode: str = 'default') -> str:
        """Get appropriate system prompt"""
        return SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS['default'])
    
    def ask(self, question: str, history: list, mode: str = 'default', model: str = None, max_memory: int = 6):
        """Main ask function with enhancements"""
        
        # Build message list
        messages = [{"role": "system", "content": self.format_system_prompt(mode)}]
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        
        # Trim memory
        if len(messages) > max_memory * 2 + 2:
            messages = [messages[0]] + messages[-max_memory*2:]
        
        # Get optimal parameters
        params = self.get_optimal_params(question)
        
        # Generate response
        try:
            response = self.client.chat.completions.create(
                model=model or self.config['model'],
                messages=messages,
                stream=True,
                **params
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    # Yield raw text during the stream for maximum speed
                    yield full_response
            
            # Phase 3: Format code blocks via Pygments POST-stream
            formatted_response = self.format_code_in_response(full_response)
            
            # Phase 4: Append static disclaimer
            meta_append = "\n\n---\n*Verify all STEM answers from an authoritative source before using them.*"
                
            formatted_response += meta_append
            yield formatted_response
            
            # Update history and metadata internally
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            self.session_metadata['messages_count'] += 2
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def format_code_in_response(self, text: str) -> str:
        """Detect and format code blocks with syntax highlighting"""
        pattern = r'```(\w+)?\n(.*?)```'
        
        def replace_code(match):
            lang = match.group(1) or 'python'
            code = match.group(2)
            try:
                lexer = get_lexer_by_name(lang)
                formatter = HtmlFormatter(style='monokai')
                highlighted = highlight(code, lexer, formatter)
                return f'<div class="code-block">{highlighted}</div>'
            except:
                return f'<pre><code>{code}</code></pre>'
        
        return re.sub(pattern, replace_code, text, flags=re.DOTALL)
        
    def suggest_follow_ups(self, text: str, question: str, model: str) -> str:
        """Generate helpful follow-up questions"""
        follow_up_prompt = f"Given the question: '{question}' and answer: '{text[:200]}...', suggest 2 natural follow-up questions. Format as short bullet points."
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": follow_up_prompt}],
                max_tokens=60,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except:
            return ""
    
    def export_conversation(self) -> str:
        """Export conversation as JSON"""
        if not self.conversation_history:
            return "{}"
        
        export_data = {
            'metadata': self.session_metadata,
            'conversation': self.conversation_history
        }
        
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            return filename
        except Exception as e:
            print(f"Failed to write file: {e}")
            return None


# ============ GRADIO INTERFACE ============

def create_enhanced_ui():
    """Create enhanced Gradio interface"""
    
    tutor = EnhancedTutor()
    
    custom_css = """
    .code-block {
        background-color: #272822; /* Monokai background */
        border: 1px solid #ddd;
        padding: 12px;
        border-radius: 4px;
        overflow-x: auto;
    }
    """
    
    with gr.Blocks(theme=gr.themes.Soft(), title="Enhanced Academic Tutor", css=custom_css) as demo:
        
        gr.Markdown("""
        # 🎓 Enhanced Academic Tutor
        **Local AI • Zero Cost • Fully Private**
        """)
        
        with gr.Tabs():
            # ===== TAB 1: CHAT =====
            with gr.TabItem("💬 Chat"):
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            height=500,
                            label="Conversation",
                            show_label=True
                        )
                    with gr.Column(scale=1):
                        mode_radio = gr.Radio(
                            ["Quick", "Detailed", "Step-by-Step"],
                            value="Quick",
                            label="Response Mode",
                            info="How much detail?"
                        )
                
                msg = gr.Textbox(
                    placeholder="Ask a question...",
                    show_label=False,
                    scale=4
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Send", scale=1)
                    clear_btn = gr.Button("Clear", scale=1)
                
                with gr.Row():
                    followup_btn = gr.Button("💡 Suggest Follow-ups", variant="secondary")
            
            # ===== TAB 2: SETTINGS =====
            with gr.TabItem("⚙️ Settings"):
                gr.Markdown("### Tutor Parameters")
                
                with gr.Row():
                    temp_slider = gr.Slider(
                        0.0, 1.0,
                        value=tutor.config.get('temperature', 0.3),
                        step=0.1,
                        label="Temperature (Randomness)"
                    )
                    memory_slider = gr.Slider(
                        2, 20,
                        value=tutor.config.get('max_memory', 4),
                        step=1,
                        label="Memory Window"
                    )
                
                model_dropdown = gr.Dropdown(
                    ["phi3:mini", "llama3.2", "mistral"],
                    value=tutor.config.get('model', 'phi3:mini'),
                    label="Model Selection"
                )
                
                save_btn = gr.Button("Save Settings")
                save_status = gr.Markdown("")
                
            # ===== TAB 3: HISTORY & EXPORT =====
            with gr.TabItem("📊 History"):
                gr.Markdown("Export your chat history as JSON to review offline.")
                
                with gr.Row():
                    export_json_btn = gr.Button("Export as JSON")
                    download_file = gr.File(label="Download File")
            
            # ===== TAB 4: HELP =====
            with gr.TabItem("❓ Help"):
                gr.Markdown("""
                ## How to Use
                
                1. **Ask Questions**: Type academic questions about math, science, CS, etc.
                2. **Choose Mode**:
                   - Quick: Fast, concise answers
                   - Detailed: Comprehensive explanations
                   - Step-by-Step: Show working for math/logic
                
                ## Example Questions
                - What is photosynthesis?
                - How does quicksort work?
                - Solve: 2x² + 5x - 3 = 0
                - Explain quantum entanglement
                
                ## Tips
                - Be specific in your questions
                - Ask follow-ups to dig deeper
                - Export conversations for study
                """)
        
        # ===== EVENT HANDLERS =====
        
        def generate_followups(history, model_val):
            if not history or len(history) < 2:
                return history
                
            last_user = history[-2]["content"] if len(history) >= 2 else ""
            last_bot = history[-1]["content"] if len(history) >= 1 else ""
            
            if not last_user or not last_bot:
                return history
                
            followups = tutor.suggest_follow_ups(last_bot, last_user, model_val)
            
            if followups:
                # Append to the latest assistant message
                appended_text = last_bot + f"\n\n**Suggested Follow-ups:**\n{followups}"
                updated_history = history[:-1] + [{"role": "assistant", "content": appended_text}]
                return updated_history
            return history
            
        def update_response_mode(mode):
            mode_map = {
                'Quick': 'default',
                'Detailed': 'detailed',
                'Step-by-Step': 'detailed'
            }
            return mode_map.get(mode, 'default')
        
        def chat_function(message, history, mode, model_val, memory_val):
            if not message:
                return
            
            mode_key = update_response_mode(mode)
            
            if history is None:
                history = []
                
            # Add user message
            new_history = history + [{"role": "user", "content": message}]
            
            # Get streaming response
            for response_chunk in tutor.ask(
                    question=message, 
                    history=new_history[:-1], 
                    mode=mode_key,
                    model=model_val,
                    max_memory=int(memory_val)):
                
                updated_history = new_history.copy()
                updated_history.append({"role": "assistant", "content": response_chunk})
                yield updated_history
        
        # Wire up submit button and Enter key
        msg.submit(
            chat_function,
            [msg, chatbot, mode_radio, model_dropdown, memory_slider],
            chatbot
        ).then(lambda: "", None, msg)
        
        submit_btn.click(
            chat_function,
            [msg, chatbot, mode_radio, model_dropdown, memory_slider],
            chatbot
        ).then(lambda: "", None, msg)
        
        # Follow-up button
        followup_btn.click(
            generate_followups,
            [chatbot, model_dropdown],
            chatbot
        )
        
        # Clear button
        def clear_history():
            tutor.conversation_history = []
            return []
            
        clear_btn.click(clear_history, None, chatbot)
        
        # Save Settings
        def handle_save_settings(temp, mem, mod):
            new_config = tutor.config.copy()
            new_config['temperature'] = temp
            new_config['max_memory'] = int(mem)
            new_config['model'] = mod
            tutor.config = new_config
            if save_settings(new_config):
                return "✅ Settings saved successfully!"
            return "❌ Failed to save settings."
            
        save_btn.click(
            handle_save_settings,
            [temp_slider, memory_slider, model_dropdown],
            save_status
        )
        
        # Export functionality
        def export_json():
            filename = tutor.export_conversation()
            return filename if filename else None
        
        export_json_btn.click(export_json, outputs=download_file)
    
    return demo

# ============ MAIN =====
if __name__ == "__main__":
    demo = create_enhanced_ui()
    
    print("\n" + "="*60)
    print("  Enhanced Academic Tutor")
    print("="*60)
    print("Model: phi3:mini")
    print("Interface: Gradio Web UI")
    print("\nLaunching on port 7861")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        theme=gr.themes.Soft()
    )