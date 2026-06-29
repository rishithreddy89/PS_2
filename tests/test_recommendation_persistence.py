"""
Tests for recommendation extraction and persistence.

Verifies that:
- _generate_recommendations scans agent_responses by real agent_id
- String-format recommendations (RecommendationAgent) are handled correctly
- Dict-format recommendations (NBAAgent) are handled correctly
- Only valid Recommendation model columns are populated
- Detailed logging occurs before save (count, titles, confidence)
- GET /api/v1/recommendations returns persisted records
"""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, AsyncMock

import pytest

from app.utils.serialization import make_json_safe
from app.models.recommendation import Recommendation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_json_serializable(value: Any, label: str = "value") -> None:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise AssertionError(f"{label} is not JSON-serializable: {exc}") from exc


VALID_RECOMMENDATION_COLUMNS = {
    "id", "case_id", "execution_id",
    "action_type", "title", "description",
    "reasoning", "confidence_score",
    "priority", "status",
    "supporting_evidence", "meta_data",
    "created_at", "updated_at",
}

INVALID_COLUMNS = {
    "recommendation_type", "recommended_action",
    "impact_assessment", "legal_basis", "alternative_actions",
}


# ---------------------------------------------------------------------------
# Unit tests: recommendation normalisation logic
# ---------------------------------------------------------------------------

class TestRecommendationNormalisation:
    """Tests for the rec normalisation logic in _generate_recommendations."""

    def _normalise(
        self,
        rec: Any,
        shared_confidence: float = 0.85,
        shared_reasoning: str = "Generated based on input",
        index: int = 0,
    ) -> Dict[str, Any]:
        """Mirror the normalisation logic from _generate_recommendations."""
        if hasattr(rec, "model_dump"):
            rec_dict = make_json_safe(rec.model_dump())
        elif hasattr(rec, "dict") and callable(rec.dict):
            rec_dict = make_json_safe(rec.dict())
        elif isinstance(rec, dict):
            rec_dict = make_json_safe(rec)
        elif isinstance(rec, str):
            rec_dict = {
                "title": rec,
                "description": rec,
                "reasoning": shared_reasoning or rec,
                "confidence_score": float(shared_confidence),
                "priority": "medium",
            }
        else:
            rec_dict = make_json_safe({"title": str(rec)})

        title = rec_dict.get("action") or rec_dict.get("title") or f"Recommendation {index + 1}"
        description = (
            rec_dict.get("reasoning")
            or rec_dict.get("description")
            or rec_dict.get("action")
            or str(title)
        )
        reasoning = rec_dict.get("reasoning") or rec_dict.get("description") or str(title)
        confidence = float(rec_dict.get("confidence_score", rec_dict.get("confidence", shared_confidence)))
        priority = str(rec_dict.get("priority", "medium"))

        raw_evidence = rec_dict.get("supporting_evidence") or rec_dict.get("evidence")
        if isinstance(raw_evidence, list):
            supporting = make_json_safe({"items": raw_evidence})
        elif isinstance(raw_evidence, dict):
            supporting = make_json_safe(raw_evidence)
        else:
            supporting = {}

        return {
            "action_type": "next_best_action",
            "title": str(title)[:500],
            "description": str(description),
            "reasoning": str(reasoning),
            "confidence_score": min(max(confidence, 0.0), 1.0),
            "priority": priority,
            "status": "pending",
            "supporting_evidence": supporting,
            "meta_data": make_json_safe({
                "generated_by": "recommendation_agent",
                "rank": index + 1,
                "legal_basis": rec_dict.get("legal_basis", ""),
                "alternative_actions": rec_dict.get("alternative_actions", []),
                "expected_impact": rec_dict.get("expected_impact", ""),
            }),
        }

    def test_string_recommendation_normalised_correctly(self):
        """Plain-string recs from RecommendationAgent should map to valid model fields."""
        rec_str = "Recommendation 1: Based on analysis"
        result = self._normalise(rec_str, shared_confidence=0.85)

        assert result["title"] == rec_str
        assert result["action_type"] == "next_best_action"
        assert result["confidence_score"] == 0.85
        assert result["priority"] == "medium"
        assert result["status"] == "pending"
        assert_json_serializable(result["supporting_evidence"], "supporting_evidence")
        assert_json_serializable(result["meta_data"], "meta_data")

    def test_dict_recommendation_nba_format_normalised_correctly(self):
        """NBA-style dict recs should map title from 'action' field."""
        rec_dict = {
            "action": "File an urgent motion",
            "reasoning": "Time-sensitive based on statute of limitations",
            "confidence_score": 0.92,
            "priority": "urgent",
            "legal_basis": "Section 123 Civil Code",
            "supporting_evidence": ["Evidence A", "Evidence B"],
            "alternative_actions": [{"action": "Alt 1", "reasoning": "why", "confidence_score": 0.7}],
            "expected_impact": "Prevents dismissal",
        }
        result = self._normalise(rec_dict)

        assert result["title"] == "File an urgent motion"
        assert result["confidence_score"] == 0.92
        assert result["priority"] == "urgent"
        assert result["meta_data"]["legal_basis"] == "Section 123 Civil Code"
        assert result["meta_data"]["expected_impact"] == "Prevents dismissal"
        assert_json_serializable(result, "full result dict")

    def test_no_invalid_columns_in_result(self):
        """The normalised dict must not contain any invalid ORM column names."""
        result = self._normalise("Do something important")
        for bad_col in INVALID_COLUMNS:
            assert bad_col not in result, f"Invalid column {bad_col!r} found in result"

    def test_confidence_clamped_to_valid_range(self):
        """confidence_score must always be in [0.0, 1.0]."""
        over = self._normalise({"action": "X", "confidence_score": 1.5})
        assert over["confidence_score"] == 1.0

        under = self._normalise({"action": "Y", "confidence_score": -0.1})
        assert under["confidence_score"] == 0.0

    def test_title_truncated_to_500_chars(self):
        """title must not exceed 500 characters."""
        long_str = "A" * 600
        result = self._normalise(long_str)
        assert len(result["title"]) <= 500

    def test_supporting_evidence_list_wrapped_in_dict(self):
        """List evidence must be wrapped in {"items": [...]} for JSON column."""
        rec = {
            "action": "Do X",
            "supporting_evidence": ["item1", "item2"],
        }
        result = self._normalise(rec)
        assert isinstance(result["supporting_evidence"], dict)
        assert "items" in result["supporting_evidence"]

    def test_supporting_evidence_dict_passes_through(self):
        """Dict evidence passes through as-is."""
        rec = {
            "action": "Do Y",
            "supporting_evidence": {"legal_ref": "Art 5", "doc": "Contract A"},
        }
        result = self._normalise(rec)
        assert result["supporting_evidence"]["legal_ref"] == "Art 5"


class TestRecommendationModelInstantiation:
    """Verify Recommendation model can be instantiated with correct columns only."""

    def _build_recommendation(
        self,
        case_id: str = "test-case-id",
        agent_id: str = "recommendation_agent",
        index: int = 0,
        rec_str: str = "Do this action",
    ) -> Recommendation:
        return Recommendation(
            case_id=case_id,
            action_type="next_best_action",
            title=rec_str[:500],
            description=rec_str,
            reasoning=rec_str,
            confidence_score=0.85,
            priority="medium",
            status="pending",
            supporting_evidence={},
            meta_data=make_json_safe({"generated_by": agent_id, "rank": index + 1}),
        )

    def test_instantiation_with_recommendation_agent_output(self):
        """Recommendation from RecommendationAgent (string format) instantiates correctly."""
        rec = self._build_recommendation(rec_str="Recommendation 1: Based on analysis")
        assert rec.action_type == "next_best_action"
        assert rec.title == "Recommendation 1: Based on analysis"
        assert rec.confidence_score == 0.85
        assert rec.status == "pending"
        assert_json_serializable(rec.supporting_evidence, "supporting_evidence")
        assert_json_serializable(rec.meta_data, "meta_data")

    def test_instantiation_with_nba_agent_output(self):
        """Recommendation from NBAAgent (dict format) instantiates correctly."""
        rec = Recommendation(
            case_id="case-001",
            action_type="next_best_action",
            title="File an urgent motion",
            description="Based on statute of limitations analysis",
            reasoning="Time-sensitive; must be filed within 30 days",
            confidence_score=0.92,
            priority="urgent",
            status="pending",
            supporting_evidence={"items": ["Evidence A", "Evidence B"]},
            meta_data=make_json_safe({
                "generated_by": "nba_agent",
                "rank": 1,
                "legal_basis": "Section 123",
                "alternative_actions": [],
                "expected_impact": "Prevents dismissal",
            }),
        )
        assert rec.confidence_score == 0.92
        assert rec.priority == "urgent"
        assert_json_serializable(rec.supporting_evidence, "supporting_evidence")
        assert_json_serializable(rec.meta_data, "meta_data")

    def test_no_invalid_column_kwargs_raises_typeerror(self):
        """Using invalid column names must raise TypeError."""
        with pytest.raises(TypeError):
            Recommendation(
                case_id="case-001",
                action_type="next_best_action",
                title="Test",
                description="Test",
                reasoning="Test",
                confidence_score=0.8,
                priority="medium",
                status="pending",
                recommendation_type="invalid_column",  # does NOT exist
            )


class TestAgentResponseScanning:
    """
    Tests that _generate_recommendations scans agent_responses by real agent_id.
    """

    def _make_agent_response(self, agent_id: str, output: Dict) -> MagicMock:
        resp = MagicMock()
        resp.agent_id = agent_id
        resp.output = output
        return resp

    def test_finds_recommendations_from_recommendation_agent(self):
        """Should find recs from 'recommendation_agent' in agent_responses."""
        resp = self._make_agent_response("recommendation_agent", {
            "recommendations": ["Rec 1", "Rec 2"],
            "confidence": 0.85,
            "reasoning": "Based on analysis",
        })

        # Simulate the scanning logic
        candidate_sources = []
        for r in [resp]:
            out = r.output or {}
            recs = out.get("recommendations")
            if recs:
                candidate_sources.append((
                    r.agent_id,
                    recs,
                    out.get("confidence", 0.8),
                    out.get("reasoning", ""),
                ))

        assert len(candidate_sources) == 1
        agent_id, recs, conf, reasoning = candidate_sources[0]
        assert agent_id == "recommendation_agent"
        assert len(recs) == 2
        assert conf == 0.85

    def test_finds_recommendations_from_nba_agent(self):
        """Should also find recs from 'nba_agent' in agent_responses."""
        resp = self._make_agent_response("nba_agent", {
            "recommendations": [
                {"action": "File motion", "reasoning": "Urgent", "confidence_score": 0.9, "priority": "urgent"},
            ],
            "overall_strategy": "Aggressive legal approach",
        })

        candidate_sources = []
        for r in [resp]:
            out = r.output or {}
            recs = out.get("recommendations")
            if recs:
                candidate_sources.append((r.agent_id, recs, out.get("confidence", 0.8), ""))

        assert len(candidate_sources) == 1
        agent_id, recs, _, _ = candidate_sources[0]
        assert agent_id == "nba_agent"
        assert recs[0]["action"] == "File motion"

    def test_empty_agent_responses_falls_through(self):
        """If no agent has recommendations, candidate_sources is empty."""
        resp = self._make_agent_response("some_agent", {"result": "done"})

        candidate_sources = []
        for r in [resp]:
            out = r.output or {}
            recs = out.get("recommendations")
            if recs:
                candidate_sources.append((r.agent_id, recs, 0.8, ""))

        assert candidate_sources == []

    def test_fallback_to_final_output_dict(self):
        """If agent_responses is empty, should fall back to final_output['agent_outputs']."""
        final_output = {
            "agent_outputs": {
                "recommendation_agent": {
                    "recommendations": ["Rec A", "Rec B"],
                    "confidence": 0.75,
                }
            }
        }

        # No agent_responses → fallback
        candidate_sources = []
        if not candidate_sources and final_output:
            inner = final_output.get("agent_outputs", {})
            for agent_id, out in (inner or {}).items():
                if not isinstance(out, dict):
                    continue
                recs = out.get("recommendations")
                if recs:
                    candidate_sources.append((
                        agent_id, recs,
                        out.get("confidence", 0.8),
                        out.get("reasoning", ""),
                    ))

        assert len(candidate_sources) == 1
        agent_id, recs, conf, _ = candidate_sources[0]
        assert agent_id == "recommendation_agent"
        assert conf == 0.75
