"""
API endpoints for chat functionality with AI personas.
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator

# Import configuration and utilities
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# No authentication for now

# In-memory conversation store (replace with a database in production)
conversation_store = {}

class ChatMessage(BaseModel):
    """Model for chat message exchange."""
    message: str = Field(..., description="The message content")
    conversation_id: Optional[str] = Field(
        None, 
        description="Optional conversation ID for continuing a conversation"
    )
    persona_id: Optional[str] = Field(
        None,
        description="ID of the persona to chat with. If not provided, uses default."
    )
    model: Optional[str] = Field(
        settings.DEFAULT_CHAT_MODEL,
        description="Model to use for the chat completion"
    )
    temperature: Optional[float] = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for the response generation"
    )
    max_tokens: Optional[int] = Field(
        1000,
        ge=1,
        le=4000,
        description="Maximum number of tokens to generate in the response"
    )
    stream: Optional[bool] = Field(
        False,
        description="Whether to stream the response"
    )

    @validator('model')
    def validate_model(cls, v):
        """Validate that the model is supported."""
        # Add any model validation logic here
        # For now, just ensure it's not empty
        if not v or not v.strip():
            raise ValueError("Model cannot be empty")
        return v.strip()

class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="The assistant's response message")
    conversation_id: str = Field(..., description="ID of the conversation")
    model: str = Field(..., description="Model used for the response")
    tokens_used: int = Field(..., description="Number of tokens used")
    finish_reason: str = Field(..., description="Reason for response completion")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the response")

async def get_conversation(conversation_id: str) -> List[Dict[str, str]]:
    """Retrieve conversation history from the store."""
    if not conversation_id or conversation_id not in conversation_store:
        return []
    return conversation_store[conversation_id]

async def save_conversation(conversation_id: str, messages: List[Dict[str, str]]) -> None:
    """Save conversation history to the store."""
    conversation_store[conversation_id] = messages

async def call_openrouter_api(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    stream: bool = False
) -> Dict[str, Any]:
    """Call the OpenRouter API to get a chat completion."""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site.com",  # Update with your site
        "X-Title": "AI Persona Chat"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error communicating with the AI service"
        )

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: Request,
    chat: ChatMessage
):
    """
    Send a message to the AI persona and get a response.
    
    This endpoint processes a user message and returns an AI-generated response
    based on the selected persona and conversation history.
    """
    try:
        # Get or create conversation ID
        conversation_id = chat.conversation_id or f"conv_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Get conversation history
        messages = await get_conversation(conversation_id)
        
        # Add system message if this is a new conversation
        if not messages:
            system_message = {
                "role": "system",
                "content": "You are a helpful AI assistant. Respond helpfully and concisely."
            }
            if chat.persona_id:
                # Load persona details from database and customize system message
                try:
                    # In a real implementation, you would fetch the persona details from a database
                    # For now, we'll use a placeholder
                    # persona = await get_persona_from_database(chat.persona_id)
                    system_message["content"] = (
                        f"You are an AI assistant with a specific personality. "
                        f"Your persona ID is {chat.persona_id}. {system_message['content']}"
                    )
                except Exception as e:
                    logger.warning(f"Could not load persona {chat.persona_id}: {str(e)}")
                    system_message["content"] = (
                        f"You are an AI assistant with persona ID {chat.persona_id}. "
                        f"{system_message['content']}"
                    )
            messages.append(system_message)
        
        # Add user message to conversation
        user_message = {"role": "user", "content": chat.message}
        messages.append(user_message)
        
        # Call OpenRouter API
        response_data = await call_openrouter_api(
            messages=messages,
            model=chat.model,
            temperature=chat.temperature,
            max_tokens=chat.max_tokens,
            stream=chat.stream
        )
        
        # Extract assistant's response
        assistant_message = response_data["choices"][0]["message"]
        assistant_message_content = assistant_message["content"]
        finish_reason = response_data["choices"][0]["finish_reason"]
        
        # Add assistant's response to conversation
        messages.append(assistant_message)
        
        # Save updated conversation
        await save_conversation(conversation_id, messages)
        
        # Return response
        return {
            "response": assistant_message_content,
            "conversation_id": conversation_id,
            "model": chat.model,
            "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
            "finish_reason": finish_reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

@router.get("/history/{conversation_id}", response_model=List[Dict[str, str]])
async def get_chat_history(
    conversation_id: str
):
    """
    Retrieve chat history for a specific conversation.
    
    This endpoint returns the message history for the specified conversation ID.
    """
    try:
        messages = await get_conversation(conversation_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat history"
        )
