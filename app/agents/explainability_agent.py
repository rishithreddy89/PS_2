"""
Explainability Agent - Generates complete explanations for recommendations.
"""

from datetime import datetime
from typing import List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.nba import ExplainabilityResponse, ExplanationDetail
from app.llm import get_openrouter_service
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class ExplainabilityAgent(BaseAgent):
    """
    Explainability Agent creates detailed explanations.
    """

    def __init__(self):
        super().__init__(
            agent_id="explainability_agent",
            name="Explainability Agent",
            description="Generates explainable AI explanations",
            version="1.0.0",
            supported_domains=["legal", "*"],
            priority=7,
        )
        self.openrouter_service = get_openrouter_service()

    @property
    def capabilities(self) -> List[str]:
        return ["explainable_ai", "transparency", "reasoning_explanation"]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Generate explanations for recommendations."""
        start_time = datetime.utcnow()
        
        try:
            recommendations = context.get_shared("nba_recommendations", [])
            evidence_analysis = context.get_shared("evidence_analysis", {})
            risk_summary = context.get_shared("risk_summary", {})
            retrieved_docs = context.get_shared("retrieved_documents", [])
            
            if not recommendations:
                raise ValueError("No recommendations to explain")
            
            prompt = self._build_explainability_prompt(
                recommendations,
                evidence_analysis,
                risk_summary,
                retrieved_docs
            )
            
            system_prompt = """You are a legal explainability specialist. Create transparent, human-understandable explanations.

For each recommendation, explain:
1. **Why this action?** - Core reasoning
2. **Why now?** - Timing rationale
3. **Supporting laws** - Relevant statutes, regulations
4. **Supporting precedents** - Case law
5. **Supporting evidence** - Facts from the case
6. **Confidence explanation** - Why this confidence level
7. **Alternatives considered** - What else was considered
8. **Risk if ignored** - Consequences of inaction

Respond ONLY with valid JSON:
{
    "explanations": [
        {
            "why_this_action": "detailed explanation",
            "why_now": "timing explanation",
            "supporting_laws": ["law1", "law2"],
            "supporting_precedents": ["precedent1"],
            "supporting_evidence": ["evidence1", "evidence2"],
            "confidence_explanation": "why this confidence score",
            "alternatives_considered": ["alt1", "alt2"],
            "risk_if_ignored": "consequences"
        }
    ]
}"""
            
            result = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=ExplainabilityResponse,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            context.set_shared("explanations", result.explanations)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Explainability Agent completed",
                explanation_count=len(result.explanations),
                duration_ms=duration
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={"explanations": [e.dict() for e in result.explanations]},
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Explainability Agent failed", error=str(e))
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

    def _build_explainability_prompt(
        self,
        recommendations,
        evidence_analysis,
        risk_summary,
        retrieved_docs
    ) -> str:
        """Build explainability prompt."""
        
        recs_text = "\n\n".join([
            f"Recommendation {i+1}:\n"
            f"Action: {rec.action if hasattr(rec, 'action') else rec.get('action', 'N/A')}\n"
            f"Reasoning: {rec.reasoning if hasattr(rec, 'reasoning') else rec.get('reasoning', 'N/A')}\n"
            f"Legal Basis: {rec.legal_basis if hasattr(rec, 'legal_basis') else rec.get('legal_basis', 'N/A')}\n"
            f"Confidence: {rec.confidence_score if hasattr(rec, 'confidence_score') else rec.get('confidence_score', 0)}\n"
            f"Priority: {rec.priority if hasattr(rec, 'priority') else rec.get('priority', 'N/A')}\n"
            f"Time Sensitivity: {rec.time_sensitivity if hasattr(rec, 'time_sensitivity') else rec.get('time_sensitivity', 'N/A')}\n"
            f"Alternatives: {', '.join([a.action if hasattr(a, 'action') else a.get('action', '') for a in (rec.alternative_actions if hasattr(rec, 'alternative_actions') else rec.get('alternative_actions', []))])}"
            for i, rec in enumerate(recommendations[:3])
        ])
        
        prompt = f"""
# RECOMMENDATIONS TO EXPLAIN
{recs_text}

# EVIDENCE CONTEXT
{str(evidence_analysis)}

# RISK CONTEXT
{str(risk_summary)}

# RETRIEVED DOCUMENTS COUNT
{len(retrieved_docs)} documents

# TASK
Create transparent, detailed explanations for each recommendation.

For each one, explain:
1. **Why this action?** - Why is this the recommended course of action?
2. **Why now?** - Why is the timing important?
3. **Supporting laws** - Which statutes, regulations apply?
4. **Supporting precedents** - Relevant case law
5. **Supporting evidence** - What evidence backs this up?
6. **Confidence explanation** - Why this confidence score (explain factors)
7. **Alternatives considered** - What other options were evaluated?
8. **Risk if ignored** - What happens if this action is not taken?

Make explanations clear, factual, and actionable for legal professionals.
"""
        return prompt
