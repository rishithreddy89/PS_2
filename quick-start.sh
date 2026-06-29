#!/bin/bash

set -e

echo "🚀 LexMind AI - Quick Start Script"
echo "==================================="
echo ""

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update DATABASE_URL and SECRET_KEY"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "📦 Installing dependencies..."
poetry install

echo ""
echo "🗄️  Setting up database..."
echo "Please ensure MySQL is running and create the database:"
echo ""
echo "  mysql -u root -p"
echo "  CREATE DATABASE lexmind_db;"
echo "  CREATE USER 'lexmind'@'localhost' IDENTIFIED BY 'lexmind_password';"
echo "  GRANT ALL PRIVILEGES ON lexmind_db.* TO 'lexmind'@'localhost';"
echo "  FLUSH PRIVILEGES;"
echo ""
read -p "Press Enter after database is created..."

echo ""
echo "🔄 Running database migrations..."
poetry run alembic upgrade head

echo ""
echo "✨ Setup complete!"
echo ""
echo "Start the application with:"
echo "  poetry run uvicorn app.main:app --reload"
echo ""
echo "Or use Docker Compose:"
echo "  docker-compose up -d"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
