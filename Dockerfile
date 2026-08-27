# Multi-stage Dockerfile for ChargeShield Decision Intelligence Platform

# Stage 1: Build Frontend Static Bundle
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Backend Runner
FROM python:3.11-slim AS production
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and compiled static frontend assets
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY data/ ./data/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY --from=frontend-builder /app/frontend/dist ./static_frontend

# Non-root security user
RUN useradd -m -u 10001 chargeshielduser && \
    chown -R chargeshielduser:chargeshielduser /app
USER chargeshielduser

EXPOSE 8000

ENV ENVIRONMENT=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/ready || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
