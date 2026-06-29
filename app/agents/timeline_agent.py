"""
Timeline Agent - AI-powered timeline generation.
"""

from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.ai_models import TimelineResponse
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.llm import get_openrouter_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.memory import get_memory_manager
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class TimelineAgent(BaseAgent):
    """
    AI-powered Timeline Agent.
    """

    def __init__(self):
        super().__init__(
            agent_id="timeline_agent",
            name="Timeline Agent",
            description="AI-powered timeline generation",
            version="2.0.0",
            supported_domains=["legal", "healthcare", "insurance", "project_management", "*"],
            priority=7,
        )
        self.openrouter_service = get_openrouter_service()
        self.prompt_manager = get_prompt_manager()
        self.memory_manager = get_memory_manager()

    @property
    def capabilities(self) -> List[str]:
        return [
            "ai_timeline_generation",
            "deadline_tracking",
            "event_extraction",
        ]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return ["case_memory"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute AI-powered timeline generation."""
        start_time = datetime.utcnow()
        
        try:
            case_id = context.input_data.get("case_id", "")
            retrieved_docs = context.get_shared("retrieved_documents", [])
            memory_context = await self.memory_manager.get_memory_context(case_id)
            
            knowledge_text = "\n\n".join([
                f"{doc.content[:200]}" for doc in retrieved_docs[:5]
            ]) if retrieved_docs else "No documents."
            
            prompt = self.prompt_manager.get_prompt(
                PromptTemplate.TIMELINE,
                {
                    "case_id": case_id,
                    "case_context": str(context.input_data),
                    "retrieved_knowledge": knowledge_text,
                    "memory_context": str(memory_context)
                }
            )
            
            from pydantic import BaseModel
            from app.schemas.report import TimelineEvent
            
            class TimelineExtraction(BaseModel):
                timeline: List[TimelineEvent]
            
            ai_response = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=TimelineExtraction,
                system_prompt="You are an expert legal AI. Extract a chronological timeline of events from the provided text."
            )
            
            context.set_shared("timeline", [event.dict() for event in ai_response.timeline])
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output=ai_response.dict(),
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Timeline agent failed", error=str(e), request_id=context.request_id)
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

    async def _validate_execution(self, context: ExecutionContext) -> None:
        pass
