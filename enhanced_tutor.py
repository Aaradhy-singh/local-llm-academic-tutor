import gradio as gr
import json

class EnhancedTutor:
    def __init__(self):
        self.conversation_history = []
        self.settings = {
            'response_mode': 'standard',
            'temperature': 0.7,
        }

    def chat(self, input_text):
        # Simulate a chat response
        response = f"You said: {input_text}\nResponse based on temperature: {self.settings['temperature']}"
        self.conversation_history.append({'user': input_text, 'bot': response})
        return response

    def export_conversation(self):
        with open('conversation_history.json', 'w') as f:
            json.dump(self.conversation_history, f)

    def update_settings(self, new_settings):
        self.settings.update(new_settings)

# Initialize the tutor
enhanced_tutor = EnhancedTutor()

# Gradio Interface
with gr.Interface(
    fn=enhanced_tutor.chat,
    inputs=gr.Textbox(label="Enter your message:"),
    outputs=gr.Textbox(label="Response:"),
) as interface:
    interface.add_component(gr.Dropdown(label="Response Mode:", choices=['standard', 'detailed', 'brief'], value='standard'))
    interface.add_component(gr.Slider(label="Temperature control:", minimum=0.0, maximum=1.0, value=0.7, step=0.1))
    interface.add_component(gr.Button(label="Export Conversation", elem_id="export_btn"))

    # Allow the export button to trigger conversation export
    def export():
        enhanced_tutor.export_conversation()
        return "Conversation exported!"

    interface.add_function(export, inputs=[], outputs=gr.Textbox(label="Export Status:"))

interface.launch()