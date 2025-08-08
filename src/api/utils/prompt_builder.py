"""
Utility functions for building and managing prompts for AI models.
"""
from typing import Dict, Any, List, Optional

class PromptBuilder:
    """Builds and manages prompts for AI interactions."""
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the prompt builder.
        
        Args:
            template_path: Optional path to load prompt templates from
        """
        self.templates = {
            "default": "{instruction}\n\nContext:\n{context}\n\nResponse:",
            "persona_generation": "Create a detailed persona based on the following analysis:\n{analysis}\n\nPersona:",
            "chat_response": "You are {persona_name}. {persona_description}\n\nCurrent conversation:\n{history}\n\nUser: {message}\n{persona_name}:"
        }
        
        if template_path:
            self.load_templates(template_path)
    
    def load_templates(self, template_path: str) -> None:
        """Load templates from a file."""
        # TODO: Implement template loading from file
        pass
    
    def build_prompt(
        self,
        template_name: str,
        variables: Dict[str, str],
        **kwargs
    ) -> str:
        """
        Build a prompt using the specified template and variables.
        
        Args:
            template_name: Name of the template to use
            variables: Dictionary of variables to substitute in the template
            **kwargs: Additional variables to include in the template
            
        Returns:
            Formatted prompt string
        """
        template = self.templates.get(template_name, "{prompt}")
        all_vars = {**variables, **kwargs}
        return template.format(**all_vars)
    
    def build_chat_prompt(
        self,
        message: str,
        history: List[Dict[str, str]],
        persona: Dict[str, str]
    ) -> str:
        """
        Build a chat prompt with conversation history and persona context.
        
        Args:
            message: Current user message
            history: List of previous messages in the conversation
            persona: Dictionary containing persona information
            
        Returns:
            Formatted chat prompt
        """
        # Format conversation history
        formatted_history = []
        for msg in history:
            role = "User" if msg["role"] == "user" else persona.get("name", "Assistant")
            formatted_history.append(f"{role}: {msg['content']}")
        
        return self.build_prompt(
            "chat_response",
            {
                "persona_name": persona.get("name", "Assistant"),
                "persona_description": persona.get("description", ""),
                "history": "\n".join(formatted_history) if formatted_history else "No history",
                "message": message
            }
        )
