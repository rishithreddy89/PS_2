"""
Legal Issue Agent - Identifies legal issues from case evidence.
"""

from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.llm import get_openrouter_service
from app.prompts import get_prompt_manager, PromptTemplate
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class LegalIssueAgent(BaseAgent):
    """
    AI-powered Legal Issue Agent.
    """

    def __init__(self):
        super().__init__(
            agent_id="legal_issue_agent",
            name="Legal Issue Agent",
            description="AI-powered identification of legal issues (e.g., retaliation, discrimination).",
            version="1.0.0",
            supported_domains=["legal", "*"],
            priority=8,
        )
        self.openrouter_service = get_openrouter_service()
        self.prompt_manager = get_prompt_manager()

    @property
    def capabilities(self) -> List[str]:
        return ["legal_issue_identification"]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute AI-powered legal issue identification."""
        start_time = datetime.utcnow()
        
        try:
            case_id = context.input_data.get("case_id", "")
            retrieved_docs = context.get_shared("retrieved_documents", [])
            
            knowledge_text = "\n\n".join([
                f"{doc.content[:200]}" for doc in retrieved_docs[:5]
            ]) if retrieved_docs else "No documents."
            
            prompt = self.prompt_manager.get_prompt(
                PromptTemplate.EVIDENCE,  # Reusing evidence prompt template as base
                {
                    "case_id": case_id,
                    "case_type": context.input_data.get("case_type", "general"),
                    "retrieved_knowledge": knowledge_text,
                    "memory_context": ""
                }
            )
            
            from pydantic import BaseModel
            from app.schemas.report import LegalIssue
            
            class LegalIssueExtraction(BaseModel):
                legal_issues: List[LegalIssue]
            
            ai_response = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=LegalIssueExtraction,
                system_prompt="You are an expert legal AI. Identify the most likely legal issues (e.g., retaliation, discrimination, contract breach) based on the provided text."
            )
            
            context.set_shared("legal_issues", [issue.dict() for issue in ai_response.legal_issues])
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output=ai_response.dict(),
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Legal issue agent failed", error=str(e), request_id=context.request_id)
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
