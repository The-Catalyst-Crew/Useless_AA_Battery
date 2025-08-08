# AI Persona Generation and Interaction System

This project provides a comprehensive system for generating AI personas and interacting with them through a web interface and API.

## Project Structure

```
project_root/
├── ui/                       # Gradio-based web interface
│   ├── app.py               # Main application script
│   └── requirements.txt     # UI dependencies
│
├── api/                     # FastAPI backend
│   ├── main.py              # Main FastAPI application
│   ├── routers/             # API endpoint definitions
│   │   ├── analyze_and_persona.py
│   │   ├── chat.py
│   │   └── generation.py
│   ├── components/          # Core functionality components
│   │   ├── vision_language_model.py
│   │   ├── chat_agent.py
│   │   └── image_generator.py
│   ├── utils/               # Utility functions
│   │   ├── prompt_builder.py
│   │   └── config.py
│   └── requirements.txt     # API dependencies
│
└── docs/                    # Documentation
    └── README.md           # This file
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Set up a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # Install API dependencies
   cd api
   pip install -r requirements.txt
   
   # Install UI dependencies
   cd ../ui
   pip install -r requirements.txt
   ```

## Running the Application

### Starting the API Server

From the `api` directory:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Starting the UI

From the `ui` directory:

```bash
python app.py
```

The UI will be available at `http://localhost:7860`

## API Documentation

Once the API server is running, you can access:

- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Configuration

Configuration can be managed through environment variables or a config file. See `api/utils/config.py` for all available options.

## Development

### Adding New Features

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Write tests for your changes
4. Run tests: `pytest`
5. Submit a pull request

### Testing

Run the test suite:

```bash
pytest
```

## License

[Specify your license here]

## Contact

[Your contact information]
