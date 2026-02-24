# Use official stable Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and app files
COPY src ./src
COPY assets ./assets
COPY app.py .
ENV PYTHONPATH=.
# Port 7860 is standard for Hugging Face Spaces
ENV PORT=7860

# Expose port
EXPOSE 7860

# Run the Gradio UI server
CMD ["python", "app.py"]
