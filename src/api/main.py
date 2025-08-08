"""
Main FastAPI application for the AI Persona Generation API.
"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Import configuration
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="AI Persona Generation API",
    description="API for generating and interacting with AI personas",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    **settings.cors_config
)

# Import and include routers
from api.routers import chat, persona, generation

# Include routers with proper prefixes
app.include_router(
    chat.router,
    prefix=settings.CHAT_ENDPOINT,
    tags=["chat"]
)

app.include_router(
    persona.router,
    prefix=settings.PERSONA_ENDPOINT,
    tags=["persona"]
)

app.include_router(
    generation.router,
    prefix=settings.IMAGE_ENDPOINT,
    tags=["generation"]
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development")
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Persona Generation API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "endpoints": {
            "chat": settings.CHAT_ENDPOINT,
            "persona": settings.PERSONA_ENDPOINT,
            "generation": settings.IMAGE_ENDPOINT
        }
    }
