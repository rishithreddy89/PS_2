#!/bin/bash

echo "=================================="
echo "PHASE 5 VERIFICATION"
echo "Decision Intelligence Layer"
echo "=================================="
echo ""

echo "✓ Checking Phase 5 Components..."
echo ""

# Check agents
echo "1. NBA Agents:"
if [ -f "app/agents/nba_agent.py" ]; then
    echo "   ✓ NBA Agent"
else
    echo "   ✗ NBA Agent MISSING"
fi

if [ -f "app/agents/evaluation_agent.py" ]; then
    echo "   ✓ Evaluation Agent"
else
    echo "   ✗ Evaluation Agent MISSING"
fi

if [ -f "app/agents/reflection_agent.py" ]; then
    echo "   ✓ Reflection Agent"
else
    echo "   ✗ Reflection Agent MISSING"
fi

if [ -f "app/agents/explainability_agent.py" ]; then
    echo "   ✓ Explainability Agent"
else
    echo "   ✗ Explainability Agent MISSING"
fi

if [ -f "app/agents/human_review_agent.py" ]; then
    echo "   ✓ Human Review Agent"
else
    echo "   ✗ Human Review Agent MISSING"
fi

echo ""
echo "2. Schemas:"
if [ -f "app/schemas/nba.py" ]; then
    echo "   ✓ NBA Schemas"
else
    echo "   ✗ NBA Schemas MISSING"
fi

echo ""
echo "3. API Routes:"
if [ -f "app/api/routers/nba.py" ]; then
    echo "   ✓ NBA Router"
else
    echo "   ✗ NBA Router MISSING"
fi

echo ""
echo "4. Tests:"
if [ -f "tests/test_phase5.py" ]; then
    echo "   ✓ Phase 5 Tests"
else
    echo "   ✗ Phase 5 Tests MISSING"
fi

echo ""
echo "=================================="
echo "RUNNING TESTS"
echo "=================================="
echo ""

# Run Phase 5 tests
poetry run pytest tests/test_phase5.py -v --tb=short

echo ""
echo "=================================="
echo "VERIFICATION COMPLETE"
echo "=================================="
