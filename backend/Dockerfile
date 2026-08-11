# ==========================================
# Stage 1 - Base Image
# ==========================================

FROM python:3.12-slim

# ==========================================
# Environment
# ==========================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# ==========================================
# Working Directory
# ==========================================

WORKDIR /app

# ==========================================
# System Dependencies
# ==========================================

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# Install Python Dependencies
# ==========================================

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# ==========================================
# Copy Application
# ==========================================

COPY . .

# ==========================================
# Create Upload Directories
# ==========================================

RUN mkdir -p uploads temp_uploads logs

# ==========================================
# Expose Port
# ==========================================

EXPOSE 8000

# ==========================================
# Health Check
# ==========================================

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ==========================================
# Start Server
# ==========================================

CMD [
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]