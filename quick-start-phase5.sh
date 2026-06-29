#!/bin/bash

echo "=================================="
echo "PHASE 5 QUICK START"
echo "Decision Intelligence Layer"
echo "=================================="
echo ""

# Set OpenAI API key if not set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Set it in .env file or export OPENAI_API_KEY=your-key"
    echo ""
fi

# Start the application
echo "Starting LexMind AI..."
echo ""

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Waiting for API to start..."
sleep 5

# Test the endpoints
echo ""
echo "=================================="
echo "TESTING NBA ENDPOINTS"
echo "=================================="
echo ""

# Health check
echo "1. Health Check:"
curl -s http://localhost:8000/health | python -m json.tool
echo ""

# Create a test case
echo "2. Creating test case..."
CASE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Contract Dispute",
    "description": "Commercial contract dispute requiring legal analysis",
    "case_type": "contract_dispute",
    "status": "active",
    "priority": "high"
  }')

CASE_ID=$(echo $CASE_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$CASE_ID" ]; then
    echo "   ✗ Failed to create test case"
    kill $API_PID
    exit 1
fi

echo "   ✓ Case created: $CASE_ID"
echo ""

# Run NBA analysis
echo "3. Running NBA Analysis..."
echo "   This will execute the full Decision Intelligence workflow:"
echo "   → Retrieval → Evidence → Timeline → Risk"
echo "   → NBA Generation → Evaluation → Reflection"
echo "   → Explainability → Human Review"
echo ""

ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/nba/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"case_id\": \"$CASE_ID\",
    \"query\": \"Analyze this contract dispute and provide next best actions\",
    \"include_memory\": true
  }")

echo "$ANALYSIS_RESPONSE" | python -m json.tool
echo ""

# Get recommendations
echo "4. Fetching Recommendations..."
curl -s http://localhost:8000/api/v1/nba/recommendations/$CASE_ID | python -m json.tool
echo ""

# Get explanations
echo "5. Fetching Explanations..."
curl -s http://localhost:8000/api/v1/nba/explanations/$CASE_ID | python -m json.tool
echo ""

echo "=================================="
echo "PHASE 5 DEMONSTRATION COMPLETE"
echo "=================================="
echo ""
echo "Available Endpoints:"
echo "  POST   /api/v1/nba/analyze"
echo "  GET    /api/v1/nba/recommendations/{case_id}"
echo "  GET    /api/v1/nba/explanations/{case_id}"
echo "  POST   /api/v1/nba/feedback"
echo "  POST   /api/v1/nba/review"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# Wait for user interrupt
wait $API_PID
