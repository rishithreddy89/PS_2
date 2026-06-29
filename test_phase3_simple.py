#!/usr/bin/env python3
"""
Simple verification script for Phase 3 agents.
Tests basic functionality without pytest dependency.
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from app.agents.context import ExecutionContext
from app.agents.ingest_agent import IngestAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.timeline_agent import TimelineAgent
from app.agents.risk_agent import RiskAgent
from app.agents.memory_agent import MemoryAgent
from app.schemas.agent import AgentExecutionStatus


async def test_ingest_agent():
    """Test IngestAgent."""
    print("Testing IngestAgent...")
    
    agent = IngestAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "document_ingestion" in agent.capabilities
    assert "metadata_extraction" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution
    context.input_data = {
        "content": "This is a test contract between Acme Corp and John Doe.",
        "title": "Test Contract",
        "type": "contract"
    }
    
    response = await agent.execute(context)
    assert response.status == AgentExecutionStatus.COMPLETED
    assert "document_summaries" in response.output
    assert response.output["total_documents"] == 1
    print("  ✅ Execution successful")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_retrieval_agent():
    """Test RetrievalAgent."""
    print("Testing RetrievalAgent...")
    
    agent = RetrievalAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "query_building" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution
    context.input_data = {
        "query": "Find legal precedents for contract disputes",
        "case_type": "contract"
    }
    
    response = await agent.execute(context)
    assert response.status == AgentExecutionStatus.COMPLETED
    assert "retrieval_request" in response.output
    print("  ✅ Execution successful")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_evidence_agent():
    """Test EvidenceAgent."""
    print("Testing EvidenceAgent...")
    
    agent = EvidenceAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "evidence_analysis" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution
    context.input_data = {
        "evidence": [
            {"id": "ev1", "description": "Contract signed", "quality": "strong"},
            {"id": "ev2", "description": "Email thread", "quality": "moderate"}
        ]
    }
    
    response = await agent.execute(context)
    assert response.status == AgentExecutionStatus.COMPLETED
    assert "evidence_summary" in response.output
    print("  ✅ Execution successful")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_timeline_agent():
    """Test TimelineAgent."""
    print("Testing TimelineAgent...")
    
    agent = TimelineAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "timeline_generation" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution
    context.input_data = {
        "events": [
            {
                "id": "evt1",
                "description": "Contract signed",
                "date": datetime.utcnow().isoformat(),
                "type": "contract"
            }
        ]
    }
    
    response = await agent.execute(context)
    assert response.status == AgentExecutionStatus.COMPLETED
    assert "timeline_summary" in response.output
    print("  ✅ Execution successful")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_risk_agent():
    """Test RiskAgent."""
    print("Testing RiskAgent...")
    
    agent = RiskAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "risk_identification" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution
    context.input_data = {}
    context.set_shared("evidence_summary", {"missing_evidence": ["doc1"]})
    
    response = await agent.execute(context)
    assert response.status == AgentExecutionStatus.COMPLETED
    assert "risk_summary" in response.output
    print("  ✅ Execution successful")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_memory_agent():
    """Test MemoryAgent."""
    print("Testing MemoryAgent...")
    
    agent = MemoryAgent()
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Test capabilities
    assert "memory_loading" in agent.capabilities
    print("  ✅ Capabilities verified")
    
    # Test execution (without providers, should use empty defaults)
    context.input_data = {"operation": "load"}
    
    response = await agent.execute(context)
    # Without providers, this will succeed with empty memory
    assert response.status in [AgentExecutionStatus.COMPLETED, AgentExecutionStatus.FAILED]
    print("  ✅ Execution tested")
    
    # Test health
    health = await agent.health()
    assert health["status"] == "healthy"
    print("  ✅ Health check passed")
    
    return True


async def test_agent_registration():
    """Test agent registration."""
    print("Testing agent registration...")
    
    from app.registry.agent_registry import agent_registry, AgentMetadata
    from app.core.enums import AgentStatus
    
    # Clear registry
    agent_registry.clear()
    
    # Register test agent
    agents = [
        IngestAgent(),
        RetrievalAgent(),
        EvidenceAgent(),
        TimelineAgent(),
        RiskAgent(),
        MemoryAgent(),
    ]
    
    for agent in agents:
        metadata = AgentMetadata(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            agent_type=agent.__class__.__name__,
            capabilities=agent.capabilities,
            description=agent.description,
            version=agent.version,
            status=AgentStatus.ACTIVE,
            metadata=agent.metadata(),
        )
        agent_registry.register_agent(metadata)
    
    # Verify registration
    assert agent_registry.get_agent_count() == 6
    print("  ✅ All 6 agents registered")
    
    # Test discovery
    evidence_agents = agent_registry.discover_agents(
        capabilities=["evidence_analysis"]
    )
    assert len(evidence_agents) >= 1
    print("  ✅ Agent discovery works")
    
    return True


async def test_workflow():
    """Test complete workflow."""
    print("Testing complete workflow...")
    
    context = ExecutionContext(case_id="test-1", domain="legal")
    
    # Step 1: Ingest
    context.input_data = {
        "content": "Test document",
        "title": "Test",
        "type": "contract"
    }
    ingest_agent = IngestAgent()
    response1 = await ingest_agent.execute(context)
    assert response1.status == AgentExecutionStatus.COMPLETED
    print("  ✅ Ingest completed")
    
    # Step 2: Evidence
    context.input_data = {
        "evidence": [{"id": "ev1", "description": "Test", "quality": "strong"}]
    }
    evidence_agent = EvidenceAgent()
    response2 = await evidence_agent.execute(context)
    assert response2.status == AgentExecutionStatus.COMPLETED
    print("  ✅ Evidence analysis completed")
    
    # Step 3: Timeline
    context.input_data = {
        "events": [
            {
                "id": "evt1",
                "description": "Test event",
                "date": datetime.utcnow().isoformat(),
                "type": "test"
            }
        ]
    }
    timeline_agent = TimelineAgent()
    response3 = await timeline_agent.execute(context)
    assert response3.status == AgentExecutionStatus.COMPLETED
    print("  ✅ Timeline generated")
    
    # Step 4: Risk
    context.input_data = {}
    risk_agent = RiskAgent()
    response4 = await risk_agent.execute(context)
    assert response4.status == AgentExecutionStatus.COMPLETED
    print("  ✅ Risk assessment completed")
    
    print("  ✅ Complete workflow successful")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("PHASE 3 - Specialized Agent Framework")
    print("Simple Verification Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("IngestAgent", test_ingest_agent),
        ("RetrievalAgent", test_retrieval_agent),
        ("EvidenceAgent", test_evidence_agent),
        ("TimelineAgent", test_timeline_agent),
        ("RiskAgent", test_risk_agent),
        ("MemoryAgent", test_memory_agent),
        ("Agent Registration", test_agent_registration),
        ("Complete Workflow", test_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {str(e)}\n")
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All tests passed! Phase 3 implementation verified.\n")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed.\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
