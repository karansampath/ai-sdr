# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv && uv pip install -r pyproject.toml

# Copy application code
COPY . .

# Create data directory for DuckDB
RUN mkdir -p data

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Set default environment variables
ENV XAI_API_KEY=""

# Run the application
CMD ["uv", "run", "run.py"]
