"""
API endpoints for generating content with AI personas.
"""
import base64
import logging
from io import BytesIO
from typing import Dict, List, Optional, Any

import requests
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from PIL import Image

# Import configuration and utilities
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# No authentication for now

class ImageGenerationRequest(BaseModel):
    """Model for image generation requests."""
    prompt: str = Field(..., description="The prompt to generate an image from")
    negative_prompt: Optional[str] = Field(
        None,
        description="Negative prompt to guide the generation away from certain content"
    )
    model: Optional[str] = Field(
        settings.DEFAULT_IMAGE_MODEL,
        description="Model to use for image generation"
    )
    steps: Optional[int] = Field(
        settings.DEFAULT_SD_STEPS,
        ge=1,
        le=150,
        description="Number of denoising steps"
    )
    cfg_scale: Optional[float] = Field(
        settings.DEFAULT_SD_CFG_SCALE,
        ge=1.0,
        le=30.0,
        description="Guidance scale for generation"
    )
    width: Optional[int] = Field(
        settings.DEFAULT_SD_WIDTH,
        ge=256,
        le=1024,
        description="Width of the generated image"
    )
    height: Optional[int] = Field(
        settings.DEFAULT_SD_HEIGHT,
        ge=256,
        le=1024,
        description="Height of the generated image"
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility"
    )
    return_image: Optional[bool] = Field(
        True,
        description="Whether to return the generated image as base64"
    )
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        if v % 64 != 0:
            raise ValueError("Width and height must be multiples of 64")
        return v

class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    prompt: str = Field(..., description="The prompt used for generation")
    model: str = Field(..., description="Model used for generation")
    parameters: Dict[str, Any] = Field(..., description="Generation parameters used")
    image_base64: Optional[str] = Field(
        None,
        description="Base64-encoded image data (if return_image=True)"
    )
    image_url: Optional[str] = Field(
        None,
        description="URL to the generated image (if saved to a file)"
    )
    seed: Optional[int] = Field(
        None,
        description="Seed used for generation"
    )

async def call_stable_diffusion_api(
    prompt: str,
    negative_prompt: Optional[str],
    model: str,
    steps: int,
    cfg_scale: float,
    width: int,
    height: int,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Call the Stable Diffusion API to generate an image."""
    headers = {
        "Authorization": f"Bearer {settings.STABLE_DIFFUSION_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or "",
        "model_id": model,
        "num_inference_steps": steps,
        "guidance_scale": cfg_scale,
        "width": width,
        "height": height,
    }
    
    if seed is not None:
        payload["seed"] = seed
    
    try:
        # Note: Replace with the actual Stable Diffusion API endpoint
        response = requests.post(
            "https://api.stablediffusion.com/v1/generate",
            headers=headers,
            json=payload,
            timeout=60  # Longer timeout for image generation
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Stable Diffusion API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error communicating with the image generation service"
        )

@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest
):
    """
    Generate an image based on the provided prompt and parameters.
    
    This endpoint generates an image using the specified model and parameters.
    It supports both returning the image as base64 or saving it to a file.
    """
    try:
        # Call the Stable Diffusion API
        response_data = await call_stable_diffusion_api(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            model=request.model,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            width=request.width,
            height=request.height,
            seed=request.seed
        )
        
        # Extract the generated image (in base64 format from the API response)
        # Note: The actual response structure may vary based on the Stable Diffusion API
        image_base64 = response_data.get("images", [None])[0]
        if not image_base64 and request.return_image:
            raise ValueError("No image data received from the generation service")
        
        # If we need to process the image (e.g., resize, convert format)
        if image_base64 and request.return_image:
            try:
                # Decode base64 to image
                image_data = base64.b64decode(image_base64)
                img = Image.open(BytesIO(image_data))
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert back to base64
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode()
            except Exception as img_error:
                logger.error(f"Error processing image: {str(img_error)}")
                raise ValueError("Error processing the generated image")
        
        # Generate a seed if none was provided
        used_seed = request.seed or response_data.get("seed") or 42
        
        return {
            "prompt": request.prompt,
            "model": request.model,
            "parameters": {
                "steps": request.steps,
                "cfg_scale": request.cfg_scale,
                "width": request.width,
                "height": request.height,
                "seed": used_seed,
                "negative_prompt": request.negative_prompt
            },
            "image_base64": image_base64 if request.return_image else None,
            "seed": used_seed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image generation: {str(e)}", exc_info=True)
        error_detail = str(e)
        if "CUDA out of memory" in error_detail:
            error_detail = "The image generation service is currently overloaded. Please try again with a smaller image size or fewer steps."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during image generation: {error_detail}"
        )
