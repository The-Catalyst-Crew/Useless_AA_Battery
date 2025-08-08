"""
Main Gradio application for the AI persona generation and interaction interface.
"""
import gradio as gr
import requests
import base64
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add the parent directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.settings_page import create_settings_page
from config import settings

# API configuration - Using localhost for better compatibility
API_BASE_URL = f"http://localhost:{settings.API_PORT}"

# Global variables to store the current persona, model, and conversation
current_persona = None
current_model = None
conversation_history = []

# Cache for available models and personalities
available_models = []
available_personalities = []

# No authentication needed for local development

def fetch_models() -> List[Dict[str, Any]]:
    """Fetch available models from the API."""
    global available_models
    try:
        # First try to get models from OpenRouter directly
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        response.raise_for_status()
        
        # Process the models
        models_data = response.json().get("data", [])
        available_models = []
        
        for model in models_data:
            try:
                # Ensure model has required architecture info
                architecture = model.get("architecture", {})
                input_modalities = architecture.get("input_modalities", [])
                
                # Skip if model doesn't support image input
                if not any(modality in ["image", "images", "image_input"] for modality in input_modalities):
                    continue
                    
                # Get pricing details
                pricing = model.get("pricing", {})
                available_models.append({
                    "id": model.get("id"),
                    "name": model.get("name"),
                    "description": model.get("description", ""),
                    "context_length": model.get("context_length"),
                    "is_free": (
                        pricing.get("prompt") == "0" and 
                        pricing.get("completion") == "0" and
                        pricing.get("image", "0") == "0"
                    ),
                    "pricing": {
                        "prompt": pricing.get("prompt", "0"),
                        "completion": pricing.get("completion", "0"),
                        "image": pricing.get("image", "0")
                    },
                    "capabilities": {
                        "input_modalities": input_modalities,
                        "output_modalities": architecture.get("output_modalities", [])
                    }
                })
                
            except Exception as e:
                print(f"Error processing model {model.get('id')}: {str(e)}")
                continue
        
        # Sort models: free first, then by name, and ensure we only have unique models
        unique_models = {}
        for model in available_models:
            model_id = model.get("id")
            if model_id and model_id not in unique_models:
                unique_models[model_id] = model
        
        available_models = list(unique_models.values())
        available_models.sort(key=lambda x: (not x["is_free"], x["name"]))
        
        return available_models
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch models: {str(e)}"
        if "ConnectionError" in str(e):
            error_msg = "Failed to connect to the backend server. Please make sure it's running."
        print(error_msg)
        return []
    except Exception as e:
        print(f"Error processing models: {str(e)}")
        return []

def fetch_personalities() -> List[Dict[str, Any]]:
    """Fetch available personalities from the API."""
    global available_personalities
    try:
        response = requests.get(
            f"{API_BASE_URL}{settings.PERSONA_ENDPOINT}/list",
            timeout=5
        )
        response.raise_for_status()
        available_personalities = response.json()
        return available_personalities
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch personalities: {str(e)}"
        if "ConnectionError" in str(e):
            error_msg = "Failed to connect to the backend server. Please make sure it's running."
        print(error_msg)
        available_personalities = []
        return available_personalities
    except Exception as e:
        error_msg = f"Unexpected error fetching personalities: {str(e)}"
        print(error_msg)
        available_personalities = []
        return available_personalities

def create_persona(name: str, description: str, system_prompt: str) -> Dict[str, Any]:
    """Create a new persona via the API."""
    try:
        # Create a basic persona with default traits
        persona_data = {
            "name": name,
            "description": description,
            "traits": {
                "personality": "Friendly and helpful AI assistant",
                "interests": ["helping users", "answering questions"],
                "communication_style": "friendly and professional",
                "knowledge_domain": "general",
                "system_prompt": system_prompt
            },
            "image_base64": None,  # Add missing required field
            "object_name": None    # Add missing required field
        }
        
        response = requests.post(
            f"{API_BASE_URL}{settings.PERSONA_ENDPOINT}/create",
            json=persona_data,
            timeout=5
        )
        response.raise_for_status()
        
        # Refresh the personalities list after creation
        fetch_personalities()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to create persona: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f"\nDetails: {error_detail}"
            except (ValueError, AttributeError):
                error_msg += f"\nResponse: {e.response.text}"
            error_msg += f" (Status: {e.response.status_code})"
        print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error creating persona: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def analyze_image(image_data: str, personality_examples: str) -> Tuple[Dict, str]:
    """Send image and personality examples to the API for analysis."""
    global current_persona
    
    # Convert image to base64 if it's a file path
    if isinstance(image_data, str) and os.path.exists(image_data):
        with open(image_data, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    payload = {
        "image_base64": image_data,
        "personality_examples": personality_examples
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{settings.PERSONA_ENDPOINT}/create",
            json=payload
        )
        response.raise_for_status()
        current_persona = response.json()
        return current_persona, "Persona created successfully!"
    except Exception as e:
        return None, f"Error creating persona: {str(e)}"

def send_message(message: str, model_id: str, persona_name: str) -> Tuple[str, List[Dict]]:
    """Send a message to the chat and get a response."""
    global current_persona, conversation_history, available_personalities
    
    # Find the selected persona
    selected_persona = next((p for p in available_personalities 
                           if p.get("name") == persona_name), None)
    
    if not selected_persona:
        return "Please select a valid persona first.", conversation_history
    
    # Set the current persona
    current_persona = selected_persona
    
    # Add user message to conversation history
    conversation_history.append({"role": "user", "content": message})
    
    try:
        # Call the chat API
        response = requests.post(
            f"{API_BASE_URL}{settings.CHAT_ENDPOINT}/chat",
            json={
                "message": message,
                "model": model_id,
                "persona_id": current_persona.get("id"),
                "conversation_history": conversation_history
            }
        )
        response.raise_for_status()
        
        # Get the AI response
        response_data = response.json()
        ai_response = response_data.get("response", "Sorry, I couldn't generate a response.")
        
        # Update conversation history
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        return "", conversation_history
        
    except Exception as e:
        error_msg = f"Error sending message: {str(e)}"
        print(error_msg)
        return error_msg, conversation_history

def generate_image(prompt: str):
    """Generate an image based on the given prompt."""
    global current_persona
    
    if not current_persona:
        return None, "Please create a persona first!"
    
    try:
        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "persona": current_persona,
            "model": settings.DEFAULT_IMAGE_MODEL,
            "steps": settings.DEFAULT_SD_STEPS,
            "cfg_scale": settings.DEFAULT_SD_CFG_SCALE,
            "width": settings.DEFAULT_SD_WIDTH,
            "height": settings.DEFAULT_SD_HEIGHT
        }
        
        # Send the request to the image generation endpoint
        response = requests.post(
            f"{API_BASE_URL}{settings.IMAGE_ENDPOINT}/generate",
            json=payload
        )
        response.raise_for_status()
        
        # Get the generated image
        response_data = response.json()
        image_base64 = response_data.get("image_base64")
        
        if not image_base64:
            return None, "No image was generated."
        
        # Convert base64 to image
        image_data = base64.b64decode(image_base64)
        return image_data, "Image generated successfully!"
    except Exception as e:
        return None, f"Error generating image: {str(e)}"

def create_ui():
    """Create the Gradio UI components."""
    # Initialize components first
    with gr.Blocks(title="AI Persona Chat") as demo:
        # Add a hidden textbox for error messages
        error_display = gr.Textbox(visible=False, interactive=False, label="Error")
        
        # Create a function to show error messages
        def show_error(message: str):
            return gr.Textbox(value=message, visible=True, interactive=False)
        
        # Create a function to hide error messages
        def hide_error():
            return gr.Textbox(visible=False)
        gr.Markdown("# AI Persona Chat")
        
        with gr.Row():
            # Left column for persona creation and settings
            with gr.Column(scale=1):
                # Model Selection
                with gr.Accordion("Model Settings", open=True):
                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            label="Select Model",
                            choices=[],
                            interactive=True,
                            value=None,
                            scale=4
                        )
                        refresh_models_btn = gr.Button("🔄", size="sm", scale=1)
                    
                    # Model info display
                    model_info = gr.Markdown("*No model selected*", label="Model Details")
                    
                    # Function to update model info when selection changes
                    def update_model_info(model_id: str) -> str:
                        if not model_id:
                            return "*No model selected*"
                            
                        # Find the selected model
                        selected_model = next((m for m in available_models if m["id"] == model_id), None)
                        if not selected_model:
                            return "*Model information not available*"
                            
                        # Format model info
                        info = f"**{selected_model['name']}**\n"
                        info += f"*ID*: `{selected_model['id']}`\n\n"
                        
                        # Add description if available
                        if selected_model.get('description'):
                            info += f"{selected_model['description']}\n\n"
                            
                        # Add capabilities
                        info += "**Capabilities**\n"
                        caps = selected_model.get('capabilities', {})
                        if 'input_modalities' in caps:
                            info += f"- Inputs: {', '.join(caps['input_modalities'])}\n"
                        if 'output_modalities' in caps:
                            info += f"- Outputs: {', '.join(caps['output_modalities'])}\n"
                            
                        # Add pricing info
                        info += "\n**Pricing**\n"
                        pricing = selected_model.get('pricing', {})
                        if pricing.get('prompt') == '0' and pricing.get('completion') == '0':
                            info += "- Free to use! 🎉\n"
                        else:
                            if 'prompt' in pricing and pricing['prompt'] != '0':
                                info += f"- Input: ${float(pricing['prompt']):.7f} per token\n"
                            if 'completion' in pricing and pricing['completion'] != '0':
                                info += f"- Output: ${float(pricing['completion']):.7f} per token\n"
                            if 'image' in pricing and pricing['image'] != '0':
                                info += f"- Image: ${float(pricing['image']):.2f} per image\n"
                                
                        # Add context length
                        if selected_model.get('context_length'):
                            info += f"\n**Context Length**: {selected_model['context_length']} tokens"
                            
                        return info
                    
                    # Update model info when selection changes
                    model_dropdown.change(
                        fn=update_model_info,
                        inputs=[model_dropdown],
                        outputs=[model_info]
                    )
                
                # Persona Selection
                with gr.Accordion("Persona Selection", open=True):
                    persona_dropdown = gr.Dropdown(
                        label="Select Personality",
                        choices=[],
                        interactive=True,
                        value=None
                    )
                    refresh_personas_btn = gr.Button("🔄", size="sm")
                
                # Persona Creation
                with gr.Accordion("Create New Persona", open=False):
                    with gr.Row():
                        image_input = gr.Image(label="Upload an image", type="filepath")
                        personality_examples = gr.Textbox(
                            label="Personality Examples",
                            placeholder="Describe the personality traits or provide examples...",
                            lines=5
                        )
                    
                    create_btn = gr.Button("Create Persona", variant="primary")
                    persona_status = gr.Textbox(label="Status", interactive=False)
                    
                    gr.Markdown("## Current Persona")
                    persona_display = gr.JSON(label="Persona Details")
                
                # Refresh buttons handlers with error handling
                def refresh_models():
                    try:
                        models = fetch_models()
                        if not models:
                            return (
                                {"__type__": "update", "choices": [], "value": None},
                                show_error("No models available. Please check your connection and API key."),
                                "*No models available*"
                            )
                        
                        # Format model names with free indicator
                        choices = []
                        for model in models:
                            name = model["name"]
                            if model.get("is_free"):
                                name += " 🆓"  # Add free indicator
                            choices.append((name, model["id"]))  # (display, value)
                        
                        value = models[0]["id"] if models else None
                        
                        # Get info for the first model if available
                        model_info = update_model_info(value) if value else "*Select a model*"
                        
                        return (
                            {"__type__": "update", "choices": choices, "value": value},
                            hide_error(),
                            model_info
                        )
                    except Exception as e:
                        return (
                            {"__type__": "update", "choices": [], "value": None},
                            show_error(f"Error loading models: {str(e)}"),
                            "*Error loading model information*"
                        )
                
                def refresh_personas():
                    try:
                        personas = fetch_personalities()
                        if not personas:
                            return (
                                {"__type__": "update", "choices": [], "value": None},
                                show_error("No personas available. Please create one first.")
                            )
                        choices = [p.get("name", "Unnamed") for p in personas]
                        value = choices[0] if choices else None
                        return (
                            {"__type__": "update", "choices": choices, "value": value},
                            hide_error()
                        )
                    except Exception as e:
                        return (
                            {"__type__": "update", "choices": [], "value": None},
                            show_error(f"Error loading personas: {str(e)}")
                        )
                
                # Set up refresh buttons
                refresh_models_btn.click(
                    fn=refresh_models,
                    inputs=[],
                    outputs=[model_dropdown, error_display, model_info]
                )
                
                refresh_personas_btn.click(
                    fn=refresh_personas,
                    inputs=[],
                    outputs=[persona_dropdown, error_display]
                )
                
                # Initial load of models and personas
                demo.load(
                    fn=refresh_models,
                    inputs=[],
                    outputs=[model_dropdown, error_display, model_info]
                )
                
                demo.load(
                    fn=refresh_personas,
                    inputs=[],
                    outputs=[persona_dropdown, error_display]
                )
            
            # Right column for chat
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Conversation")
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Type a message...",
                        placeholder="What would you like to say?",
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary")
                
                with gr.Accordion("Image Generation", open=False):
                    image_prompt = gr.Textbox(
                        label="Prompt for Image Generation",
                        placeholder="Describe the image you want to generate..."
                    )
                    generate_btn = gr.Button("Generate Image")
                    generated_image = gr.Image(label="Generated Image")
                    image_status = gr.Textbox(label="Status", interactive=False)
        
        # Event handlers
        create_btn.click(
            fn=analyze_image,
            inputs=[image_input, personality_examples],
            outputs=[persona_display, persona_status]
        ).then(
            fn=refresh_personas,
            outputs=persona_dropdown
        )
        
        def process_message(message: str, model: str, persona: str):
            # This function will be called when the user submits a message
            # It returns a tuple of (message, model, persona) to be used by send_message
            return message, model, persona
            
        def clear_message(message: str):
            # This function clears the message input after submission
            return ""
            
        # Handle message submission via Enter key
        msg.submit(
            fn=process_message,
            inputs=[msg, model_dropdown, persona_dropdown],
            outputs=[msg, model_dropdown, persona_dropdown],
            queue=False
        ).then(
            fn=send_message,
            inputs=[msg, model_dropdown, persona_dropdown],
            outputs=[msg, chatbot]
        ).then(
            fn=clear_message,
            inputs=[msg],
            outputs=[msg],
            queue=False
        )
        
        # Handle message submission via Send button
        submit_btn.click(
            fn=process_message,
            inputs=[msg, model_dropdown, persona_dropdown],
            outputs=[msg, model_dropdown, persona_dropdown],
            queue=False
        ).then(
            fn=send_message,
            inputs=[msg, model_dropdown, persona_dropdown],
            outputs=[msg, chatbot]
        ).then(
            fn=clear_message,
            inputs=[msg],
            outputs=[msg],
            queue=False
        )
        
        generate_btn.click(
            fn=generate_image,
            inputs=image_prompt,
            outputs=[generated_image, image_status]
        )
    
    return demo

def main(server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False):
    """Initialize and launch the Gradio UI.
    
    Args:
        server_name: The server name to use (default: "0.0.0.0")
        server_port: The port to run the server on (default: 7860)
        share: Whether to create a public link (default: False)
    """
    with gr.Blocks(title="AI Persona Chat") as app:
        with gr.Tabs():
            with gr.Tab("Chat"):
                create_ui()
            
            with gr.Tab("Settings"):
                create_settings_page()
    
    app.launch(server_name=server_name, server_port=server_port, share=share)

if __name__ == "__main__":
    main()
