"""
Human Review Agent - Prepares recommendations for human approval.
Tracks decisions and stores feedback in memory.
"""

from datetime import datetime
from typing import List, Dict, Any

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.nba import HumanReviewResponse
from app.memory import get_memory_manager
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class HumanReviewAgent(BaseAgent):
    """
    Human Review Agent prepares recommendations for approval.
    Never executes automatically - requires human decision.
    """

    def __init__(self):
        super().__init__(
            agent_id="human_review_agent",
            name="Human Review Agent",
            description="Prepares recommendations for human approval",
            version="1.0.0",
            supported_domains=["legal", "*"],
            priority=6,
        )
        self.memory_manager = get_memory_manager()

    @property
    def capabilities(self) -> List[str]:
        return ["human_in_the_loop", "approval_workflow", "feedback_tracking"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return ["feedback_memory"]

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Prepare recommendations for human review."""
        start_time = datetime.utcnow()
        
        try:
            case_id = context.input_data.get("case_id", "")
            recommendations = context.get_shared("nba_recommendations", [])
            explanations = context.get_shared("explanations", [])
            evaluation_results = context.get_shared("evaluation_results", [])
            
            if not recommendations:
                raise ValueError("No recommendations to review")
            
            # Prepare review context
            review_context = self._prepare_review_context(
                recommendations,
                explanations,
                evaluation_results
            )
            
            # Store in memory for tracking
            await self._store_review_metadata(case_id, review_context)
            
            # Mark as requiring approval
            context.set_shared("requires_human_approval", True)
            context.set_shared("review_context", review_context)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Human Review Agent prepared recommendations",
                case_id=case_id,
                recommendation_count=len(recommendations),
                duration_ms=duration
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={
                    "case_id": case_id,
                    "recommendations_count": len(recommendations),
                    "requires_approval": True,
                    "prepared_for_review": True,
                    "review_context": review_context
                },
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("Human Review Agent failed", error=str(e))
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
        return (
            context.get_shared("nba_recommendations") is not None and
            "case_id" in context.input_data
        )

    def _prepare_review_context(
        self,
        recommendations,
        explanations,
        evaluation_results
    ) -> Dict[str, Any]:
        """Prepare context for human review."""
        
        review_items = []
        for i, rec in enumerate(recommendations[:3]):
            item = {
                "rank": i + 1,
                "action": rec.action if hasattr(rec, 'action') else rec.get('action', 'N/A'),
                "reasoning": rec.reasoning if hasattr(rec, 'reasoning') else rec.get('reasoning', 'N/A'),
                "confidence_score": rec.confidence_score if hasattr(rec, 'confidence_score') else rec.get('confidence_score', 0),
                "priority": rec.priority if hasattr(rec, 'priority') else rec.get('priority', 'N/A'),
                "legal_basis": rec.legal_basis if hasattr(rec, 'legal_basis') else rec.get('legal_basis', 'N/A'),
                "expected_impact": rec.expected_impact if hasattr(rec, 'expected_impact') else rec.get('expected_impact', 'N/A'),
                "time_sensitivity": rec.time_sensitivity if hasattr(rec, 'time_sensitivity') else rec.get('time_sensitivity', 'N/A'),
            }
            
            # Add explanation if available
            if explanations and i < len(explanations):
                exp = explanations[i]
                item["explanation"] = {
                    "why_this_action": exp.why_this_action if hasattr(exp, 'why_this_action') else exp.get('why_this_action', ''),
                    "why_now": exp.why_now if hasattr(exp, 'why_now') else exp.get('why_now', ''),
                    "risk_if_ignored": exp.risk_if_ignored if hasattr(exp, 'risk_if_ignored') else exp.get('risk_if_ignored', '')
                }
            
            # Add evaluation if available
            if evaluation_results and i < len(evaluation_results):
                eval_result = evaluation_results[i]
                item["evaluation"] = {
                    "overall_score": eval_result.overall_score if hasattr(eval_result, 'overall_score') else eval_result.get('overall_score', 0),
                    "passed": eval_result.passed if hasattr(eval_result, 'passed') else eval_result.get('passed', False)
                }
            
            review_items.append(item)
        
        return {
            "review_items": review_items,
            "total_recommendations": len(recommendations),
            "prepared_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            "instructions": "Review each recommendation and decide: approve, reject, or modify"
        }

    async def _store_review_metadata(self, case_id: str, review_context: Dict[str, Any]) -> None:
        """Store review metadata in memory."""
        try:
            metadata = {
                "type": "human_review_prepared",
                "case_id": case_id,
                "prepared_at": datetime.utcnow().isoformat(),
                "recommendation_count": review_context.get("total_recommendations", 0),
                "status": "pending_review"
            }
            
            # Store in case memory
            await self.memory_manager.store_case_context(case_id, "review_metadata", metadata)
            
            logger.info("Review metadata stored", case_id=case_id)
            
        except Exception as e:
            logger.warning("Failed to store review metadata", error=str(e))

    async def process_feedback(
        self,
        case_id: str,
        recommendation_id: str,
        decision: str,
        rating: int,
        comments: str,
        modifications: Dict[str, Any]
    ) -> None:
        """Process human feedback and store in memory."""
        try:
            feedback = {
                "recommendation_id": recommendation_id,
                "decision": decision,
                "rating": rating,
                "comments": comments,
                "modifications": modifications,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Store feedback in memory for learning
            await self.memory_manager.store_feedback(case_id, feedback)
            
            logger.info(
                "Feedback processed and stored",
                case_id=case_id,
                recommendation_id=recommendation_id,
                decision=decision
            )
            
        except Exception as e:
            logger.error("Failed to process feedback", error=str(e))
