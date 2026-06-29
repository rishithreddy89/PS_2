"""Normalization functions for LLM responses."""

from typing import Dict, Any

def normalize_nba_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the raw JSON response for NBAResponse to prevent minor
    schema issues from crashing the workflow.
    """
    if not isinstance(data, dict):
        return data

    # 1. Handle missing or malformed recommendations
    recs = data.get("recommendations")
    if not isinstance(recs, list):
        pass # Let Pydantic validation handle missing or malformed recommendations
    else:
        # Force max 3 recommendations
        recs = recs[:3]
        data["recommendations"] = recs
    
    # 2. Normalize individual recommendations
    normalized_recs = []
    for idx, rec in enumerate(recs):
        if not isinstance(rec, dict):
            continue
            
        # Map fields from various prompt formats to NextBestAction schema
        if "confidence" in rec and "confidence_score" not in rec:
            rec["confidence_score"] = rec.pop("confidence")
            
        if "description" in rec and "executive_summary" not in rec:
            rec["executive_summary"] = rec.pop("description")
            
        if "expected_impact" in rec and "expected_outcome" not in rec:
            rec["expected_outcome"] = rec.pop("expected_impact")
            
        if "legal_basis" in rec and "applicable_laws" not in rec:
            val = rec.pop("legal_basis")
            rec["applicable_laws"] = [val] if isinstance(val, str) else val
            
        if "alternative_actions" in rec and "alternative_strategies" not in rec:
            alts = rec.pop("alternative_actions")
            if isinstance(alts, list):
                mapped_alts = []
                for alt in alts:
                    if isinstance(alt, dict):
                        mapped_alts.append({
                            "action": alt.get("action", "Alternative action"),
                            "reasoning": alt.get("reasoning", "Alternative reasoning"),
                            "confidence_score": alt.get("confidence_score", 0.5)
                        })
                    elif isinstance(alt, str):
                        mapped_alts.append({
                            "action": alt,
                            "reasoning": "Alternative reasoning",
                            "confidence_score": 0.5
                        })
                rec["alternative_strategies"] = mapped_alts
                
        # Ensure float parsing doesn't crash here but let Pydantic handle invalid values
        if "confidence_score" in rec and rec["confidence_score"] is not None:
            try:
                rec["confidence_score"] = float(rec["confidence_score"])
            except (ValueError, TypeError):
                pass
                
        # Ensure lists are lists
        list_fields = [
            "supporting_evidence", "missing_evidence", "applicable_laws",
            "relevant_precedents", "legal_risks", "next_best_actions",
            "alternative_strategies", "source_citations", "detailed_applicable_laws",
            "detailed_precedents", "counterarguments"
        ]
        for field in list_fields:
            if field in rec and not isinstance(rec[field], list):
                rec[field] = [rec[field]] if rec[field] else []
            elif field not in rec:
                rec[field] = []
                
        if "rank" not in rec:
            rec["rank"] = idx + 1
            
        normalized_recs.append(rec)
        
    if "recommendations" in data and isinstance(data["recommendations"], list):
        data["recommendations"] = normalized_recs

    # Remove unknown top-level fields just to be safe
    known_fields = {
        "recommendations", "overall_strategy", "generated_at",
        "executive_opinion", "litigation_risk", "action_plan", "contradiction_analysis"
    }
    keys_to_remove = [k for k in data.keys() if k not in known_fields]
    for k in keys_to_remove:
        del data[k]

    return data
