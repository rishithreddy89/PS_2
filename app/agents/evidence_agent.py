"""
Evidence Agent - AI-powered evidence analysis.
"""

from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.ai_models import EvidenceResponse
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.specialized_agents import EvidenceSummary, EvidenceQuality
from app.llm import get_openrouter_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.memory import get_memory_manager
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class EvidenceAgent(BaseAgent):
    """
    AI-powered Evidence Agent for intelligent evidence analysis.
    """

    def __init__(self):
        super().__init__(
            agent_id="evidence_agent",
            name="Evidence Agent",
            description="AI-powered evidence quality analysis",
            version="2.0.0",
            supported_domains=["legal", "insurance", "compliance", "*"],
            priority=8,
        )
        self.openrouter_service = get_openrouter_service()
        self.prompt_manager = get_prompt_manager()
        self.memory_manager = get_memory_manager()

    @property
    def capabilities(self) -> List[str]:
        return [
            "ai_evidence_analysis",
            "quality_assessment",
            "gap_identification",
            "conflict_detection",
        ]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return ["case_memory"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute AI-powered evidence analysis."""
        start_time = datetime.utcnow()
        
        try:
            await self._validate_execution(context)
            
            case_id = context.input_data.get("case_id", "")
            case_type = context.input_data.get("case_type", "general")
            
            retrieved_docs = context.get_shared("retrieved_documents", [])
            memory_context = await self.memory_manager.get_memory_context(case_id)
            
            knowledge_text = "\n\n".join([
                f"{doc.content[:200]}" for doc in retrieved_docs[:5]
            ]) if retrieved_docs else "No evidence documents retrieved."
            
            prompt = self.prompt_manager.get_prompt(
                PromptTemplate.EVIDENCE,
                {
                    "case_id": case_id,
                    "case_type": case_type,
                    "retrieved_knowledge": knowledge_text,
                    "memory_context": str(memory_context.get("feedback", []))
                }
            )
            
            from pydantic import BaseModel
            from app.schemas.report import EvidenceItem, Contradiction
            
            class EvidenceExtraction(BaseModel):
                evidence_matrix: List[EvidenceItem]
                contradictions: List[Contradiction]
                missing_evidence: List[str]
            
            ai_response = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=EvidenceExtraction,
                system_prompt="You are an expert legal AI. Extract a detailed evidence matrix, identify any contradictions, and list missing documents that would strengthen the case based on the provided text."
            )
            
            context.set_shared("evidence_matrix", [item.dict() for item in ai_response.evidence_matrix])
            context.set_shared("contradictions", [c.dict() for c in ai_response.contradictions])
            context.set_shared("missing_evidence", ai_response.missing_evidence)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output=ai_response.dict(),
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Evidence agent failed", error=str(e), request_id=context.request_id)
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
        return True

    async def _validate_execution(self, context: ExecutionContext) -> None:
        """Validate before execution."""
        if not await self.validate(context):
            raise ValueError("Invalid execution context")
