"""
Utility for generating AI personalities using GLM-4.5-Air model via OpenRouter.
"""
import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from openai import OpenAI
from config import settings

# Directory to store personality JSON files
PERSONALITIES_DIR = Path("data/personalities")
PERSONALITIES_DIR.mkdir(parents=True, exist_ok=True)

class PersonalityGenerator:
    """Handles generation and management of AI personalities."""
    
    def __init__(self):
        """Initialize the OpenAI client with OpenRouter configuration."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
        
    def _generate_personality_prompt(self, object_name: str, image_description: str) -> str:
        """Generate a prompt for creating a personality based on an object."""
        return f"""Create a detailed system prompt for an AI that gives {object_name} a unique personality. 
        The AI should have a distinct voice, mannerisms, and backstory that fits {object_name}.
        
        Here's a description of the {object_name}:
        {image_description}
        
        Your response should ONLY include the system prompt content, without any additional text or formatting. 
        The prompt should be in the second person ("You are...") and describe the AI's personality, 
        communication style, and any special knowledge or abilities it has.
        
        Example format (but make it unique to {object_name}):
        "You are a {object_name} with a quirky personality. You love to [describe personality traits]..."
        """
    
    def generate_personality(self, object_name: str, image_description: str) -> Dict:
        """
        Generate a personality for the given object using GLM-4.5-Air.
        
        Args:
            object_name: Name of the object to create a personality for
            image_description: Description of the object's appearance
            
        Returns:
            Dict containing the generated personality information
        """
        try:
            # Generate the personality prompt
            system_prompt = self._generate_personality_prompt(object_name, image_description)
            
            # Call the OpenRouter API
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "AI Persona Generator",
                },
                model="z-ai/glm-4.5-air:free",
                messages=[
                    {"role": "system", "content": "You are a creative AI that generates unique and engaging personalities for objects."},
                    {"role": "user", "content": system_prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            # Extract the generated personality
            personality_content = completion.choices[0].message.content.strip()
            
            # Create personality data structure
            personality_data = {
                "name": object_name,
                "system_prompt": personality_content,
                "description": f"A personality for {object_name} generated based on its appearance.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "model": "z-ai/glm-4.5-air:free"
            }
            
            # Save to JSON file
            self._save_personality(personality_data)
            
            return personality_data
            
        except Exception as e:
            print(f"Error generating personality: {str(e)}")
            raise
    
    def _save_personality(self, personality_data: Dict) -> str:
        """
        Save personality data to a JSON file.
        
        Args:
            personality_data: Dictionary containing personality information
            
        Returns:
            Path to the saved file
        """
        # Create a safe filename from the object name
        safe_name = "".join(c if c.isalnum() else "_" for c in personality_data["name"]).lower()
        file_path = PERSONALITIES_DIR / f"{safe_name}.json"
        
        # If file exists, load and update it, otherwise create new
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
                existing_data.append(personality_data)
                personality_data = existing_data
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(personality_data, f, indent=2, ensure_ascii=False)
        
        return str(file_path)
    
    def get_personality(self, object_name: str) -> Optional[Dict]:
        """
        Retrieve a saved personality by object name.
        
        Args:
            object_name: Name of the object to retrieve
            
        Returns:
            Dictionary with personality data or None if not found
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in object_name).lower()
        file_path = PERSONALITIES_DIR / f"{safe_name}.json"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_personalities(self) -> List[str]:
        """List all available personality files."""
        return [f.stem for f in PERSONALITIES_DIR.glob("*.json")]
    
    @staticmethod
    def get_free_models_with_image_support() -> List[Dict[str, Any]]:
        """
        Fetch a list of models from OpenRouter that support image inputs.
        
        Returns:
            List of dictionaries containing model information with pricing details
        """
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            response.raise_for_status()
            
            models_data = response.json().get("data", [])
            
            # Filter for models that support image inputs
            image_models = []
            for model in models_data:
                try:
                    # Check if model supports image inputs
                    architecture = model.get("architecture", {})
                    input_modalities = architecture.get("input_modalities", [])
                    
                    if "image" not in input_modalities:
                        continue
                        
                    # Get pricing information
                    pricing = model.get("pricing", {})
                    
                    # Format model information
                    model_info = {
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
                    }
                    
                    image_models.append(model_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing model {model.get('id')}: {str(e)}")
                    continue
            
            # Sort models: free first, then by name
            image_models.sort(key=lambda x: (not x["is_free"], x["name"]))
            
            return image_models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching models from OpenRouter: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return []

# Example usage
if __name__ == "__main__":
    generator = PersonalityGenerator()
    
    # Example: Generate a personality for a coffee mug
    object_name = "coffee mug"
    image_description = "A plain white ceramic coffee mug with a small chip on the handle."
    
    try:
        personality = generator.generate_personality(object_name, image_description)
        print(f"Generated personality for {object_name}:")
        print(json.dumps(personality, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
