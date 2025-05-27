# Use a slim, recent Python image
FROM python:3.11-slim
# FROM pytorch/pytorch:2.6.0-cuda11.8-cudnn8-runtime
# FROM pytorch/pytorch:2.7.0-cuda11.8-cudnn9-runtime

# Set environment variables to avoid issues with Python buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y ffmpeg git curl && apt-get clean
# RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.enableCORS=false"]
