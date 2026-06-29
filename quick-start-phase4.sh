#!/bin/bash

# Phase 4 Quick Start
# Run this after cloning/setting up the project

set -e

echo "========================================="
echo "Phase 4 - Quick Start"
echo "========================================="
echo ""

# 1. Setup environment
echo "Step 1: Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
    echo ""
    echo "⚠ IMPORTANT: Edit .env and set your OPENAI_API_KEY"
    echo ""
else
    echo "✓ .env already exists"
fi

# 2. Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
if command -v poetry &> /dev/null; then
    poetry install
    echo "✓ Dependencies installed via Poetry"
else
    pip install -r requirements.txt
    echo "✓ Dependencies installed via pip"
fi

# 3. Setup database
echo ""
echo "Step 3: Setting up database..."
if command -v docker &> /dev/null; then
    echo "Starting MySQL container..."
    docker-compose up -d mysql
    sleep 5
    echo "✓ MySQL container started"
else
    echo "⚠ Docker not found. Please start MySQL manually."
fi

# 4. Run migrations
echo ""
echo "Step 4: Running database migrations..."
if command -v poetry &> /dev/null; then
    poetry run alembic upgrade head
else
    alembic upgrade head
fi
echo "✓ Database migrations complete"

# 5. Create ChromaDB directory
echo ""
echo "Step 5: Setting up ChromaDB..."
mkdir -p ./chroma_db
echo "✓ ChromaDB directory created"

# 6. Run tests
echo ""
echo "Step 6: Running Phase 4 tests..."
if command -v poetry &> /dev/null; then
    poetry run pytest tests/test_phase4.py -v --tb=short || true
else
    pytest tests/test_phase4.py -v --tb=short || true
fi

# 7. Start application
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo ""
if command -v poetry &> /dev/null; then
    echo "  poetry run uvicorn app.main:app --reload"
else
    echo "  uvicorn app.main:app --reload"
fi
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "========================================="
echo "Phase 4 Features"
echo "========================================="
echo ""
echo "✓ Knowledge Base (ChromaDB)"
echo "✓ Hybrid Retrieval (Vector + BM25)"
echo "✓ OpenAI Integration (GPT-5.5)"
echo "✓ Prompt Management"
echo "✓ Memory System"
echo "✓ AI-Powered Agents"
echo ""
echo "To ingest documents:"
echo '  from app.knowledge import get_ingestion_service'
echo '  service = get_ingestion_service()'
echo '  await service.ingest_directory("./legal_docs/")'
echo ""
echo "To use AI agents:"
echo '  from app.agents import RetrievalAgent, ExecutionContext'
echo '  agent = RetrievalAgent()'
echo '  context = ExecutionContext(case_id="case-1")'
echo '  context.input_data = {"query": "Find contract law"}'
echo '  response = await agent.execute(context)'
echo ""
echo "For more information, see PHASE4_README.md"
echo ""
