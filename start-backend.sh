#!/bin/bash

# Quick Start Script - Frontend + Backend
# Run this to start both services

echo "=== LexMind AI - Quick Start ==="
echo ""

# Check if backend is needed
echo "Starting backend API..."
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Set environment variables
export DATABASE_URL="sqlite:///./lexmind.db"
export SECRET_KEY="development-secret-key-change-in-production"
export ENVIRONMENT="development"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start backend in background
echo "Starting backend on http://localhost:8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID)"
echo ""
echo "=== Both services are running ==="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the backend"

# Wait for backend process
wait $BACKEND_PID
