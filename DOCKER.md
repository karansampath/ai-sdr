# Docker Setup for AI-SDR

This document explains how to run the AI-SDR application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- XAI API key (get one from [console.x.ai](https://console.x.ai/))

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and add your XAI_API_KEY
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - FastAPI Backend: http://localhost:8000
   - Streamlit Frontend: http://localhost:8501

## Configuration

### Environment Variables

- `XAI_API_KEY`: Required - Your XAI API key for Grok services

### Ports

- **8000**: FastAPI backend server
- **8501**: Streamlit frontend application

### Data Persistence

The DuckDB database is stored in the `./data` directory, which is mounted as a Docker volume for persistence across container restarts.

## Docker Commands

### Build the image:
```bash
docker-compose build
```

### Run in background:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f
```

### Stop services:
```bash
docker-compose down
```

### Remove everything (including volumes):
```bash
docker-compose down -v
```

## Development

For development, you can mount the source code as a volume by adding this to the docker-compose.yml service:

```yaml
volumes:
  - .:/app
  - ./data:/app/data
```

This allows you to edit code without rebuilding the Docker image.
