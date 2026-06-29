"""
Sample agents for testing and demonstration.
"""

from typing import List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class AnalysisAgent(BaseAgent):
    """Sample analysis agent."""

    def __init__(self):
        super().__init__(
            agent_id="analysis_agent",
            name="Analysis Agent",
            description="Performs data analysis",
            version="1.0.0",
            supported_domains=["*"],
            priority=10,
        )

    @property
    def capabilities(self) -> List[str]:
        return ["analysis", "data_processing"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute analysis."""
        logger.info("Analysis agent executing", request_id=context.request_id)
        
        # Simulate analysis
        input_data = context.input_data
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            status=AgentExecutionStatus.COMPLETED,
            output={
                "analysis_result": "Data analyzed successfully",
                "insights": ["Insight 1", "Insight 2"],
                "processed_items": len(input_data),
            },
            duration_ms=100.0,
        )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate context."""
        return context.input_data is not None


class RecommendationAgent(BaseAgent):
    """Sample recommendation agent."""

    def __init__(self):
        super().__init__(
            agent_id="recommendation_agent",
            name="Recommendation Agent",
            description="Generates recommendations",
            version="1.0.0",
            supported_domains=["*"],
            priority=5,
        )

    @property
    def capabilities(self) -> List[str]:
        return ["recommendation", "decision_support"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute recommendation generation."""
        logger.info("Recommendation agent executing", request_id=context.request_id)
        
        # Get analysis output if available
        analysis_output = context.get_agent_output("analysis_agent")
        
        recommendations = [
            "Recommendation 1: Based on analysis",
            "Recommendation 2: Consider this action",
        ]
        
        if analysis_output:
            recommendations.append(
                f"Recommendation 3: Follow up on {len(analysis_output.output.get('insights', []))} insights"
            )
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            status=AgentExecutionStatus.COMPLETED,
            output={
                "recommendations": recommendations,
                "confidence": 0.85,
                "reasoning": "Generated based on input data and analysis",
            },
            duration_ms=150.0,
        )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate context."""
        return True


class DocumentParsingAgent(BaseAgent):
    """Sample document parsing agent."""

    def __init__(self):
        super().__init__(
            agent_id="document_parser",
            name="Document Parser Agent",
            description="Parses and extracts document content",
            version="1.0.0",
            supported_domains=["*"],
            priority=20,
        )

    @property
    def capabilities(self) -> List[str]:
        return ["document_parsing", "extraction"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute document parsing."""
        logger.info("Document parser executing", request_id=context.request_id)
        
        documents = context.input_data.get("documents", [])
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            status=AgentExecutionStatus.COMPLETED,
            output={
                "parsed_documents": len(documents),
                "extracted_text": f"Extracted content from {len(documents)} documents",
                "metadata": {"format": "text", "encoding": "utf-8"},
            },
            duration_ms=200.0,
        )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate context."""
        return "documents" in context.input_data
