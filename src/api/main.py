"""
Main FastAPI application for the AI Persona Generation API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Persona Generation API",
    description="API for generating and interacting with AI personas",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"status": "API is running"}

# Import and include routers
from routers import analyze_and_persona, chat, generation

app.include_router(analyze_and_persona.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(generation.router, prefix="/api/v1/generate", tags=["Generation"])
