"""
API endpoints for managing AI personas.
"""
import base64
import json
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.param_functions import Depends as DependsParam
from pydantic import BaseModel, Field, validator
from PIL import Image, UnidentifiedImageError

# Import configuration and utilities
from config import settings
from utils.personality_generator import PersonalityGenerator

# Field descriptions for reuse
PERSONA_NAME_DESC = "Name of the persona"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# No authentication for now
OptionalAuth = None

class PersonaTrait(BaseModel):
    """Model for persona traits."""
    name: str = Field(..., description="Name of the trait")
    description: str = Field(..., description="Description of the trait")
    value: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Intensity of the trait (0.0 to 1.0)"
    )

class PersonaCreateRequest(BaseModel):
    """Request model for creating a new persona."""
    name: str = Field(..., description=PERSONA_NAME_DESC)
    description: str = Field(..., description="Brief description of the persona")
    image_base64: Optional[str] = Field(
        None,
        description="Base64-encoded image of the persona (optional)"
    )
    traits: List[PersonaTrait] = Field(
        default_factory=list,
        description="List of personality traits"
    )
    background: Optional[str] = Field(
        None,
        description="Background story or context for the persona"
    )
    
    @validator('image_base64')
    def validate_image(cls, v):
        if v is not None:
            try:
                # Try to decode the base64 image to validate it
                image_data = base64.b64decode(v)
                Image.open(BytesIO(image_data))
            except Exception as e:
                raise ValueError(f"Invalid image data: {str(e)}")
        return v

class PersonaResponse(BaseModel):
    """Response model for persona operations."""
    id: str = Field(..., description="Unique identifier for the persona")
    name: str = Field(..., description=PERSONA_NAME_DESC)
    description: str = Field(..., description="Description of the persona")
    traits: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of personality traits with values"
    )
    created_at: str = Field(..., description="ISO 8601 timestamp of creation")
    updated_at: str = Field(..., description="ISO 8601 timestamp of last update")

class PersonaTraits(BaseModel):
    """Model for persona traits."""
    personality: str = Field(..., description="Personality description")
    interests: List[str] = Field(default_factory=list, description="List of interests")
    communication_style: str = Field(..., description="Communication style")
    knowledge_domain: str = Field(..., description="Domain of knowledge")
    system_prompt: Optional[str] = Field(None, description="System prompt for the AI")

class PersonaCreate(BaseModel):
    """Model for creating a new persona."""
    name: str = Field(..., description=PERSONA_NAME_DESC)
    description: str = Field(..., description="Description of the persona")
    traits: PersonaTraits = Field(..., description="Traits of the persona")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image of the persona")
    object_name: Optional[str] = Field(None, description="Name of the object for personality generation")

class PersonaResponse(PersonaCreate):
    """Response model for persona operations."""
    id: str = Field(..., description="Unique identifier for the persona")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the message")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatResponse(BaseModel):
    """Response model for chat operations."""
    message: str = Field(..., description="The assistant's response message")
    conversation_id: str = Field(..., description="ID of the conversation")
    timestamp: datetime = Field(..., description="Timestamp of the response")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis and personality generation."""
    image_base64: str = Field(..., description="Base64 encoded image")
    object_name: str = Field(..., description="Name of the object in the image")
    description: Optional[str] = Field(None, description="Optional description of the object")

class PersonalityGenerationResponse(BaseModel):
    """Response model for personality generation."""
    object_name: str = Field(..., description="Name of the object")
    system_prompt: str = Field(..., description="Generated system prompt")
    saved_path: str = Field(..., description="Path to the saved personality file")

class ModelInfo(BaseModel):
    """Model information response model."""
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Display name of the model")
    description: str = Field(..., description="Description of the model")
    context_length: Optional[int] = Field(None, description="Maximum context length")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Model capabilities")

@router.get("/models/free-with-images", response_model=List[ModelInfo])
async def list_free_models_with_image_support() -> List[Dict[str, Any]]:
    """
    Get a list of free models that support image inputs.
    
    Args:
        token: OAuth2 token for authentication
        
    Returns:
        List of model information dictionaries
    """
    try:
        return personality_generator.get_free_models_with_image_support()
    except Exception as e:
        logger.error(f"Error fetching free models with image support: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching models: {str(e)}"
        )

@router.post("/generate-from-image", response_model=PersonalityGenerationResponse)
async def generate_personality_from_image(
    request: ImageAnalysisRequest
) -> Dict[str, Any]:
    """
    Generate a personality for an object based on its image.
    
    Args:
        request: The image analysis request
        token: OAuth2 token for authentication
        
    Returns:
        Dict containing the generated personality details
    """
    try:
        # Generate a description of the image if not provided
        image_description = request.description
        if not image_description:
            # TODO: Add image analysis to generate a description
            # For now, use a placeholder
            image_description = f"An image of {request.object_name}"
        
        # Generate the personality using the personality generator
        personality_data = PersonalityGenerator().generate_personality(
            object_name=request.object_name,
            image_description=image_description
        )
        
        return {
            "object_name": request.object_name,
            "system_prompt": personality_data["system_prompt"],
            "saved_path": personality_data.get("saved_path", "")
        }
        
    except Exception as e:
        logger.error(f"Error generating personality from image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the personality: {str(e)}"
        )

@router.post("/create", response_model=PersonaResponse)
async def create_persona(
    request: PersonaCreate
) -> Dict[str, Any]:
    """
    Create a new persona with the given details.
    
    Args:
        request: The persona creation request
        token: OAuth2 token for authentication
        
    Returns:
        Dict containing the created persona details
    """
    try:
        # Generate a unique ID for the persona
        persona_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Generate personality if object_name is provided
        system_prompt = None
        if request.object_name and not (request.traits and request.traits.system_prompt):
            try:
                personality_data = PersonalityGenerator().generate_personality(
                    object_name=request.object_name,
                    image_description=f"An image of {request.object_name}"
                )
                system_prompt = personality_data["system_prompt"]
                
                # Update traits with the generated system prompt
                traits = request.traits.dict() if request.traits else {}
                traits["system_prompt"] = system_prompt
                request.traits = PersonaTraits(**traits)
                
            except Exception as e:
                logger.warning(f"Failed to generate personality: {str(e)}")
        
        # Create the persona object
        persona = {
            "id": persona_id,
            "name": request.name,
            "description": request.description,
            "traits": request.traits.dict() if request.traits else {},
            "created_at": current_time,
            "updated_at": current_time,
            "image_base64": request.image_base64,
            "object_name": request.object_name
        }
        
        # Store the persona (in-memory for now)
        personas[persona_id] = persona
        
        return PersonaResponse(**persona)
        
    except Exception as e:
        logger.error(f"Error creating persona: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the persona: {str(e)}"
        )

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_personas(token: str = OptionalAuth) -> List[Dict[str, Any]]:
    """
    List all available personas.
    
    Returns:
        List of persona dictionaries
    """
    try:
        # List all JSON files in the personas directory
        personas_dir = Path("personas")
        personas_dir.mkdir(exist_ok=True)
        
        personas = []
        for file_path in personas_dir.glob("*.json"):
            with open(file_path, "r") as f:
                try:
                    persona_data = json.load(f)
                    personas.append(persona_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {file_path}")
        
        return personas
    except Exception as e:
        logger.error(f"Error listing personas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while listing personas: {str(e)}"
        )

@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str
):
    """
    Retrieve details of a specific persona by ID.
    
    This endpoint returns the full details of a persona, including its traits
    and other attributes.
    """
    try:
        # TODO: Implement actual persona retrieval logic
        # For now, return a mock response
        from datetime import datetime, timedelta
        now = datetime.utcnow().isoformat()
        
        return {
            "id": persona_id,
            "name": "Example Persona",
            "description": "This is an example persona",
            "traits": [
                {"name": "creativity", "description": "Creative thinking", "value": 0.8},
                {"name": "humor", "description": "Sense of humor", "value": 0.6}
            ],
            "created_at": now,
            "updated_at": now
        }
        
    except Exception as e:
        logger.error(f"Error retrieving persona {persona_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve persona: {str(e)}"
        )

@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...)
):
    """
    Analyze an image to extract persona attributes.
    
    This endpoint analyzes the provided image to suggest persona traits
    and characteristics based on visual content.
    """
    try:
        # TODO: Implement actual image analysis logic
        # For now, return a mock response
        return {
            "object_class": "person",
            "suggested_traits": [
                {"name": "confidence", "description": "Self-assurance", "value": 0.7},
                {"name": "openness", "description": "Openness to experience", "value": 0.8}
            ],
            "description_suggestion": "A confident and open-minded individual who enjoys new experiences."
        }
        
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze image: {str(e)}"
        )

@router.post("/chat-with-persona")
async def chat_with_persona(conversation: Dict[str, Any]):
    """
    Chat with the created persona.
    
    Args:
        conversation: Contains conversation history and current message
        
    Returns:
        Dict containing the persona's response
    """
    try:
        # TODO: Implement chat logic with the persona
        return {
            "response": "Meow! Thanks for the message! I'm the cat from the image you sent earlier.",
            "conversation_id": conversation.get("conversation_id", "default")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-image")
async def generate_image(request: Dict[str, Any]):
    """
    Generate an image based on the persona and user prompt.
    
    Args:
        request: Contains persona details and generation prompt
        
    Returns:
        Dict containing the generated image as base64
    """
    try:
        # TODO: Implement image generation logic
        return {
            "image_base64": "",  # Base64 encoded image
            "prompt": request.get("prompt", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
