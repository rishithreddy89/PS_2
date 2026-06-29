"""
Tests for Phase 5 Decision Intelligence Layer.
"""

import pytest
from datetime import datetime

from app.agents.context import ExecutionContext
from app.agents.nba_agent import NBAAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.human_review_agent import HumanReviewAgent
from app.schemas.nba import NextBestAction, AlternativeAction


class TestNBAAgent:
    """Test NBA Agent."""
    
    @pytest.mark.asyncio
    async def test_nba_agent_execution(self):
        """Test NBA Agent generates recommendations."""
        agent = NBAAgent()
        
        context = ExecutionContext(
            case_id="test-case-123",
            domain="legal",
            workflow="nba_generation",
            input_data={
                "case_id": "test-case-123",
                "case_context": {
                    "case_type": "contract_dispute",
                    "description": "Commercial contract dispute"
                }
            }
        )
        
        # Add mock data to context
        context.set_shared("evidence_analysis", {
            "overall_strength": "moderate",
            "strong_evidence": [{"id": "1", "description": "Contract signed"}]
        })
        context.set_shared("timeline_summary", {"events": []})
        context.set_shared("risk_summary", {"overall_risk_level": "medium"})
        context.set_shared("retrieved_documents", [])
        
        result = await agent.execute(context)
        
        assert result.status == "completed"
        assert "recommendations" in result.output
        recommendations = result.output["recommendations"]
        assert len(recommendations) <= 3
        assert len(recommendations) > 0
    
    def test_nba_agent_capabilities(self):
        """Test NBA Agent capabilities."""
        agent = NBAAgent()
        
        assert "nba_generation" in agent.capabilities
        assert "action_ranking" in agent.capabilities
        assert "openai" in agent.required_tools
    
    @pytest.mark.asyncio
    async def test_nba_agent_validation(self):
        """Test NBA Agent validation."""
        agent = NBAAgent()
        
        context = ExecutionContext(
            case_id="test-case",
            input_data={"case_id": "test-case"}
        )
        
        is_valid = await agent.validate(context)
        assert is_valid is True
        
        # Test invalid context
        invalid_context = ExecutionContext(
            case_id="test-case",
            input_data={}
        )
        
        is_valid = await agent.validate(invalid_context)
        assert is_valid is False


class TestEvaluationAgent:
    """Test Evaluation Agent."""
    
    @pytest.mark.asyncio
    async def test_evaluation_agent_execution(self):
        """Test Evaluation Agent evaluates recommendations."""
        agent = EvaluationAgent()
        
        context = ExecutionContext(
            case_id="test-case-123",
            domain="legal",
            workflow="evaluation"
        )
        
        # Add mock recommendations
        mock_recommendations = [
            NextBestAction(
                action="File motion to dismiss",
                reasoning="Jurisdiction issue",
                confidence_score=0.85,
                priority="high",
                legal_basis="Rule 12(b)",
                supporting_evidence=["evidence1"],
                expected_impact="Case dismissed",
                time_sensitivity="immediate",
                dependencies=[],
                alternative_actions=[],
                rank=1
            )
        ]
        
        context.set_shared("nba_recommendations", mock_recommendations)
        context.set_shared("evidence_analysis", {})
        context.set_shared("retrieved_documents", [])
        
        result = await agent.execute(context)
        
        assert result.status == "completed"
        assert "evaluations" in result.output
        assert "overall_quality_score" in result.output
    
    def test_evaluation_agent_capabilities(self):
        """Test Evaluation Agent capabilities."""
        agent = EvaluationAgent()
        
        assert "quality_verification" in agent.capabilities
        assert "evidence_checking" in agent.capabilities


class TestReflectionAgent:
    """Test Reflection Agent."""
    
    @pytest.mark.asyncio
    async def test_reflection_agent_execution(self):
        """Test Reflection Agent reviews recommendations."""
        agent = ReflectionAgent()
        
        context = ExecutionContext(
            case_id="test-case-123",
            domain="legal",
            workflow="reflection"
        )
        
        mock_recommendations = [
            NextBestAction(
                action="Review contract terms",
                reasoning="Need clarity on clauses",
                confidence_score=0.75,
                priority="medium",
                legal_basis="Contract law",
                supporting_evidence=["contract"],
                expected_impact="Better understanding",
                time_sensitivity="1-week",
                dependencies=[],
                alternative_actions=[],
                rank=1
            )
        ]
        
        context.set_shared("nba_recommendations", mock_recommendations)
        context.set_shared("evaluation_results", [])
        
        result = await agent.execute(context)
        
        assert result.status == "completed"
        assert "reflections" in result.output
        assert "approved" in result.output
    
    def test_reflection_agent_capabilities(self):
        """Test Reflection Agent capabilities."""
        agent = ReflectionAgent()
        
        assert "self_reflection" in agent.capabilities
        assert "quality_improvement" in agent.capabilities


class TestExplainabilityAgent:
    """Test Explainability Agent."""
    
    @pytest.mark.asyncio
    async def test_explainability_agent_execution(self):
        """Test Explainability Agent generates explanations."""
        agent = ExplainabilityAgent()
        
        context = ExecutionContext(
            case_id="test-case-123",
            domain="legal",
            workflow="explainability"
        )
        
        mock_recommendations = [
            NextBestAction(
                action="File response",
                reasoning="Deadline approaching",
                confidence_score=0.90,
                priority="urgent",
                legal_basis="Civil procedure rules",
                supporting_evidence=["deadline"],
                expected_impact="Avoid default",
                time_sensitivity="immediate",
                dependencies=[],
                alternative_actions=[],
                rank=1
            )
        ]
        
        context.set_shared("nba_recommendations", mock_recommendations)
        context.set_shared("evidence_analysis", {})
        context.set_shared("risk_summary", {})
        context.set_shared("retrieved_documents", [])
        
        result = await agent.execute(context)
        
        assert result.status == "completed"
        assert "explanations" in result.output
    
    def test_explainability_agent_capabilities(self):
        """Test Explainability Agent capabilities."""
        agent = ExplainabilityAgent()
        
        assert "explainable_ai" in agent.capabilities
        assert "transparency" in agent.capabilities


class TestHumanReviewAgent:
    """Test Human Review Agent."""
    
    @pytest.mark.asyncio
    async def test_human_review_agent_execution(self):
        """Test Human Review Agent prepares for review."""
        agent = HumanReviewAgent()
        
        context = ExecutionContext(
            case_id="test-case-123",
            domain="legal",
            workflow="human_review",
            input_data={"case_id": "test-case-123"}
        )
        
        mock_recommendations = [
            NextBestAction(
                action="Schedule deposition",
                reasoning="Gather testimony",
                confidence_score=0.80,
                priority="high",
                legal_basis="Discovery rules",
                supporting_evidence=["witness list"],
                expected_impact="Key evidence",
                time_sensitivity="2-weeks",
                dependencies=[],
                alternative_actions=[],
                rank=1
            )
        ]
        
        context.set_shared("nba_recommendations", mock_recommendations)
        context.set_shared("explanations", [])
        context.set_shared("evaluation_results", [])
        
        result = await agent.execute(context)
        
        assert result.status == "completed"
        assert result.output["requires_approval"] is True
        assert result.output["prepared_for_review"] is True
        assert "review_context" in result.output
    
    def test_human_review_agent_capabilities(self):
        """Test Human Review Agent capabilities."""
        agent = HumanReviewAgent()
        
        assert "human_in_the_loop" in agent.capabilities
        assert "approval_workflow" in agent.capabilities
        assert "feedback_tracking" in agent.capabilities


class TestNBASchemas:
    """Test NBA Pydantic schemas."""
    
    def test_next_best_action_schema(self):
        """Test NextBestAction schema validation."""
        action = NextBestAction(
            action="Test action",
            reasoning="Test reasoning",
            confidence_score=0.85,
            priority="high",
            legal_basis="Test law",
            supporting_evidence=["evidence1"],
            expected_impact="Test impact",
            time_sensitivity="immediate",
            dependencies=[],
            alternative_actions=[],
            rank=1
        )
        
        assert action.action == "Test action"
        assert action.confidence_score == 0.85
        assert action.rank == 1
    
    def test_alternative_action_schema(self):
        """Test AlternativeAction schema."""
        alt = AlternativeAction(
            action="Alternative approach",
            reasoning="Different strategy",
            confidence_score=0.70
        )
        
        assert alt.action == "Alternative approach"
        assert alt.confidence_score == 0.70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
