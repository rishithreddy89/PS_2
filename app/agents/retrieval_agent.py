"""
Retrieval Agent - AI-powered knowledge retrieval.
"""

from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.ai_models import RetrievalResponse
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.specialized_agents import RetrievalRequest, SearchIntent, SearchSource
from app.knowledge import get_retrieval_service
from app.llm import get_openrouter_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.memory import get_memory_manager
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class RetrievalAgent(BaseAgent):
    """
    AI-powered Retrieval Agent for intelligent knowledge retrieval.
    """

    def __init__(self):
        super().__init__(
            agent_id="retrieval_agent",
            name="Retrieval Agent",
            description="AI-powered knowledge retrieval with hybrid search",
            version="2.0.0",
            supported_domains=["legal", "healthcare", "insurance", "finance", "*"],
            priority=7,
        )
        self.retrieval_service = get_retrieval_service()
        self.openrouter_service = get_openrouter_service()
        self.prompt_manager = get_prompt_manager()
        self.memory_manager = get_memory_manager()

    @property
    def capabilities(self) -> List[str]:
        return [
            "ai_powered_retrieval",
            "hybrid_search",
            "intent_detection",
            "semantic_search",
        ]

    @property
    def required_tools(self) -> List[str]:
        return ["chromadb", "openrouter"]

    @property
    def required_memory(self) -> List[str]:
        return ["case_memory"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute AI-powered retrieval."""
        start_time = datetime.utcnow()
        
        try:
            case_id = context.case_id or context.input_data.get("case_id", "")
            if not case_id:
                raise ValueError("case_id is required for case-specific retrieval")
                
            query = context.input_data.get("query", "facts, evidence, events, and timeline")
            case_type = context.input_data.get("case_type", "general")
            
            # Fetch from case documents
            initial_filters = {"case_id": case_id}
            initial_collection = "case_documents"
            from app.knowledge.local_embedding import get_local_embedding_service
            embedding_svc = get_local_embedding_service()
            
            logger.info(
                "Initiating retrieval",
                query=query,
                collection_used=initial_collection,
                filters_applied=initial_filters,
                embedding_model=embedding_svc.model_name
            )
            
            retrieved_docs = await self.retrieval_service.retrieve(
                query=query,
                collections=[initial_collection],
                top_k=20,
                filters=initial_filters
            )
            
            if not retrieved_docs:
                logger.warning("Zero chunks returned with initial query. Attempting Fallback 1: No metadata filter, top_k=20.", case_id=case_id)
                retrieved_docs = await self.retrieval_service.retrieve(
                    query=query,
                    collections=[initial_collection],
                    top_k=20,
                    filters=None
                )
                if retrieved_docs:
                    logger.info("Fallback 1 succeeded. The metadata filter caused the initial failure.", failed_filter=initial_filters)
                
            if not retrieved_docs:
                logger.error("Zero chunks returned after all fallbacks. Exact reason: No matching chunks found in the index for the given query and collection. Check ChromaDB state.", case_id=case_id)
            else:
                logger.info(
                    "Retrieved case documents", 
                    case_id=case_id, 
                    count=len(retrieved_docs),
                    query=query,
                    retrieved_chunk_ids=[d.chunk_id for d in retrieved_docs],
                    similarity_scores=[d.final_score for d in retrieved_docs],
                    collection_used=initial_collection,
                    embedding_model=embedding_svc.model_name
                )
                for idx, doc in enumerate(retrieved_docs):
                    logger.debug(f"Retrieved chunk {idx}", chunk_id=doc.chunk_id, score=doc.final_score, metadata=doc.metadata, content_preview=doc.content[:100])
            
            # Optionally format for LLM if needed, though we rely on specialized agents later
            knowledge_text = "\n\n".join([
                f"[Doc: {doc.document_id} | Type: {doc.metadata.get('document_type', 'unknown')}]\n{doc.content}"
                for doc in retrieved_docs
            ])
            
            context.set_shared("retrieved_documents", retrieved_docs)
            context.set_shared("retrieved_knowledge_text", knowledge_text)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={
                    "retrieved_count": len(retrieved_docs),
                    "query_used": query
                },
                duration_ms=duration,
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("Retrieval agent failed", error=str(e), request_id=context.request_id)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration,
            )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate execution context."""
        return bool(context.case_id or context.input_data.get("case_id"))
