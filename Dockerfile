# Build stage - React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Backend stage - Django
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend (preserve package structure)
COPY manage.py .
COPY nyc_taxi_dashboard/ nyc_taxi_dashboard/
COPY dashboard/ dashboard/

# Copy built React frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Run migrations, load zones, and start server
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py load_zones && gunicorn --bind 0.0.0.0:8000 --workers 2 nyc_taxi_dashboard.wsgi:application"]
