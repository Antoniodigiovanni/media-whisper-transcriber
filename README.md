# Whisper AI Transcriber

Whisper AI Transcriber is a media transcription app that leverages OpenAI's Whisper model to transcribe audio from YouTube videos, podcasts, and audio files. It runs as a Streamlit web app, providing an easy-to-use interface for uploading media and getting accurate transcriptions in real-time.

---

## Features

- Transcribe YouTube videos, podcast episodes, and local audio files
- Uses OpenAI Whisper for state-of-the-art speech recognition
    - The model is either used through the Groq API or locally through HuggingFace's Transformers  
- Streamlit interface for quick, interactive use
- Runs fully in Docker for easy deployment and reproducibility

---

## Getting Started

### Prerequisites

- Docker installed and running
- A Groq API key with Whisper access or enough computational resources to run Whisper locally

### Setup

1. Create a `.env` file in the root directory of the project following the `.env.example`
2. To run the app, just run the following commands in the project root directory:
```bash
docker build -t whisper-ai-transcriber .
docker run -p 8501:8501 whisper-ai-transcriber
```

## Project Structure
```
├── Dockerfile
├── README.md
├── requirements.txt
├── src
│   ├── downloader
│   │   ├── downloader.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── transcription
│   │   ├── api_model.py
│   │   ├── __init__.py
│   │   └── local_model.py
│   └── utils
│       ├── __init__.py
│       └── utils.py
└── streamlit_app.py
```
