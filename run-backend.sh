#!/bin/bash

echo "Starting LexMind AI Backend..."
echo ""

# Set environment variables
export DATABASE_URL="mysql+aiomysql://root:Rishith%401289@localhost:3306/leximind_db"
export SECRET_KEY="dev-secret-key-change-in-production"
export ENVIRONMENT="development"
export DEBUG="True"

# Create database if it doesn't exist
echo "Setting up database..."
mysql -uroot -pRishith@1289 -e "CREATE DATABASE IF NOT EXISTS leximind_db;" 2>/dev/null || echo "Database already exists or MySQL not accessible"

# Start uvicorn
echo "Backend API starting on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
