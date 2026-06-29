"""
Reflection Agent - Improves recommendations before showing users.
"""

from datetime import datetime
from typing import List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.nba import ReflectionResponse, ReflectionResult, ReflectionImprovement, NextBestAction
from app.llm import get_openrouter_service
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class ReflectionAgent(BaseAgent):
    """
    Reflection Agent reviews and improves recommendations.
    """

    def __init__(self):
        super().__init__(
            agent_id="reflection_agent",
            name="Reflection Agent",
            description="Reviews and improves recommendations",
            version="1.0.0",
            supported_domains=["legal", "*"],
            priority=8,
        )
        self.openrouter_service = get_openrouter_service()

    @property
    def capabilities(self) -> List[str]:
        return ["self_reflection", "quality_improvement", "reasoning_refinement"]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Reflect on and improve recommendations."""
        start_time = datetime.utcnow()
        
        try:
            recommendations = context.get_shared("nba_recommendations", [])
            evaluation_results = context.get_shared("evaluation_results", [])
            
            if not recommendations:
                raise ValueError("No recommendations to reflect on")
            
            prompt = self._build_reflection_prompt(recommendations, evaluation_results)
            
            system_prompt = """You are a legal reflection and improvement specialist.
Review each recommendation and decide if improvements are needed.

Check:
1. Reasoning - Is it clear, logical, and complete?
2. Confidence - Is the score well-calibrated?
3. Priority - Is it appropriate given urgency?
4. Evidence - Is supporting evidence sufficient?
5. Alternatives - Are alternative actions meaningful?

If improvements exist, suggest specific changes.
Only approve if no significant improvements needed.

Respond ONLY with valid JSON:
{
    "reflections": [
        {
            "recommendation_rank": 1,
            "needs_improvement": false,
            "improvements": [],
            "approval_status": "approved"
        }
    ],
    "revised_recommendations": null,
    "approved": true
}

If needs_improvement is true, include improvements array and optionally revised_recommendations."""
            
            result = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=ReflectionResponse,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # If revisions were made, update recommendations
            if result.revised_recommendations:
                context.set_shared("nba_recommendations", result.revised_recommendations)
                logger.info("Recommendations revised by Reflection Agent")
            
            context.set_shared("reflection_results", result.reflections)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Reflection Agent completed",
                approved=result.approved,
                revised=result.revised_recommendations is not None,
                duration_ms=duration
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={
                    "reflections": [r.dict() for r in result.reflections],
                    "approved": result.approved,
                    "revised": result.revised_recommendations is not None
                },
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Reflection Agent failed", error=str(e))
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
        return context.get_shared("nba_recommendations") is not None

    def _build_reflection_prompt(self, recommendations, evaluation_results) -> str:
        """Build reflection prompt."""
        
        recs_text = "\n\n".join([
            f"Rank {i+1}:\n"
            f"Action: {rec.action if hasattr(rec, 'action') else rec.get('action', 'N/A')}\n"
            f"Reasoning: {rec.reasoning if hasattr(rec, 'reasoning') else rec.get('reasoning', 'N/A')}\n"
            f"Confidence: {rec.confidence_score if hasattr(rec, 'confidence_score') else rec.get('confidence_score', 0)}\n"
            f"Priority: {rec.priority if hasattr(rec, 'priority') else rec.get('priority', 'N/A')}\n"
            f"Evidence: {', '.join(rec.supporting_evidence if hasattr(rec, 'supporting_evidence') else rec.get('supporting_evidence', []))}\n"
            f"Alternatives: {len(rec.alternative_actions if hasattr(rec, 'alternative_actions') else rec.get('alternative_actions', []))}"
            for i, rec in enumerate(recommendations[:3])
        ])
        
        eval_text = "\n".join([
            f"Rank {e.recommendation_rank if hasattr(e, 'recommendation_rank') else e.get('recommendation_rank', i+1)}: "
            f"Score {e.overall_score if hasattr(e, 'overall_score') else e.get('overall_score', 0):.2f}, "
            f"Passed: {e.passed if hasattr(e, 'passed') else e.get('passed', False)}"
            for i, e in enumerate(evaluation_results[:3])
        ]) if evaluation_results else "No evaluation results"
        
        prompt = f"""
# RECOMMENDATIONS TO REVIEW
{recs_text}

# EVALUATION RESULTS
{eval_text}

# TASK
Review each recommendation critically:

1. **Reasoning**: Is it clear, logical, and complete? Any gaps?
2. **Confidence**: Is the score appropriate? Too high/low?
3. **Priority**: Does it match urgency and importance?
4. **Evidence**: Is supporting evidence sufficient and relevant?
5. **Alternatives**: Are alternatives meaningful and well-justified?

For each recommendation:
- If significant improvements exist, set needs_improvement=true and provide specific suggestions
- If only minor issues or acceptable as-is, approve it

Only generate revised_recommendations if you made actual improvements.
"""
        return prompt
