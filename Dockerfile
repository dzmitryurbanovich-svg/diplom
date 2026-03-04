# Backend & Final Image
FROM python:3.11-slim
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY assets/ ./assets/
COPY server.py .

# Copy pre-built frontend from host
# Ensure 'npm run build' was executed locally before deploy
COPY frontend/dist/ ./frontend/dist/
RUN ls -R frontend/dist

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
