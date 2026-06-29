#!/bin/bash

# Phase 2 - Quick Start Script
# Dynamic Planner & Agent Orchestration

echo "=========================================="
echo "LexMind AI - Phase 2 Quick Start"
echo "=========================================="
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
poetry install || pip install -r requirements.txt

# Start application
echo ""
echo "🚀 Starting application..."
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
APP_PID=$!

# Wait for startup
echo ""
echo "⏳ Waiting for application to start..."
sleep 5

# Test endpoints
echo ""
echo "✅ Testing Phase 2 endpoints..."
echo ""

# Test health
echo "1. Health Check:"
curl -s http://localhost:8000/health | python -m json.tool
echo ""

# List agents
echo ""
echo "2. List Registered Agents:"
curl -s http://localhost:8000/api/v1/agents | python -m json.tool
echo ""

# Create execution plan
echo ""
echo "3. Create Execution Plan:"
curl -s -X POST http://localhost:8000/api/v1/planner/plan \
  -H "Content-Type: application/json" \
  -d '{
    "task_requirements": {
      "query": "Analyze documents",
      "analyze_evidence": true,
      "generate_recommendation": true
    },
    "domain": "general"
  }' | python -m json.tool
echo ""

# Execute workflow
echo ""
echo "4. Execute Complete Workflow:"
curl -s -X POST http://localhost:8000/api/v1/planner/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "documents": ["doc1.pdf", "doc2.pdf"],
      "query": "Analyze legal documents",
      "analyze_evidence": true
    },
    "domain": "legal",
    "workflow": "document_analysis"
  }' | python -m json.tool
echo ""

echo ""
echo "=========================================="
echo "✅ Phase 2 Quick Start Complete!"
echo "=========================================="
echo ""
echo "📖 API Documentation: http://localhost:8000/docs"
echo "📊 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Key Endpoints:"
echo "  • POST /api/v1/planner/execute - Execute workflow"
echo "  • POST /api/v1/planner/plan - Create plan"
echo "  • GET /api/v1/agents - List agents"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Wait for user interrupt
wait $APP_PID
