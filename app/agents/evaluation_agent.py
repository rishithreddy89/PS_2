"""
Evaluation Agent - Verifies recommendation quality.
"""

from datetime import datetime
from typing import List

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.nba import EvaluationResponse, EvaluationResult, EvidenceCheck
from app.llm import get_openrouter_service
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class EvaluationAgent(BaseAgent):
    """
    Evaluation Agent verifies recommendation quality.
    """

    def __init__(self):
        super().__init__(
            agent_id="evaluation_agent",
            name="Evaluation Agent",
            description="Verifies recommendation quality and evidence support",
            version="1.0.0",
            supported_domains=["legal", "*"],
            priority=9,
        )
        self.openrouter_service = get_openrouter_service()

    @property
    def capabilities(self) -> List[str]:
        return ["quality_verification", "evidence_checking", "confidence_calibration"]

    @property
    def required_tools(self) -> List[str]:
        return ["openai"]

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Evaluate recommendations."""
        start_time = datetime.utcnow()
        
        try:
            recommendations = context.get_shared("nba_recommendations", [])
            evidence_analysis = context.get_shared("evidence_analysis", {})
            retrieved_docs = context.get_shared("retrieved_documents", [])
            
            if not recommendations:
                raise ValueError("No recommendations to evaluate")
            
            prompt = self._build_evaluation_prompt(
                recommendations,
                evidence_analysis,
                retrieved_docs
            )
            
            system_prompt = """You are a legal quality assurance specialist. Evaluate each recommendation for:
1. Evidence support (does evidence back the claim?)
2. Citation quality (are sources credible and relevant?)
3. Consistency (no contradictions?)
4. Confidence calibration (is confidence score appropriate?)
5. Potential issues (hallucinations, gaps, errors)

Respond ONLY with valid JSON:
{
    "evaluations": [
        {
            "recommendation_rank": 1,
            "evidence_support_score": 0.85,
            "citation_quality_score": 0.90,
            "consistency_score": 0.88,
            "confidence_calibration": "well_calibrated",
            "evidence_check": {
                "has_support": true,
                "evidence_quality": "strong",
                "missing_evidence": []
            },
            "potential_issues": [],
            "overall_score": 0.87,
            "passed": true
        }
    ],
    "all_passed": true,
    "overall_quality_score": 0.87,
    "recommendations_text": "All recommendations are well-supported"
}"""
            
            result = await self.openrouter_service.complete_structured(
                prompt=prompt,
                response_model=EvaluationResponse,
                system_prompt=system_prompt,
                temperature=0.2
            )
            
            context.set_shared("evaluation_results", result.evaluations)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Evaluation Agent completed",
                all_passed=result.all_passed,
                quality_score=result.overall_quality_score,
                duration_ms=duration
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={
                    "evaluations": [e.dict() for e in result.evaluations],
                    "all_passed": result.all_passed,
                    "overall_quality_score": result.overall_quality_score
                },
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Evaluation Agent failed", error=str(e))
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

    def _build_evaluation_prompt(self, recommendations, evidence_analysis, retrieved_docs) -> str:
        """Build evaluation prompt."""
        
        recs_text = "\n\n".join([
            f"Rank {i+1}: {rec.action if hasattr(rec, 'action') else rec.get('action', 'N/A')}\n"
            f"Reasoning: {rec.reasoning if hasattr(rec, 'reasoning') else rec.get('reasoning', 'N/A')}\n"
            f"Confidence: {rec.confidence_score if hasattr(rec, 'confidence_score') else rec.get('confidence_score', 0)}\n"
            f"Evidence: {', '.join(rec.supporting_evidence if hasattr(rec, 'supporting_evidence') else rec.get('supporting_evidence', []))}"
            for i, rec in enumerate(recommendations[:3])
        ])
        
        prompt = f"""
# RECOMMENDATIONS TO EVALUATE
{recs_text}

# AVAILABLE EVIDENCE
{str(evidence_analysis)}

# RETRIEVED DOCUMENTS
{len(retrieved_docs)} documents retrieved

# TASK
Evaluate each recommendation:
1. Check if evidence supports claims
2. Verify citation quality
3. Check for consistency
4. Assess confidence calibration
5. Identify potential issues (missing evidence, hallucinations, gaps)

Provide scores (0.0-1.0) for each aspect and overall score.
Mark as "passed" only if overall_score >= 0.70
"""
        return prompt
