"""
Risk Agent - AI-powered risk identification and assessment.
"""

from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.ai_models import RiskResponse
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.specialized_agents import RiskItem, RiskLevel, RiskSummary
from app.llm import get_openrouter_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.memory import get_memory_manager
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class RiskAgent(BaseAgent):
    """
    AI-powered Risk Agent for intelligent risk identification and assessment.
    """

    def __init__(self):
        super().__init__(
            agent_id="risk_agent",
            name="Risk Agent",
            description="AI-powered risk identification and assessment",
            version="2.0.0",
            supported_domains=["legal", "healthcare", "insurance", "finance", "compliance", "*"],
            priority=9,
        )
        self.openrouter_service = get_openrouter_service()
        self.prompt_manager = get_prompt_manager()
        self.memory_manager = get_memory_manager()

    @property
    def capabilities(self) -> List[str]:
        return [
            "ai_risk_assessment",
            "risk_identification",
            "severity_classification",
            "risk_prioritization",
        ]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return ["case_memory", "long_term"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute AI-powered risk assessment."""
        start_time = datetime.utcnow()

        try:
            case_id = context.input_data.get("case_id", "") or context.case_id or ""
            case_type = context.input_data.get("case_type", "general")

            evidence_analysis = context.get_shared("evidence_analysis") or {}
            timeline_analysis = context.get_shared("timeline_analysis") or {}
            memory_context = await self.memory_manager.get_memory_context(case_id)

            evidence_summary = str(evidence_analysis)[:500] if evidence_analysis else "No evidence analysis available."
            timeline_summary = str(timeline_analysis)[:500] if timeline_analysis else "No timeline analysis available."

            prompt = self.prompt_manager.get_prompt(
                PromptTemplate.RISK,
                {
                    "case_id": case_id,
                    "case_type": case_type,
                    "case_context": str(context.input_data),
                    "retrieved_knowledge": str(context.get_shared("retrieved_documents", []))[:300],
                    "evidence_summary": evidence_summary,
                    "timeline_summary": timeline_summary,
                    "memory_context": str(memory_context.get("feedback", []))
                }
            )

            from pydantic import BaseModel
            from app.schemas.report import RiskScores
            
            ai_response = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=RiskScores,
                system_prompt="You are an expert legal AI. Calculate numerical percentage risk scores (0-100) based on the evidence."
            )

            context.set_shared("risk_assessment", ai_response.dict())

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output=ai_response.dict(),
                duration_ms=duration,
            )

        except Exception as e:
            logger.error("Risk agent failed", error=str(e), request_id=context.request_id)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration,
            )

    async def validate(self, context: ExecutionContext) -> bool:
        return True
