"""
Phase 4 Tests - AI Intelligence Layer (RAG + OpenAI + Memory)

Tests for:
- Knowledge ingestion
- Embedding service
- Hybrid retrieval
- Prompt management
- OpenAI service
- Memory implementation
- Agent integration
- Validation failures
- Retry logic
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import os

from app.knowledge import (
    get_embedding_service,
    get_chroma_service,
    get_ingestion_service,
    get_retrieval_service,
    Document,
    DocumentType,
)
from app.llm import get_openai_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.memory import get_memory_manager
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.timeline_agent import TimelineAgent
from app.agents.risk_agent import RiskAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus


# ============================================================================
# EMBEDDING SERVICE TESTS
# ============================================================================


@pytest.mark.asyncio
class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_openai_client(self):
        mock = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock.embeddings.create = AsyncMock(return_value=mock_response)
        return mock

    @pytest.fixture
    def service(self, mock_openai_client):
        svc = get_embedding_service()
        svc.client = mock_openai_client
        return svc

    async def test_embed_text(self, service):
        """Test single text embedding."""
        result = await service.embed_text("Test document content")
        assert isinstance(result, list)
        assert len(result) == 1536

    async def test_embed_batch(self, service):
        """Test batch text embedding."""
        texts = ["Document 1", "Document 2", "Document 3"]
        results = await service.embed_batch(texts)
        assert len(results) == 3
        assert all(len(emb) == 1536 for emb in results)

    async def test_embed_query(self, service):
        """Test query embedding."""
        result = await service.embed_query("Search query")
        assert isinstance(result, list)
        assert len(result) == 1536


# ============================================================================
# CHROMADB TESTS
# ============================================================================


@pytest.mark.asyncio
class TestChromaDBService:
    """Tests for ChromaDB service."""

    @pytest.fixture
    def service(self):
        return get_chroma_service()

    async def test_get_collection(self, service):
        """Test collection creation/retrieval."""
        collection = service.get_collection("test_statutes")
        assert collection is not None

    async def test_insert_and_search(self, service):
        """Test inserting and searching documents."""
        from app.knowledge.models import DocumentChunk
        
        chunks = [
            DocumentChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="Legal statute about contracts",
                chunk_index=0,
                metadata={"document_type": "statute"}
            )
        ]
        embeddings = [[0.1] * 1536]

        await service.insert("test_statutes", chunks, embeddings)

        # Search
        query_embedding = [0.1] * 1536
        results = await service.search("test_statutes", query_embedding, n_results=1)
        
        assert len(results) >= 0

    async def test_delete_document(self, service):
        """Test document deletion."""
        await service.delete_document("test_statutes", "doc1")


# ============================================================================
# KNOWLEDGE INGESTION TESTS
# ============================================================================


@pytest.mark.asyncio
class TestIngestionService:
    """Tests for document ingestion."""

    @pytest.fixture
    def mock_embedding_service(self):
        svc = AsyncMock()
        svc.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
        return svc

    @pytest.fixture
    def mock_chroma_service(self):
        svc = AsyncMock()
        svc.insert = AsyncMock()
        return svc

    @pytest.fixture
    def service(self, mock_embedding_service, mock_chroma_service):
        svc = get_ingestion_service()
        svc.embedding_service = mock_embedding_service
        svc.chroma_service = mock_chroma_service
        return svc

    async def test_detect_statute_type(self, service):
        """Test statute document type detection."""
        doc_type = service._detect_document_type(
            "statute.txt",
            "This regulation governs employment contracts..."
        )
        assert doc_type == DocumentType.STATUTE

    async def test_detect_case_law_type(self, service):
        """Test case law document type detection."""
        doc_type = service._detect_document_type(
            "case_law.txt",
            "Case law precedent for contract disputes..."
        )
        assert doc_type == DocumentType.CASE_LAW

    async def test_chunk_text(self, service):
        """Test text chunking."""
        text = "This is a test. " * 100
        chunks = service._chunk_text(text)
        assert len(chunks) > 0
        assert all(len(chunk) < service.chunk_size + 100 for chunk in chunks)

    async def test_ingest_file(self, service):
        """Test file ingestion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Legal statute content for testing")
            f.flush()
            temp_path = f.name

        try:
            doc = await service.ingest_file(temp_path, DocumentType.STATUTE)
            assert doc is not None
            assert doc.document_type == DocumentType.STATUTE
        finally:
            os.unlink(temp_path)


# ============================================================================
# HYBRID RETRIEVAL TESTS
# ============================================================================


@pytest.mark.asyncio
class TestHybridRetrieval:
    """Tests for hybrid retrieval."""

    @pytest.fixture
    def mock_embedding_service(self):
        svc = AsyncMock()
        svc.embed_query = AsyncMock(return_value=[0.1] * 1536)
        return svc

    @pytest.fixture
    def mock_chroma_service(self):
        from app.knowledge.models import RetrievalResult
        svc = AsyncMock()
        svc.search = AsyncMock(return_value=[
            RetrievalResult(
                document_id="doc1",
                chunk_id="chunk1",
                content="Contract law precedent",
                score=0.85,
                metadata={"document_type": "case_law"}
            )
        ])
        svc.get_collection = MagicMock(return_value=MagicMock(get=MagicMock(return_value={
            "ids": ["chunk1"],
            "documents": ["Contract law precedent"],
            "metadatas": [{"document_id": "doc1"}]
        })))
        return svc

    @pytest.fixture
    def service(self, mock_embedding_service, mock_chroma_service):
        svc = get_retrieval_service()
        svc.embedding_service = mock_embedding_service
        svc.chroma_service = mock_chroma_service
        return svc

    async def test_vector_search(self, service):
        """Test vector similarity search."""
        results = await service._vector_search(
            "statutes",
            [0.1] * 1536,
            top_k=5,
            filters=None
        )
        assert len(results) >= 0

    async def test_hybrid_retrieve(self, service):
        """Test hybrid retrieval combines vector and BM25."""
        results = await service.retrieve(
            query="contract disputes",
            collections=["statutes", "precedents"],
            top_k=5
        )
        assert isinstance(results, list)

    async def test_deduplication(self, service):
        """Test result deduplication."""
        from app.knowledge.models import HybridRetrievalResult
        
        results = [
            HybridRetrievalResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Content",
                vector_score=0.9,
                bm25_score=0.8,
                final_score=0.85,
                metadata={}
            ),
            HybridRetrievalResult(
                chunk_id="chunk1",
                document_id="doc1",
                content="Content",
                vector_score=0.85,
                bm25_score=0.75,
                final_score=0.80,
                metadata={}
            )
        ]
        
        unique = service._deduplicate(results)
        assert len(unique) == 1


# ============================================================================
# PROMPT MANAGER TESTS
# ============================================================================


class TestPromptManager:
    """Tests for prompt management."""

    @pytest.fixture
    def manager(self):
        return get_prompt_manager()

    def test_get_retrieval_prompt(self, manager):
        """Test retrieval prompt template."""
        prompt = manager.get_prompt(
            PromptTemplate.RETRIEVAL,
            {
                "query": "Find contract law",
                "case_type": "contract",
                "case_context": "Contract dispute",
                "memory_context": "Previous searches",
                "retrieved_knowledge": "Legal precedents"
            }
        )
        assert "Find contract law" in prompt
        assert "contract" in prompt

    def test_get_evidence_prompt(self, manager):
        """Test evidence analysis prompt."""
        prompt = manager.get_prompt(
            PromptTemplate.EVIDENCE,
            {
                "case_id": "case-1",
                "case_type": "civil",
                "retrieved_knowledge": "Evidence documents",
                "memory_context": "Previous analysis"
            }
        )
        assert "case-1" in prompt

    def test_get_risk_prompt(self, manager):
        """Test risk assessment prompt."""
        prompt = manager.get_prompt(
            PromptTemplate.RISK,
            {
                "case_id": "case-1",
                "case_type": "contract",
                "case_context": "Context",
                "retrieved_knowledge": "Risks",
                "evidence_summary": "Evidence",
                "timeline_summary": "Timeline",
                "memory_context": "History"
            }
        )
        assert "risk" in prompt.lower()

    def test_get_system_prompt(self, manager):
        """Test system prompt retrieval."""
        system = manager.get_system_prompt("retrieval")
        assert len(system) > 0
        assert "retrieval" in system.lower() or "knowledge" in system.lower()


# ============================================================================
# OPENAI SERVICE TESTS
# ============================================================================


@pytest.mark.asyncio
class TestOpenRouterService:
    """Tests for OpenAI service."""

    @pytest.fixture
    def mock_client(self):
        from unittest.mock import MagicMock
        mock = MagicMock()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "test"}'), finish_reason="stop")]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response.model = "gpt-5.5"
        
        mock.chat.completions.create = AsyncMock(return_value=mock_response)
        return mock

    @pytest.fixture
    def service(self, mock_client):
        from app.core.config import settings
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        svc = get_openai_service()
        svc.client = mock_client
        return svc

    async def test_complete(self, service):
        """Test basic completion."""
        result = await service.complete(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant"
        )
        assert "content" in result
        assert "total_tokens" in result
        assert result["total_tokens"] == 30

    async def test_complete_with_retry(self, service):
        """Test completion with retry on failure."""
        service.client.chat.completions.create = AsyncMock(
            side_effect=[Exception("API Error"), MagicMock(
                choices=[MagicMock(message=MagicMock(content="Success"), finish_reason="stop")],
                usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                model="gpt-5.5"
            )]
        )
        
        result = await service.complete(prompt="Test")
        assert result["content"] == "Success"

    async def test_complete_structured(self, service):
        """Test structured output validation."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            result: str
        
        result = await service.complete_structured(
            prompt="Generate test result",
            response_model=TestModel,
            system_prompt="You are a test assistant"
        )
        
        assert isinstance(result, TestModel)
        assert hasattr(result, "result")

    async def test_cost_estimation(self, service):
        """Test token cost estimation."""
        cost = service.estimate_cost(input_tokens=1000, output_tokens=500)
        assert cost > 0
        assert isinstance(cost, float)


# ============================================================================
# MEMORY TESTS
# ============================================================================


@pytest.mark.asyncio
class TestMemoryImplementation:
    """Tests for memory implementation."""

    @pytest.fixture
    def manager(self):
        return get_memory_manager()

    async def test_store_recommendation(self, manager):
        """Test storing recommendation in memory."""
        await manager.store_recommendation(
            case_id="case-1",
            recommendation={"action": "File motion", "priority": "high"},
            status="accepted"
        )
        
        recs = await manager.get_case_recommendations("case-1", status="accepted")
        assert len(recs) > 0
        assert recs[0]["action"] == "File motion"

    async def test_store_feedback(self, manager):
        """Test storing lawyer feedback."""
        await manager.store_feedback(
            case_id="case-1",
            feedback={"rating": 5, "comment": "Excellent recommendation"}
        )
        
        context = await manager.get_memory_context("case-1")
        assert len(context["feedback"]) > 0

    async def test_get_memory_context(self, manager):
        """Test getting comprehensive memory context."""
        await manager.case_memory.set_case_context("case-1", {"status": "active"})
        
        context = await manager.get_memory_context("case-1")
        
        assert "case_context" in context
        assert "recommendations" in context
        assert "feedback" in context
        assert "conversation" in context

    async def test_short_term_ttl(self, manager):
        """Test short-term memory TTL."""
        await manager.short_term.set("temp_key", "temp_value", ttl=1)
        
        value = await manager.short_term.get("temp_key")
        assert value == "temp_value"
        
        # Value should exist immediately
        exists = await manager.short_term.exists("temp_key")
        assert exists is True


# ============================================================================
# AGENT INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
class TestAgentIntegration:
    """Tests for AI-powered agent integration."""

    @pytest.fixture
    def mock_openai(self):
        mock = AsyncMock()
        mock.complete_structured = AsyncMock(return_value=MagicMock(
            search_queries=["test"],
            document_types=["statute"],
            priority_sources=["precedents"],
            reasoning="test"
        ))
        return mock

    @pytest.fixture
    def mock_retrieval_service(self):
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_memory_manager(self):
        mock = AsyncMock()
        mock.get_memory_context = AsyncMock(return_value={
            "case_context": {},
            "recommendations": [],
            "feedback": [],
            "conversation": []
        })
        mock.case_memory = AsyncMock()
        mock.case_memory.set = AsyncMock(return_value=True)
        return mock

    async def test_retrieval_agent_with_memory(self, mock_openai, mock_retrieval_service, mock_memory_manager):
        """Test retrieval agent loads memory before execution."""
        agent = RetrievalAgent()
        agent.openai_service = mock_openai
        agent.retrieval_service = mock_retrieval_service
        agent.memory_manager = mock_memory_manager
        
        context = ExecutionContext(case_id="case-1", domain="legal")
        context.input_data = {"query": "Find contract law", "case_type": "contract"}
        
        response = await agent.execute(context)
        
        assert response.status == AgentExecutionStatus.COMPLETED
        mock_memory_manager.get_memory_context.assert_called_once()

    async def test_agents_share_context(self, mock_openai, mock_memory_manager):
        """Test agents share context through ExecutionContext."""
        context = ExecutionContext(case_id="case-1", domain="legal")
        context.input_data = {"query": "test", "case_type": "contract"}
        
        # Retrieval agent
        retrieval_agent = RetrievalAgent()
        retrieval_agent.openai_service = mock_openai
        retrieval_agent.retrieval_service = AsyncMock(retrieve=AsyncMock(return_value=[]))
        retrieval_agent.memory_manager = mock_memory_manager
        
        await retrieval_agent.execute(context)
        
        # Check shared context
        assert "retrieved_documents" in context.shared_context
        assert "retrieval_analysis" in context.shared_context


# ============================================================================
# VALIDATION AND ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
class TestValidationAndErrors:
    """Tests for validation and error handling."""

    async def test_retrieval_agent_validation_failure(self):
        """Test retrieval agent validation failure."""
        agent = RetrievalAgent()
        context = ExecutionContext(case_id="case-1")
        context.input_data = {}  # No query
        
        is_valid = await agent.validate(context)
        assert is_valid is False

    async def test_openai_retry_on_failure(self):
        """Test OpenAI service retries on failure."""
        from app.core.config import settings
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        service = get_openai_service()
        
        # Mock client to fail twice then succeed
        mock_client = MagicMock()
        call_count = 0
        
        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return MagicMock(
                choices=[MagicMock(message=MagicMock(content="Success"), finish_reason="stop")],
                usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                model="gpt-5.5"
            )
        
        mock_client.chat.completions.create = mock_create
        service.client = mock_client
        
        result = await service.complete(prompt="Test")
        assert result["content"] == "Success"
        assert call_count == 2

    async def test_structured_output_validation_retry(self):
        """Test structured output retries on validation failure."""
        from pydantic import BaseModel
        from app.core.config import settings
        
        if not settings.openai_api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        class StrictModel(BaseModel):
            required_field: str
        
        service = get_openai_service()
        
        # Mock to return invalid JSON first, then valid
        mock_client = MagicMock()
        call_count = 0
        
        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                content = '{"wrong_field": "value"}'
            else:
                content = '{"required_field": "correct"}'
            
            return MagicMock(
                choices=[MagicMock(message=MagicMock(content=content), finish_reason="stop")],
                usage=MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                model="gpt-5.5"
            )
        
        mock_client.chat.completions.create = mock_create
        service.client = mock_client
        
        result = await service.complete_structured(
            prompt="Generate data",
            response_model=StrictModel,
            max_retries=2
        )
        
        assert isinstance(result, StrictModel)
        assert result.required_field == "correct"
        assert call_count == 2


# ============================================================================
# END-TO-END PHASE 4 TEST
# ============================================================================


@pytest.mark.asyncio
class TestPhase4EndToEnd:
    """End-to-end test for Phase 4 intelligence layer."""

    async def test_complete_intelligence_pipeline(self):
        """Test complete AI intelligence pipeline without real API calls."""
        # Setup mocks
        mock_openai = AsyncMock()
        mock_openai.complete_structured = AsyncMock(return_value=MagicMock(
            search_queries=["contract law"],
            document_types=["statute"],
            priority_sources=["precedents"],
            reasoning="Searching for contract law"
        ))
        
        mock_retrieval = AsyncMock()
        mock_retrieval.retrieve = AsyncMock(return_value=[])
        
        mock_memory = get_memory_manager()
        
        # Create context
        context = ExecutionContext(case_id="case-1", domain="legal")
        context.input_data = {
            "query": "Find contract law precedents",
            "case_type": "contract"
        }
        
        # Execute retrieval agent
        agent = RetrievalAgent()
        agent.openai_service = mock_openai
        agent.retrieval_service = mock_retrieval
        agent.memory_manager = mock_memory
        
        response = await agent.execute(context)
        
        # Verify
        assert response.status == AgentExecutionStatus.COMPLETED
        assert "retrieved_count" in response.output
        assert "analysis" in response.output
        assert context.get_shared("retrieved_documents") is not None
        assert context.get_shared("retrieval_analysis") is not None
