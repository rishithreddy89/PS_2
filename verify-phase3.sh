#!/bin/bash

# Phase 3 Verification Script
# Tests specialized agent framework implementation

set -e

echo "=========================================="
echo "PHASE 3 - Specialized Agent Framework"
echo "Verification Script"
echo "=========================================="
echo ""

# Check if we're in the correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📋 Checking specialized agent files..."
echo ""

# Check agent files
REQUIRED_FILES=(
    "app/agents/ingest_agent.py"
    "app/agents/retrieval_agent.py"
    "app/agents/evidence_agent.py"
    "app/agents/timeline_agent.py"
    "app/agents/risk_agent.py"
    "app/agents/memory_agent.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo ""
echo "📋 Checking response schemas..."
echo ""

# Check schema file
if [ -f "app/schemas/specialized_agents.py" ]; then
    echo "✅ app/schemas/specialized_agents.py"
else
    echo "❌ Missing: app/schemas/specialized_agents.py"
    exit 1
fi

echo ""
echo "📋 Checking test files..."
echo ""

if [ -f "tests/test_specialized_agents.py" ]; then
    echo "✅ tests/test_specialized_agents.py"
else
    echo "❌ Missing: tests/test_specialized_agents.py"
    exit 1
fi

echo ""
echo "🔬 Running unit tests..."
echo ""

# Run tests
poetry run pytest tests/test_specialized_agents.py -v --tb=short 2>&1 | head -n 100

echo ""
echo "🔍 Verifying agent registration..."
echo ""

# Create a Python script to verify agent registration
cat > /tmp/verify_agents.py << 'EOF'
import sys
sys.path.insert(0, '.')

from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.timeline_agent import TimelineAgent
from app.agents.risk_agent import RiskAgent
from app.agents.memory_agent import MemoryAgent

agents = [
    IngestAgent(),
    RetrievalAgent(),
    EvidenceAgent(),
    TimelineAgent(),
    RiskAgent(),
    MemoryAgent(),
]

print("Registered Agents:")
print("-" * 60)
for agent in agents:
    print(f"✅ {agent.name} (ID: {agent.agent_id})")
    print(f"   Capabilities: {', '.join(agent.capabilities[:3])}...")
    print(f"   Domains: {', '.join(agent.supported_domains)}")
    print(f"   Priority: {agent.priority}")
    print()

print(f"Total agents: {len(agents)}")
print()

# Test metadata
print("Agent Metadata Test:")
print("-" * 60)
for agent in agents:
    metadata = agent.metadata()
    assert 'agent_id' in metadata
    assert 'capabilities' in metadata
    assert len(metadata['capabilities']) > 0
    print(f"✅ {agent.name} metadata valid")

print()
print("All agents verified successfully!")
EOF

poetry run python /tmp/verify_agents.py

echo ""
echo "🧪 Testing agent execution..."
echo ""

# Create a test script
cat > /tmp/test_execution.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '.')

from app.agents.context import ExecutionContext
from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.schemas.agent import AgentExecutionStatus

async def test_agents():
    print("Testing agent execution...")
    print()
    
    # Test Ingest Agent
    context = ExecutionContext(case_id="test-1", domain="legal")
    context.input_data = {
        "content": "This is a test contract between parties.",
        "title": "Test Contract",
        "type": "contract"
    }
    
    ingest_agent = IngestAgent()
    response = await ingest_agent.execute(context)
    
    if response.status == AgentExecutionStatus.COMPLETED:
        print("✅ IngestAgent execution successful")
        print(f"   Duration: {response.duration_ms:.2f}ms")
        print(f"   Documents processed: {response.output.get('total_documents', 0)}")
    else:
        print(f"❌ IngestAgent failed: {response.error}")
        return False
    
    print()
    
    # Test Retrieval Agent
    context.input_data = {
        "query": "Find legal precedents",
        "case_type": "civil"
    }
    
    retrieval_agent = RetrievalAgent()
    response = await retrieval_agent.execute(context)
    
    if response.status == AgentExecutionStatus.COMPLETED:
        print("✅ RetrievalAgent execution successful")
        print(f"   Duration: {response.duration_ms:.2f}ms")
    else:
        print(f"❌ RetrievalAgent failed: {response.error}")
        return False
    
    print()
    
    # Test Evidence Agent
    context.input_data = {
        "evidence": [
            {"id": "ev1", "description": "Contract", "quality": "strong"},
            {"id": "ev2", "description": "Email", "quality": "moderate"}
        ]
    }
    
    evidence_agent = EvidenceAgent()
    response = await evidence_agent.execute(context)
    
    if response.status == AgentExecutionStatus.COMPLETED:
        print("✅ EvidenceAgent execution successful")
        print(f"   Duration: {response.duration_ms:.2f}ms")
        print(f"   Total evidence: {response.metadata.get('total_evidence', 0)}")
    else:
        print(f"❌ EvidenceAgent failed: {response.error}")
        return False
    
    print()
    print("All agent executions successful!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_agents())
    sys.exit(0 if result else 1)
EOF

poetry run python /tmp/test_execution.py

echo ""
echo "=========================================="
echo "✅ PHASE 3 VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "--------"
echo "✅ All specialized agent files present"
echo "✅ Response schemas implemented"
echo "✅ Unit tests created"
echo "✅ Agents registered successfully"
echo "✅ Agent execution verified"
echo ""
echo "Specialized Agents Implemented:"
echo "  • IngestAgent - Document ingestion and normalization"
echo "  • RetrievalAgent - Retrieval request preparation"
echo "  • EvidenceAgent - Evidence analysis"
echo "  • TimelineAgent - Timeline generation"
echo "  • RiskAgent - Risk assessment"
echo "  • MemoryAgent - Memory management"
echo ""
echo "Next Steps:"
echo "  • Phase 4: LLM Integration (Claude, LangGraph)"
echo "  • Phase 5: RAG Implementation (ChromaDB, Embeddings)"
echo ""
echo "To run full test suite:"
echo "  poetry run pytest tests/test_specialized_agents.py -v"
echo ""
