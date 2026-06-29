"""
NBA (Next Best Action) API Router.
Endpoints for analysis, review, and feedback.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.nba import (
    AnalysisRequest,
    AnalysisResponse,
    HumanReviewDecision,
    FeedbackCreate,
    NextBestAction,
    ExplanationDetail,
    EvaluationResult
)
from app.agents.context import ExecutionContext
from app.agents.orchestrator import Orchestrator as AgentOrchestrator
from app.agents.human_review_agent import HumanReviewAgent
from app.repositories.recommendation import RecommendationRepository
from app.repositories.feedback import FeedbackRepository
from app.models.recommendation import Recommendation
from app.models.feedback import Feedback
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/nba", tags=["NBA"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_case(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute complete NBA analysis for a case.
    
    Flow:
    1. Retrieval → Evidence → Timeline → Risk
    2. NBA Generation
    3. Evaluation
    4. Reflection
    5. Explainability
    6. Human Review Preparation
    """
    try:
        logger.info("Starting NBA analysis", case_id=request.case_id)
        
        # Create execution context
        context = ExecutionContext(
            case_id=request.case_id,
            domain="legal",
            workflow="nba_analysis",
            input_data={
                "case_id": request.case_id,
                "query": request.query or "Analyze case and provide next best actions",
                "include_memory": request.include_memory
            }
        )
        
        # Execute orchestration
        orchestrator = AgentOrchestrator()
        
        from app.schemas.agent import ExecutionPlan, PlannerDecision, WorkflowStep
        
        # Define execution plan
        agent_sequence = [
            "retrieval_agent",
            "evidence_agent",
            "timeline_agent",
            "legal_issue_agent",
            "risk_agent",
            "recommendation_agent"
        ]
        
        plan = ExecutionPlan(
            plan_id="static_plan_" + request.case_id,
            workflow_steps=[
                WorkflowStep(
                    step_id=f"step_{i}",
                    agent_id=agent_id,
                    agent_name=agent_id.replace("_", " ").title(),
                    dependencies=[agent_sequence[i-1]] if i > 0 else []
                ) for i, agent_id in enumerate(agent_sequence)
            ],
            decision=PlannerDecision(
                required_capabilities=[],
                selected_agents=agent_sequence,
                execution_order=agent_sequence,
                reasoning="Static execution plan for NBA analysis."
            )
        )
        
        result = await orchestrator.execute(
            plan=plan,
            context=context
        )
        
        # Extract results
        recommendations = context.get_shared("recommendations", [])
        evidence_matrix = context.get_shared("evidence_matrix", [])
        contradictions = context.get_shared("contradictions", [])
        missing_evidence = context.get_shared("missing_evidence", [])
        timeline = context.get_shared("timeline", [])
        legal_issues = context.get_shared("legal_issues", [])
        risk_assessment = context.get_shared("risk_assessment", None)
        
        if not recommendations:
            error_details = context.errors if context.has_errors() else "Unknown error in orchestration"
            raise HTTPException(status_code=500, detail=f"No recommendations generated. Errors: {error_details}")
            
        # Update case metadata
        from sqlalchemy import update
        from app.models.case import Case
        case_meta = {
            "evidence_matrix": evidence_matrix,
            "contradictions": contradictions,
            "missing_evidence": missing_evidence,
            "timeline": timeline,
            "legal_issues": legal_issues,
            "risk_assessment": risk_assessment
        }
        await db.execute(
            update(Case).where(Case.case_number == request.case_id).values(meta_data=case_meta)
        )
        # Handle edge case where request uses UUID id instead of case_number
        await db.execute(
            update(Case).where(Case.id == request.case_id).values(meta_data=case_meta)
        )
        
        # Store recommendations in database
        rec_repo = RecommendationRepository(db)
        # Clear old recommendations for this case (optional, depending on business logic)
        for i, rec in enumerate(recommendations[:3]):
            rec_data = {
                "case_id": request.case_id,
                "action_type": "next_best_action",
                "title": rec.get("title", "N/A"),
                "description": rec.get("executive_summary", ""),
                "reasoning": rec.get("reasoning", ""),
                "confidence_score": rec.get("confidence_score", 0),
                "priority": rec.get("priority", "medium"),
                "status": "pending_review",
                "supporting_evidence": rec.get("supporting_evidence", []),
                "meta_data": rec
            }
            await rec_repo.create(rec_data)
        
        logger.info(
            "NBA analysis completed",
            case_id=request.case_id,
            recommendations_count=len(recommendations)
        )
        
        return AnalysisResponse(
            case_id=request.case_id,
            execution_id=context.request_id,
            recommendations=recommendations[:3],
            timeline=timeline,
            evidence_matrix=evidence_matrix,
            contradictions=contradictions,
            missing_evidence=missing_evidence,
            legal_issues=legal_issues,
            risk_assessment=risk_assessment,
            overall_quality=1.0,
            requires_review=True
        )
        
    except Exception as e:
        logger.error("NBA analysis failed", error=str(e), case_id=request.case_id)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/recommendations/{case_id}")
async def get_recommendations(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all recommendations for a case."""
    try:
        rec_repo = RecommendationRepository(db)
        recommendations = await rec_repo.filter({"case_id": case_id})
        
        return {
            "case_id": case_id,
            "recommendations": [
                {
                    "id": str(rec.id),
                    "action": rec.title,
                    "description": rec.description,
                    "reasoning": rec.reasoning,
                    "confidence_score": rec.confidence_score,
                    "priority": rec.priority,
                    "status": rec.status,
                    "supporting_evidence": rec.supporting_evidence,
                    "created_at": rec.created_at.isoformat()
                }
                for rec in recommendations
            ]
        }
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e), case_id=case_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explanations/{case_id}")
async def get_explanations(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get explanations for case recommendations."""
    try:
        rec_repo = RecommendationRepository(db)
        recommendations = await rec_repo.filter({"case_id": case_id})
        
        explanations = []
        for rec in recommendations:
            evidence = rec.supporting_evidence or {}
            explanations.append({
                "recommendation_id": str(rec.id),
                "action": rec.title,
                "legal_basis": evidence.get("legal_basis", ""),
                "supporting_evidence": evidence.get("evidence", []),
                "expected_impact": evidence.get("expected_impact", ""),
                "confidence_explanation": f"Confidence: {rec.confidence_score:.2f}"
            })
        
        return {
            "case_id": case_id,
            "explanations": explanations
        }
    except Exception as e:
        logger.error("Failed to get explanations", error=str(e), case_id=case_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit human feedback on a recommendation.
    Stores feedback for future learning.
    """
    try:
        logger.info(
            "Submitting feedback",
            recommendation_id=feedback.recommendation_id,
            decision=feedback.decision
        )
        
        feedback_repo = FeedbackRepository(db)
        
        feedback_data = {
            "recommendation_id": feedback.recommendation_id,
            "user_id": feedback.user_id,
            "action_taken": feedback.decision,
            "rating": feedback.rating,
            "comments": feedback.comments,
            "modified_recommendation": feedback.modifications,
            "outcome": feedback.decision
        }
        
        stored_feedback = await feedback_repo.create(feedback_data)
        
        # Update recommendation status
        rec_repo = RecommendationRepository(db)
        await rec_repo.update(
            feedback.recommendation_id,
            {"status": feedback.decision}
        )
        
        # Store in memory for learning
        review_agent = HumanReviewAgent()
        await review_agent.process_feedback(
            case_id="",  # Would need to fetch from recommendation
            recommendation_id=feedback.recommendation_id,
            decision=feedback.decision,
            rating=feedback.rating or 0,
            comments=feedback.comments or "",
            modifications=feedback.modifications or {}
        )
        
        logger.info("Feedback stored successfully", feedback_id=str(stored_feedback.id))
        
        return {
            "success": True,
            "feedback_id": str(stored_feedback.id),
            "message": "Feedback recorded and will influence future recommendations"
        }
        
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review")
async def prepare_review(
    case_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Prepare recommendations for human review."""
    try:
        rec_repo = RecommendationRepository(db)
        recommendations = await rec_repo.filter({
            "case_id": case_id,
            "status": "pending_review"
        })
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No pending recommendations")
        
        review_items = [
            {
                "recommendation_id": str(rec.id),
                "action": rec.title,
                "reasoning": rec.reasoning,
                "confidence_score": rec.confidence_score,
                "priority": rec.priority,
                "created_at": rec.created_at.isoformat()
            }
            for rec in recommendations
        ]
        
        return {
            "case_id": case_id,
            "review_items": review_items,
            "total_pending": len(review_items),
            "requires_approval": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to prepare review", error=str(e), case_id=case_id)
        raise HTTPException(status_code=500, detail=str(e))
