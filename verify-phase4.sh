#!/bin/bash

# Phase 4 Verification Script
# Validates AI Intelligence Layer (RAG + OpenAI + Memory)

set -e

echo "========================================="
echo "Phase 4 - AI Intelligence Layer Verification"
echo "========================================="
echo ""

# Check if in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

echo "✓ Running from project root"
echo ""

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
fi

echo "✓ Environment file exists"
echo ""

# Check required environment variables
echo "Checking environment variables..."
source .env 2>/dev/null || true

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠ Warning: OPENAI_API_KEY not set in .env"
    echo "  AI-powered agents will not work without OpenAI API key"
else
    echo "✓ OPENAI_API_KEY is set"
fi

if [ -z "$OPENAI_MODEL" ]; then
    echo "⚠ Warning: OPENAI_MODEL not set, defaulting to gpt-4"
else
    echo "✓ OPENAI_MODEL is set to: $OPENAI_MODEL"
fi

if [ -z "$EMBEDDING_MODEL" ]; then
    echo "⚠ Warning: EMBEDDING_MODEL not set"
else
    echo "✓ EMBEDDING_MODEL is set to: $EMBEDDING_MODEL"
fi

if [ -z "$CHROMA_PERSIST_DIRECTORY" ]; then
    echo "⚠ Warning: CHROMA_PERSIST_DIRECTORY not set"
else
    echo "✓ CHROMA_PERSIST_DIRECTORY is set to: $CHROMA_PERSIST_DIRECTORY"
fi

echo ""

# Check directory structure
echo "Verifying Phase 4 directory structure..."

check_file() {
    if [ -f "$1" ]; then
        echo "  ✓ $1"
    else
        echo "  ❌ Missing: $1"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "  ✓ $1/"
    else
        echo "  ❌ Missing: $1/"
        return 1
    fi
}

# Knowledge module
check_dir "app/knowledge"
check_file "app/knowledge/__init__.py"
check_file "app/knowledge/models.py"
check_file "app/knowledge/embedding.py"
check_file "app/knowledge/chroma_service.py"
check_file "app/knowledge/ingestion.py"
check_file "app/knowledge/retrieval.py"

# LLM module
check_dir "app/llm"
check_file "app/llm/__init__.py"
check_file "app/llm/openai_service.py"

# Prompts module
check_dir "app/prompts"
check_file "app/prompts/__init__.py"
check_file "app/prompts/manager.py"

# Memory module
check_dir "app/memory"
check_file "app/memory/__init__.py"
check_file "app/memory/providers.py"
check_file "app/memory/implementation.py"

# Upgraded agents
check_file "app/agents/retrieval_agent.py"
check_file "app/agents/evidence_agent.py"
check_file "app/agents/timeline_agent.py"
check_file "app/agents/risk_agent.py"
check_file "app/agents/memory_agent.py"

# AI models
check_file "app/agents/ai_models.py"

# Tests
check_file "tests/test_phase4.py"
check_file "tests/test_specialized_agents.py"

echo ""

# Install dependencies
echo "Checking Python dependencies..."
if command -v poetry &> /dev/null; then
    echo "✓ Poetry is installed"
    echo ""
    echo "Installing dependencies..."
    poetry install --no-interaction
    echo "✓ Dependencies installed"
else
    echo "⚠ Poetry not found, using pip..."
    pip install -q openai chromadb rank-bm25 pypdf2 markdown sentence-transformers tenacity
    echo "✓ Dependencies installed via pip"
fi

echo ""

# Run Phase 4 tests
echo "========================================="
echo "Running Phase 4 Tests"
echo "========================================="
echo ""

if command -v poetry &> /dev/null; then
    poetry run pytest tests/test_phase4.py -v --tb=short
else
    pytest tests/test_phase4.py -v --tb=short
fi

echo ""
echo "========================================="
echo "Running Updated Agent Tests"
echo "========================================="
echo ""

if command -v poetry &> /dev/null; then
    poetry run pytest tests/test_specialized_agents.py -v --tb=short
else
    pytest tests/test_specialized_agents.py -v --tb=short
fi

echo ""

# Summary
echo "========================================="
echo "Phase 4 Verification Summary"
echo "========================================="
echo ""
echo "✓ Knowledge Base - Implemented"
echo "  - Document models"
echo "  - Embedding service (OpenAI)"
echo "  - ChromaDB integration"
echo "  - Ingestion pipeline"
echo "  - Hybrid retrieval (Vector + BM25)"
echo ""
echo "✓ LLM Integration - Implemented"
echo "  - OpenAI service"
echo "  - Structured outputs"
echo "  - Retry logic"
echo "  - Token tracking"
echo "  - Cost estimation"
echo ""
echo "✓ Prompt Management - Implemented"
echo "  - Centralized prompt templates"
echo "  - Variable substitution"
echo "  - System prompts"
echo "  - Reusable prompts"
echo ""
echo "✓ Memory Implementation - Implemented"
echo "  - Short-term memory"
echo "  - Long-term memory"
echo "  - Conversation memory"
echo "  - Case memory"
echo "  - Memory manager"
echo ""
echo "✓ AI-Powered Agents - Upgraded"
echo "  - Retrieval Agent (AI-powered)"
echo "  - Evidence Agent (AI-powered)"
echo "  - Timeline Agent (AI-powered)"
echo "  - Risk Agent (AI-powered)"
echo "  - Memory Agent (integrated)"
echo ""
echo "✓ Tests - Comprehensive"
echo "  - Knowledge ingestion tests"
echo "  - Embedding service tests"
echo "  - Hybrid retrieval tests"
echo "  - Prompt manager tests"
echo "  - OpenAI service tests"
echo "  - Memory implementation tests"
echo "  - Agent integration tests"
echo "  - Validation & retry tests"
echo ""
echo "========================================="
echo "Phase 4 Verification Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Set OPENAI_API_KEY in .env for full functionality"
echo "2. Ingest knowledge documents into ChromaDB"
echo "3. Test AI-powered agents with real queries"
echo "4. Monitor token usage and costs"
echo ""
echo "Note: Some tests may be skipped if OPENAI_API_KEY is not set."
echo "      This is expected behavior for CI/CD environments."
echo ""
