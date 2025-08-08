"""
Configuration management for the application.
"""
import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """Manages application configuration."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration with default values."""
        if self._initialized:
            return
            
        self._config = {
            "app": {
                "name": "AI Persona Generation API",
                "version": "0.1.0",
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "server": {
                "host": os.getenv("HOST", "0.0.0.0"),
                "port": int(os.getenv("PORT", "8000")),
                "reload": os.getenv("RELOAD", "false").lower() == "true"
            },
            "models": {
                "vision_language": os.getenv("VISION_LANGUAGE_MODEL", "default-vlm"),
                "chat": os.getenv("CHAT_MODEL", "default-chat"),
                "image_generation": os.getenv("IMAGE_GEN_MODEL", "default-image-gen")
            },
            "storage": {
                "type": os.getenv("STORAGE_TYPE", "local"),
                "local_path": os.getenv("STORAGE_LOCAL_PATH", "./storage"),
                "s3_bucket": os.getenv("S3_BUCKET", "")
            },
            "security": {
                "api_key": os.getenv("API_KEY", "")
            }
        }
        
        # Load additional config from file if specified
        config_file = os.getenv("CONFIG_FILE")
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
            
        self._initialized = True
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load configuration from a YAML file.
        
        Args:
            file_path: Path to the YAML config file
        """
        try:
            with open(file_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}
                self._deep_update(self._config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {file_path}: {e}")
    
    def _deep_update(self, original: Dict[Any, Any], update: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Recursively update a dictionary.
        
        Args:
            original: Dictionary to update
            update: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                original[key] = self._deep_update(original[key], value)
            else:
                original[key] = value
        return original
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot notation key.
        
        Args:
            key: Dot notation key (e.g., 'server.port')
            default: Default value if key not found
            
        Returns:
            The configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to config values."""
        return self.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary."""
        return self._config.copy()

# Global configuration instance
config = Config()
