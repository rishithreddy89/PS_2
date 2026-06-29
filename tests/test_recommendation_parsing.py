import pytest
from app.agents.recommendation_agent import (
    ExecutivePhase,
    ContradictionPhase,
    RecommendationPhase,
    RiskPhase,
    ActionPlanPhase
)
from app.schemas.nba import (
    ExecutiveLegalOpinion,
    ContradictionAnalysis,
    NextBestAction,
    DetailedLitigationRisk,
    ActionPlanStep
)

def test_executive_phase_parsing():
    json_data = '''
    {
      "executive_opinion": {
        "overall_assessment": "Strong case",
        "case_strength": "High",
        "primary_claim": "Breach",
        "strongest_evidence": "Contract",
        "weakest_evidence": "None",
        "primary_recommendation": "Sue",
        "biggest_litigation_risk": "Cost",
        "overall_confidence": "High"
      },
      "overall_strategy": "Aggressive litigation"
    }
    '''
    model = ExecutivePhase.model_validate_json(json_data)
    assert model.overall_strategy == "Aggressive litigation"
    assert model.executive_opinion is not None
    assert model.executive_opinion.case_strength == "High"

def test_recommendation_phase_parsing():
    json_data = '''
    {
      "recommendations": [
        {
          "title": "File lawsuit",
          "priority": "High",
          "confidence_score": 0.9,
          "executive_summary": "Sue them now",
          "reasoning": "They breached the contract.",
          "expected_outcome": "Win",
          "urgency": "Immediate"
        }
      ]
    }
    '''
    model = RecommendationPhase.model_validate_json(json_data)
    assert len(model.recommendations) == 1
    assert model.recommendations[0].title == "File lawsuit"
    assert model.recommendations[0].priority == "High"
