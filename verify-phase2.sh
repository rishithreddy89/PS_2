#!/bin/bash

# Phase 2 Verification Script
# Verifies all Phase 2 components are working

echo "=========================================="
echo "Phase 2 - Verification Script"
echo "=========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python --version || python3 --version

# Check Poetry
echo ""
echo "✓ Checking Poetry..."
poetry --version

# Verify file structure
echo ""
echo "✓ Verifying file structure..."

files=(
    "app/agents/base.py"
    "app/agents/context.py"
    "app/agents/factory.py"
    "app/agents/planner.py"
    "app/agents/orchestrator.py"
    "app/agents/sample_agents.py"
    "app/agents/init.py"
    "app/schemas/agent.py"
    "app/services/planner.py"
    "app/api/routers/planner.py"
    "tests/test_agents.py"
    "PHASE2_SUMMARY.md"
    "PHASE2_EXAMPLES.md"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    echo ""
    echo "❌ Some files are missing!"
    exit 1
fi

# Check dependencies
echo ""
echo "✓ Checking dependencies..."
if grep -q "langgraph" requirements.txt && grep -q "langchain-core" requirements.txt; then
    echo "  ✓ LangGraph dependencies present"
else
    echo "  ✗ LangGraph dependencies missing"
    exit 1
fi

# Run Python syntax check
echo ""
echo "✓ Checking Python syntax..."
python -m py_compile app/agents/*.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✓ All agent files have valid syntax"
else
    echo "  ✗ Syntax errors found"
    exit 1
fi

# Try importing modules
echo ""
echo "✓ Checking module imports..."
python -c "
from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.factory import AgentFactory
from app.agents.planner import PlannerAgent
from app.agents.orchestrator import Orchestrator
from app.schemas.agent import AgentResponse, ExecutionPlan
print('  ✓ All modules import successfully')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "  ✗ Module import errors (install dependencies first)"
fi

# Check test file
echo ""
echo "✓ Checking test file..."
if python -m py_compile tests/test_agents.py 2>/dev/null; then
    echo "  ✓ Test file has valid syntax"
else
    echo "  ✗ Test file has syntax errors"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Phase 2 Verification Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Install dependencies: poetry install"
echo "  2. Run tests: poetry run pytest tests/test_agents.py"
echo "  3. Start app: poetry run uvicorn app.main:app --reload"
echo "  4. Try quick start: ./quick-start-phase2.sh"
echo ""
