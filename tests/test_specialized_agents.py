"""
Unit tests for specialized agents.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.context import ExecutionContext
from app.agents.evidence_agent import EvidenceAgent
from app.agents.ingest_agent import IngestAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.risk_agent import RiskAgent
from app.agents.timeline_agent import TimelineAgent
from app.schemas.agent import AgentExecutionStatus
from app.schemas.specialized_agents import (
    DocumentCategory,
    EvidenceQuality,
    RiskLevel,
    SearchIntent,
)


# ============================================================================
# INGEST AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestIngestAgent:
    """Tests for IngestAgent."""

    @pytest.fixture
    def agent(self):
        return IngestAgent()

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_capabilities(self, agent):
        """Test agent capabilities."""
        assert "document_ingestion" in agent.capabilities
        assert "metadata_extraction" in agent.capabilities
        assert "entity_extraction" in agent.capabilities

    async def test_execute_single_document(self, agent, context):
        """Test ingesting a single document."""
        context.input_data = {
            "content": "This is a legal contract between John Doe and Acme Corp.",
            "title": "Contract Agreement",
            "type": "contract",
        }

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "document_summaries" in response.output
        assert response.output["total_documents"] == 1
        assert response.duration_ms > 0

    async def test_execute_multiple_documents(self, agent, context):
        """Test ingesting multiple documents."""
        context.input_data = {
            "documents": [
                {"content": "Email from sender", "title": "Email", "type": "email"},
                {"content": "Court notice received", "title": "Notice", "type": "court_notice"},
            ]
        }

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert response.output["total_documents"] == 2

    async def test_detect_email_category(self, agent, context):
        """Test email category detection."""
        context.input_data = {
            "content": "From: sender@example.com\nTo: receiver@example.com",
            "type": "email",
        }

        response = await agent.execute(context)
        summaries = response.output["document_summaries"]
        assert summaries[0]["category"] == DocumentCategory.EMAIL

    async def test_detect_contract_category(self, agent, context):
        """Test contract category detection."""
        context.input_data = {
            "content": "This agreement is made between parties...",
            "type": "contract",
        }

        response = await agent.execute(context)
        summaries = response.output["document_summaries"]
        assert summaries[0]["category"] == DocumentCategory.CONTRACT

    async def test_entity_extraction(self, agent, context):
        """Test entity extraction."""
        context.input_data = {
            "content": "John Smith met with Mary Johnson at Microsoft headquarters.",
            "title": "Meeting Notes",
        }

        response = await agent.execute(context)
        summaries = response.output["document_summaries"]
        assert len(summaries[0]["entities"]) > 0

    async def test_validate_no_content(self, agent, context):
        """Test validation with no content."""
        context.input_data = {}
        is_valid = await agent.validate(context)
        assert is_valid is False

    async def test_execute_invalid_input(self, agent, context):
        """Test execution with invalid input."""
        context.input_data = {}
        response = await agent.execute(context)
        assert response.status == AgentExecutionStatus.FAILED
        assert response.error is not None

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"
        assert health["agent_id"] == "ingest_agent"

    async def test_metadata(self, agent):
        """Test agent metadata."""
        metadata = agent.metadata()
        assert metadata["agent_id"] == "ingest_agent"
        assert len(metadata["capabilities"]) > 0
        assert metadata["version"] == "1.0.0"


# ============================================================================
# RETRIEVAL AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestRetrievalAgent:
    """Tests for RetrievalAgent (Phase 4 - AI-powered)."""

    @pytest.fixture
    def mock_openai(self):
        from unittest.mock import AsyncMock
        from app.agents.ai_models import RetrievalResponse
        mock = AsyncMock()
        mock.complete_structured = AsyncMock(return_value=RetrievalResponse(
            search_queries=["contract dispute precedents"],
            document_types=["case_law", "statute"],
            priority_sources=["precedents"],
            reasoning="Searching for relevant legal precedents"
        ))
        return mock

    @pytest.fixture
    def mock_retrieval_service(self):
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_memory_manager(self):
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.get_memory_context = AsyncMock(return_value={
            "case_context": {}, "recommendations": [], "feedback": [], "conversation": []
        })
        return mock

    @pytest.fixture
    def agent(self, mock_openai, mock_retrieval_service, mock_memory_manager):
        a = RetrievalAgent()
        a.openai_service = mock_openai
        a.retrieval_service = mock_retrieval_service
        a.memory_manager = mock_memory_manager
        return a

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_execute_legal_research(self, agent, context):
        """Test AI-powered retrieval returns analysis and retrieved_count."""
        context.input_data = {
            "query": "Find legal precedents for contract disputes",
            "case_type": "contract",
        }

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "retrieved_count" in response.output
        assert "analysis" in response.output

    async def test_validate_no_query(self, agent, context):
        """Test validation with no query."""
        context.input_data = {}
        is_valid = await agent.validate(context)
        assert is_valid is False

    async def test_execute_invalid_input(self, agent, context):
        """Test execution with invalid input fails gracefully."""
        context.input_data = {}
        response = await agent.execute(context)
        assert response.status == AgentExecutionStatus.FAILED

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"


# ============================================================================
# EVIDENCE AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestEvidenceAgent:
    """Tests for EvidenceAgent (Phase 4 - AI-powered)."""

    @pytest.fixture
    def mock_openai(self):
        from unittest.mock import AsyncMock
        from app.agents.ai_models import EvidenceResponse, EvidenceAnalysis
        mock = AsyncMock()
        mock.complete_structured = AsyncMock(return_value=EvidenceResponse(
            strong_evidence=[EvidenceAnalysis(id="ev1", description="Contract signed", quality="strong")],
            weak_evidence=[EvidenceAnalysis(id="ev2", description="Hearsay", quality="weak")],
            missing_evidence=["Financial records"],
            conflicts=[],
            overall_strength="moderate",
            reasoning="Analysis of provided evidence"
        ))
        return mock

    @pytest.fixture
    def mock_memory_manager(self):
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.get_memory_context = AsyncMock(return_value={
            "case_context": {}, "recommendations": [], "feedback": [], "conversation": []
        })
        return mock

    @pytest.fixture
    def agent(self, mock_openai, mock_memory_manager):
        a = EvidenceAgent()
        a.openai_service = mock_openai
        a.memory_manager = mock_memory_manager
        return a

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_execute_with_evidence(self, agent, context):
        """Test analyzing evidence returns AI response."""
        context.input_data = {"case_id": "test-case-1", "case_type": "contract"}

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "evidence_analysis" in response.output

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"


# ============================================================================
# TIMELINE AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestTimelineAgent:
    """Tests for TimelineAgent (Phase 4 - AI-powered)."""

    @pytest.fixture
    def mock_openai(self):
        from unittest.mock import AsyncMock
        from app.agents.ai_models import TimelineResponse, TimelineEventModel
        mock = AsyncMock()
        mock.complete_structured = AsyncMock(return_value=TimelineResponse(
            events=[
                TimelineEventModel(
                    date="2024-01-15",
                    description="Court hearing scheduled",
                    type="hearing",
                    is_deadline=True,
                    is_urgent=False
                )
            ],
            critical_deadlines=["2024-01-15: Court hearing"],
            overdue_items=[]
        ))
        return mock

    @pytest.fixture
    def mock_memory_manager(self):
        from unittest.mock import AsyncMock
        mock = AsyncMock()
        mock.get_memory_context = AsyncMock(return_value={
            "case_context": {}, "recommendations": [], "feedback": [], "conversation": []
        })
        return mock

    @pytest.fixture
    def agent(self, mock_openai, mock_memory_manager):
        a = TimelineAgent()
        a.openai_service = mock_openai
        a.memory_manager = mock_memory_manager
        return a

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_execute_returns_timeline(self, agent, context):
        """Test AI-powered timeline generation returns timeline_analysis."""
        context.input_data = {"case_id": "test-case-1"}

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "timeline_analysis" in response.output
        assert "events" in response.output["timeline_analysis"]

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"


# ============================================================================
# RISK AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestRiskAgent:
    """Tests for RiskAgent (Phase 4 - AI-powered)."""

    @pytest.fixture
    def mock_openai(self):
        from unittest.mock import AsyncMock
        from app.agents.ai_models import RiskResponse, RiskItemModel
        mock = AsyncMock()
        mock.complete_structured = AsyncMock(return_value=RiskResponse(
            risks=[
                RiskItemModel(
                    risk_id="R1",
                    type="legal",
                    description="Missing critical evidence",
                    severity="high",
                    probability=0.8,
                    impact="Case weakened",
                    mitigation="Gather missing evidence"
                )
            ],
            overall_risk_level="high",
            risk_score=70.0
        ))
        return mock

    @pytest.fixture
    def mock_memory_manager(self):
        from unittest.mock import AsyncMock, MagicMock
        mock = AsyncMock()
        mock.get_memory_context = AsyncMock(return_value={
            "case_context": {}, "recommendations": [], "feedback": [], "conversation": []
        })
        mock.case_memory = AsyncMock()
        mock.case_memory.set = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def agent(self, mock_openai, mock_memory_manager):
        a = RiskAgent()
        a.openai_service = mock_openai
        a.memory_manager = mock_memory_manager
        return a

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_execute_risk_assessment(self, agent, context):
        """Test AI-powered risk assessment."""
        context.input_data = {"case_id": "test-case-1", "case_type": "contract"}

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        summary = response.output["risk_summary"]
        assert "total_risks" in summary
        assert summary["total_risks"] >= 1

    async def test_overall_risk_level_in_output(self, agent, context):
        """Test overall_risk_level is present in summary."""
        context.input_data = {"case_id": "test-case-1"}
        response = await agent.execute(context)
        summary = response.output["risk_summary"]
        assert summary["overall_risk_level"] in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]

    async def test_risk_score_in_range(self, agent, context):
        """Test risk score is between 0 and 100."""
        context.input_data = {"case_id": "test-case-1"}
        response = await agent.execute(context)
        summary = response.output["risk_summary"]
        assert 0.0 <= summary["risk_score"] <= 100.0

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"


# ============================================================================
# MEMORY AGENT TESTS
# ============================================================================


@pytest.mark.asyncio
class TestMemoryAgent:
    """Tests for MemoryAgent."""

    @pytest.fixture
    def mock_short_term(self):
        mock = AsyncMock()
        mock.get = AsyncMock(return_value={"key": "value"})
        mock.set = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def mock_long_term(self):
        mock = AsyncMock()
        mock.get = AsyncMock(return_value={"history": "data"})
        mock.set = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def mock_conversation(self):
        mock = AsyncMock()
        mock.get_history = AsyncMock(return_value=[{"role": "user", "content": "Hello"}])
        return mock

    @pytest.fixture
    def mock_case_memory(self):
        mock = AsyncMock()
        mock.get_case_context = AsyncMock(return_value={"case_data": "value"})
        mock.set_case_context = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def agent(self, mock_short_term, mock_long_term, mock_conversation, mock_case_memory):
        return MemoryAgent(
            short_term=mock_short_term,
            long_term=mock_long_term,
            conversation=mock_conversation,
            case_memory=mock_case_memory,
        )

    @pytest.fixture
    def context(self):
        return ExecutionContext(
            case_id="test-case-1",
            user_id="test-user-1",
            domain="legal",
        )

    async def test_load_memory(self, agent, context):
        """Test loading memory from providers."""
        context.input_data = {"operation": "load"}

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        assert "memory_context" in response.output
        assert response.output["memory_context"]["case_id"] == "test-case-1"

    async def test_store_memory(self, agent, context):
        """Test storing memory to providers."""
        context.input_data = {
            "operation": "store",
            "memory_data": {"long_term": {"key": "value"}},
        }

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        agent.short_term.set.assert_called()

    async def test_update_memory(self, agent, context):
        """Test updating existing memory."""
        context.input_data = {
            "operation": "update",
            "updates": {"short_term": {"new_key": "new_value"}},
        }

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        agent.short_term.set.assert_called()

    async def test_merge_context(self, agent, context):
        """Test merging context for LLM prompts."""
        context.input_data = {"operation": "merge"}
        context.set_shared("test_key", "test_value")

        response = await agent.execute(context)

        assert response.status == AgentExecutionStatus.COMPLETED
        memory_ctx = response.output["memory_context"]
        assert "case_specific" in memory_ctx

    async def test_validate_invalid_operation(self, agent, context):
        """Test validation with invalid operation."""
        context.input_data = {"operation": "invalid"}
        is_valid = await agent.validate(context)
        assert is_valid is False

    async def test_execute_invalid_operation(self, agent, context):
        """Test execution with invalid operation."""
        context.input_data = {"operation": "invalid"}
        response = await agent.execute(context)
        assert response.status == AgentExecutionStatus.FAILED

    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health()
        assert health["status"] == "healthy"

    async def test_metadata(self, agent):
        """Test agent metadata."""
        metadata = agent.metadata()
        assert metadata["agent_id"] == "memory_agent"
        assert "memory_loading" in metadata["capabilities"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
class TestAgentIntegration:
    """Integration tests for agent workflows."""

    async def test_document_ingestion_workflow(self):
        """Test ingest agent works standalone."""
        context = ExecutionContext(case_id="test-case-1", domain="legal")

        ingest_agent = IngestAgent()
        context.input_data = {
            "documents": [
                {
                    "content": "Contract signed on 2024-01-01",
                    "title": "Contract",
                    "type": "contract",
                }
            ]
        }
        ingest_response = await ingest_agent.execute(context)
        assert ingest_response.status == AgentExecutionStatus.COMPLETED
        assert ingest_response.output["total_documents"] == 1

    async def test_shared_context_propagation(self):
        """Test shared context propagates between agents correctly."""
        context = ExecutionContext(case_id="test-case-1", domain="legal")
        context.set_shared("retrieved_documents", [])
        context.set_shared("evidence_analysis", {"overall_strength": "moderate"})
        context.set_shared("timeline_analysis", {"events": []})

        assert context.get_shared("retrieved_documents") == []
        assert context.get_shared("evidence_analysis") is not None
        assert context.get_shared("timeline_analysis") is not None
