# Use official Python image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Set PYTHONPATH to include current directory
ENV PYTHONPATH=.
# Port 7860 is standard for Hugging Face Spaces
ENV PORT=7860

# Expose port
EXPOSE 7860

# Run the server in SSE mode
CMD ["python", "src/mcp/server.py", "--sse"]
