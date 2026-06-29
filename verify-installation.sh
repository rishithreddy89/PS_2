#!/bin/bash

echo "🔍 LexMind AI - Installation Verification"
echo "=========================================="
echo ""

ERRORS=0

echo "Checking project structure..."

# Check critical files
FILES=(
    "app/main.py"
    "app/core/config.py"
    "app/database/session.py"
    "app/models/__init__.py"
    "app/schemas/base.py"
    "app/repositories/base.py"
    "app/services/base.py"
    "app/registry/agent_registry.py"
    "app/registry/tool_registry.py"
    "app/memory/providers.py"
    "docker-compose.yml"
    "Dockerfile"
    "pyproject.toml"
    "alembic.ini"
    ".env.example"
    "README.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "Checking Python modules..."

# Check models
MODELS=(
    "app/models/user.py"
    "app/models/case.py"
    "app/models/case_document.py"
    "app/models/recommendation.py"
    "app/models/planner_execution.py"
    "app/models/memory.py"
    "app/models/feedback.py"
    "app/models/audit_log.py"
)

for model in "${MODELS[@]}"; do
    if [ -f "$model" ]; then
        echo "✅ $model"
    else
        echo "❌ Missing: $model"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "Checking API routers..."

ROUTERS=(
    "app/api/routers/health.py"
    "app/api/routers/cases.py"
    "app/api/routers/recommendations.py"
    "app/api/routers/agents.py"
    "app/api/routers/tools.py"
    "app/api/routers/planner.py"
    "app/api/routers/memory.py"
)

for router in "${ROUTERS[@]}"; do
    if [ -f "$router" ]; then
        echo "✅ $router"
    else
        echo "❌ Missing: $router"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "=========================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All files present!"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env"
    echo "2. Update database credentials in .env"
    echo "3. Run: docker-compose up -d"
    echo "   OR"
    echo "   Run: ./quick-start.sh"
    echo ""
    exit 0
else
    echo "❌ Found $ERRORS missing files"
    echo ""
    exit 1
fi
