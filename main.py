"""
Main launcher script for the AI Persona Generation and Interaction application.
This script starts both the FastAPI backend and Gradio frontend.
"""
import subprocess
import threading
import time
import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_backend():
    """Run the FastAPI backend server."""
    print("Starting FastAPI backend server...")
    api_dir = Path(__file__).parent / "src"
    
    # Ensure the Python path is set correctly
    sys.path.insert(0, str(api_dir.parent))
    
    # Load environment variables again to ensure they're available in the subprocess
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the FastAPI app using uvicorn
    os.chdir(str(api_dir))
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False, app_dir=str(api_dir))

def run_frontend():
    """Run the Gradio frontend."""
    # Give the backend a moment to start
    time.sleep(2)
    print("\nStarting Gradio frontend...")
    
    # Ensure the Python path is set correctly
    ui_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(ui_dir.parent))
    
    # Load environment variables again to ensure they're available
    from dotenv import load_dotenv
    load_dotenv()
    
    # Import and run the Gradio app
    from ui.app import main as run_gradio
    run_gradio()

def main():
    """Main function to start both backend and frontend."""
    try:
        # Start the backend in a separate thread
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # Start the frontend in the main thread
        run_frontend()
        
    except KeyboardInterrupt:
        print("\nShutting down the application...")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("""
    AI Persona Generation and Interaction
    ====================================
    Starting application...
    - Backend API: http://localhost:8000
    - API Docs: http://localhost:8000/docs
    - Frontend UI: http://localhost:7860
    
    Press Ctrl+C to stop the application.
    """)
    main()
