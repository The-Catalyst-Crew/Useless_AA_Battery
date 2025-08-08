"""
Settings page for the AI Persona Generation and Interaction application.
"""
import gradio as gr
from pathlib import Path
import os
import sys

# Add the parent directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

def create_settings_page():
    """Create the settings page UI."""
    with gr.Blocks(title="Settings") as settings_page:
        gr.Markdown("# Settings")
        
        with gr.Tabs():
            with gr.TabItem("API Configuration"):
                gr.Markdown("### External API Keys")
                with gr.Row():
                    openrouter_key = gr.Textbox(
                        label="OpenRouter API Key",
                        value=settings.OPENROUTER_API_KEY or "",
                        type="password"
                    )
                    sd_key = gr.Textbox(
                        label="Stable Diffusion API Key",
                        value=settings.STABLE_DIFFUSION_API_KEY or "",
                        type="password"
                    )
                
                gr.Markdown("### Server Configuration")
                with gr.Row():
                    api_host = gr.Textbox(
                        label="API Host",
                        value=settings.API_HOST,
                        placeholder="0.0.0.0"
                    )
                    api_port = gr.Number(
                        label="API Port",
                        value=settings.API_PORT,
                        precision=0
                    )
                    frontend_port = gr.Number(
                        label="Frontend Port",
                        value=settings.FRONTEND_PORT,
                        precision=0
                    )
                
            with gr.TabItem("Model Settings"):
                with gr.Row():
                    chat_model = gr.Dropdown(
                        label="Default Chat Model",
                        choices=["gpt-4", "gpt-3.5-turbo", "claude-2", "llama-2-70b-chat"],
                        value=settings.DEFAULT_CHAT_MODEL
                    )
                    image_model = gr.Dropdown(
                        label="Default Image Generation Model",
                        choices=["stabilityai/stable-diffusion-2-1", "runwayml/stable-diffusion-v1-5", "CompVis/stable-diffusion-v1-4"],
                        value=settings.DEFAULT_IMAGE_MODEL
                    )
                
                gr.Markdown("### Image Generation Settings")
                with gr.Row():
                    sd_steps = gr.Slider(
                        minimum=10, 
                        maximum=100, 
                        step=5, 
                        value=settings.DEFAULT_SD_STEPS, 
                        label="Default Steps"
                    )
                    sd_cfg_scale = gr.Slider(
                        minimum=1.0, 
                        maximum=20.0, 
                        step=0.5, 
                        value=settings.DEFAULT_SD_CFG_SCALE, 
                        label="Default CFG Scale"
                    )
                with gr.Row():
                    sd_width = gr.Slider(
                        minimum=256, 
                        maximum=1024, 
                        step=64, 
                        value=settings.DEFAULT_SD_WIDTH, 
                        label="Default Width"
                    )
                    sd_height = gr.Slider(
                        minimum=256, 
                        maximum=1024, 
                        step=64, 
                        value=settings.DEFAULT_SD_HEIGHT, 
                        label="Default Height"
                    )
        
        save_btn = gr.Button("Save Settings", variant="primary")
        status = gr.Textbox(label="Status", interactive=False, visible=True)
        
        def load_settings():
            """Load current settings from environment."""
            return {
                openrouter_key: settings.OPENROUTER_API_KEY or "",
                sd_key: settings.STABLE_DIFFUSION_API_KEY or "",
                api_host: settings.API_HOST,
                api_port: settings.API_PORT,
                frontend_port: settings.FRONTEND_PORT,
                chat_model: settings.DEFAULT_CHAT_MODEL,
                image_model: settings.DEFAULT_IMAGE_MODEL,
                sd_steps: settings.DEFAULT_SD_STEPS,
                sd_cfg_scale: settings.DEFAULT_SD_CFG_SCALE,
                sd_width: settings.DEFAULT_SD_WIDTH,
                sd_height: settings.DEFAULT_SD_HEIGHT
            }
        
        def save_settings(
            openrouter_key_val,
            sd_key_val,
            api_host_val,
            api_port_val,
            frontend_port_val,
            chat_model_val,
            image_model_val,
            steps_val,
            cfg_scale_val,
            width_val,
            height_val
        ):
            """Save settings to .env file."""
            try:
                env_path = Path(__file__).parent.parent / ".env"
                
                # Prepare environment variables
                env_vars = {
                    'API_HOST': api_host_val,
                    'API_PORT': str(int(api_port_val)),
                    'FRONTEND_PORT': str(int(frontend_port_val)),
                    'OPENROUTER_API_KEY': openrouter_key_val,
                    'STABLE_DIFFUSION_API_KEY': sd_key_val,
                    'DEFAULT_CHAT_MODEL': chat_model_val,
                    'DEFAULT_IMAGE_MODEL': image_model_val,
                    'DEFAULT_SD_STEPS': str(int(steps_val)),
                    'DEFAULT_SD_CFG_SCALE': str(float(cfg_scale_val)),
                    'DEFAULT_SD_WIDTH': str(int(width_val)),
                    'DEFAULT_SD_HEIGHT': str(int(height_val)),
                    'SECRET_KEY': settings.SECRET_KEY,  # Keep existing secret key
                    'ALGORITHM': settings.ALGORITHM,    # Keep existing algorithm
                    'ACCESS_TOKEN_EXPIRE_MINUTES': str(settings.ACCESS_TOKEN_EXPIRE_MINUTES)  # Keep existing token expiry
                }
                
                # Write to .env file
                with open(env_path, 'w') as f:
                    for key, value in env_vars.items():
                        if value is not None:  # Only write non-None values
                            f.write(f"{key}={value}\n")
                
                return "Settings saved successfully! Please restart the application for changes to take effect."
            except Exception as e:
                return f"Error saving settings: {str(e)}"
        
        # Set up event handlers
        save_btn.click(
            fn=save_settings,
            inputs=[
                openrouter_key,
                sd_key,
                api_host,
                api_port,
                frontend_port,
                chat_model,
                image_model,
                sd_steps,
                sd_cfg_scale,
                sd_width,
                sd_height
            ],
            outputs=status
        )
        
        # Load settings when page loads
        settings_page.load(
            fn=load_settings,
            outputs=[
                openrouter_key,
                sd_key,
                api_host,
                api_port,
                frontend_port,
                chat_model,
                image_model,
                sd_steps,
                sd_cfg_scale,
                sd_width,
                sd_height
            ]
        )
    
    return settings_page