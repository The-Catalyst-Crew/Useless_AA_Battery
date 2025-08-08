# AI Persona Generation and Interaction

Create, interact with, and visualize AI personas based on images. This project combines computer vision and natural language processing to generate unique AI personalities from images and enables interactive conversations with them.

## Features

- 🖼️ **Image Analysis**: Upload any image or use your webcam to analyze visual content
- 🎭 **Persona Generation**: Automatically create unique AI personas based on image content
- 💬 **Interactive Chat**: Have natural conversations with your AI persona
- 🎨 **Image Generation**: Generate new images based on your AI persona's characteristics
- 🌐 **Web Interface**: User-friendly Gradio-based web interface
- 🔄 **RESTful API**: Fully documented API for custom integrations

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Webcam (optional, for real-time image capture)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Useless
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Using the Launcher Script (Recommended)

Simply run the main launcher script:

```bash
python main.py
```

This will start both the FastAPI backend and Gradio frontend automatically.

### Option 2: Manual Startup

#### 1. Start the FastAPI Backend

```bash
cd src/api
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

#### 2. Start the Gradio Frontend

In a new terminal window:

```bash
cd src/ui
python app.py
```

The web interface will be available at `http://localhost:7860`

## Project Structure

```
src/
├── api/                     # FastAPI backend
│   ├── main.py             # Main FastAPI application
│   ├── routers/            # API route handlers
│   │   └── persona.py      # Persona-related endpoints
│   └── requirements.txt    # Python dependencies
└── ui/                     # Gradio frontend
    ├── app.py              # Main Gradio application
    └── requirements.txt    # UI-specific dependencies
```

## API Endpoints

### `POST /api/v1/analyze-and-create-persona`
Analyze an image and create a persona based on its content.

**Request Body:**
```json
{
  "image_base64": "base64_encoded_image",
  "personality_examples": "Optional personality description"
}
```

### `POST /api/v1/chat-with-persona`
Chat with the created persona.

**Request Body:**
```json
{
  "message": "Your message here",
  "persona": { /* persona object */ },
  "conversation_history": [ /* array of messages */ ]
}
```

### `POST /api/v1/generate-image`
Generate an image based on the persona and prompt.

**Request Body:**
```json
{
  "persona": { /* persona object */ },
  "prompt": "Description of the image to generate"
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
- [Gradio](https://gradio.app/) - Rapid web UIs for machine learning models
- [Hugging Face](https://huggingface.co/) - For pre-trained models and datasets
