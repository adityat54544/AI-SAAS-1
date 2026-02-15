# SaaS Application

A production-ready Python SaaS application built with FastAPI.

## Description

This is a modern, containerized SaaS application built using FastAPI framework. It provides a solid foundation for building scalable web applications with proper DevOps practices.

## Features

- FastAPI-based REST API
- Docker containerization
- Health check endpoints
- Production-ready configuration
- Comprehensive testing setup

## Project Structure

```
project_root/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_basic.py
├── .gitignore
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-saas-important
```

### 2. Virtual Environment Setup

Create a virtual environment:

```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

Upgrade pip and install the required packages:

```bash
pip install --upgrade pip
pip install fastapi uvicorn pytest httpx
```

### 4. Freeze Dependencies

Save all dependencies to requirements.txt:

```bash
pip freeze > requirements.txt
```

## Running Locally

### Option 1: Using Python directly

```bash
python app/main.py
```

### Option 2: Using Uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at: http://localhost:8000

### API Endpoints

- **Root**: `GET /` - Returns `{"status": "ok"}`
- **Health Check**: `GET /health` - Returns health status
- **API Docs**: `GET /docs` - OpenAPI documentation

## Running with Docker

### 1. Build and Run with Docker Compose

```bash
docker-compose up --build
```

### 2. Run in Detached Mode

```bash
docker-compose up -d --build
```

### 3. View Logs

```bash
docker-compose logs -f
```

### 4. Stop the Container

```bash
docker-compose down
```

The application will be available at: http://localhost:8000

## Running Tests

Run the test suite:

```bash
# With pytest
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Available variables:
- `APP_NAME` - Application name
- `APP_VERSION` - Application version
- `DEBUG` - Debug mode (true/false)
- `HOST` - Server host
- `PORT` - Server port

## Development

### Hot Reload

For development with auto-reload:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development

```bash
docker-compose -f docker-compose.yml up --build
```

## Production Deployment

The application is production-ready with:
- Multi-stage Docker builds
- Non-root user in container
- Optimized Python 3.11-slim base image
- Proper signal handling

## License

MIT License
