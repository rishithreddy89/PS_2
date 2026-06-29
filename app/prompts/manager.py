"""Centralized prompt management."""

from typing import Dict, Any, Optional
from enum import Enum


class PromptTemplate(str, Enum):
    """Available prompt templates."""
    RETRIEVAL = "retrieval"
    EVIDENCE = "evidence"
    TIMELINE = "timeline"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    REFLECTION = "reflection"
    EVALUATION = "evaluation"
    PLANNER = "planner"
    NBA = "nba"
    EXPLAINABILITY = "explainability"


class PromptManager:
    """Manages prompts for all agents."""
    
    def __init__(self):
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates."""
        return {
            PromptTemplate.RETRIEVAL: """You are a legal retrieval specialist. Analyze the user query and case context to formulate an effective search strategy.

Query: {query}
Case Type: {case_type}
Case Context: {case_context}

Context from Memory:
{memory_context}

Retrieved Knowledge:
{retrieved_knowledge}

Task: Identify the most relevant legal documents, statutes, precedents, and case law that should be retrieved.

Respond in JSON format:
{{
    "search_queries": ["query1", "query2"],
    "document_types": ["type1", "type2"],
    "priority_sources": ["source1", "source2"],
    "reasoning": "explanation of search strategy"
}}""",
            
            PromptTemplate.EVIDENCE: """You are a legal evidence analyst. Analyze all available evidence for the case.

Case ID: {case_id}
Case Type: {case_type}

Retrieved Evidence Documents:
{retrieved_knowledge}

Memory Context (Previous Analysis):
{memory_context}

Task: Analyze evidence quality, identify gaps, conflicts, and provide assessment.

Respond in JSON format:
{{
    "strong_evidence": [{{"id": "1", "description": "...", "quality": "strong"}}],
    "weak_evidence": [{{"id": "2", "description": "...", "quality": "weak"}}],
    "missing_evidence": ["missing item 1", "missing item 2"],
    "conflicts": ["conflict description"],
    "overall_strength": "strong|moderate|weak|insufficient",
    "reasoning": "detailed analysis"
}}""",
            
            PromptTemplate.TIMELINE: """You are a legal timeline specialist. Extract and organize key events chronologically.

Case ID: {case_id}
Case Documents: {case_context}

Retrieved Knowledge:
{retrieved_knowledge}

Memory Context:
{memory_context}

Task: Build a comprehensive timeline of all events, deadlines, and milestones.

Respond in JSON format:
{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "description": "event description",
            "type": "event_type",
            "is_deadline": false,
            "is_urgent": false
        }}
    ],
    "critical_deadlines": ["deadline1", "deadline2"],
    "overdue_items": ["item1"]
}}""",
            
            PromptTemplate.RISK: """You are a legal risk assessment specialist. Identify and evaluate all risks in the case.

Case ID: {case_id}
Case Type: {case_type}
Case Context: {case_context}

Retrieved Knowledge:
{retrieved_knowledge}

Evidence Analysis:
{evidence_summary}

Timeline Summary:
{timeline_summary}

Memory Context (Historical Risks):
{memory_context}

Task: Identify legal, procedural, financial, and reputational risks.

Respond in JSON format:
{{
    "risks": [
        {{
            "risk_id": "R1",
            "type": "legal|procedural|financial|reputational",
            "description": "risk description",
            "severity": "critical|high|medium|low",
            "probability": 0.8,
            "impact": "impact description",
            "mitigation": "mitigation strategy"
        }}
    ],
    "overall_risk_level": "critical|high|medium|low",
    "risk_score": 75.5
}}""",
            
            PromptTemplate.RECOMMENDATION: """You are a senior legal strategist. Provide actionable next best actions.

Case Summary: {case_context}
Evidence Analysis: {evidence_summary}
Timeline: {timeline_summary}
Risk Assessment: {risk_summary}

Retrieved Knowledge:
{retrieved_knowledge}

Memory Context (Previous Recommendations):
{memory_context}

Task: Recommend the top 3-5 next best actions with clear reasoning and priority.

Respond in JSON format:
{{
    "recommendations": [
        {{
            "action": "specific action",
            "priority": "urgent|high|medium|low",
            "rationale": "detailed reasoning",
            "expected_outcome": "outcome",
            "deadline": "YYYY-MM-DD",
            "assigned_to": "role"
        }}
    ],
    "overall_strategy": "strategic approach summary"
}}""",
            
            PromptTemplate.REFLECTION: """You are a legal quality assurance specialist. Review and critique the analysis.

Original Query: {query}
Retrieval Results: {retrieval_summary}
Evidence Analysis: {evidence_summary}
Risk Assessment: {risk_summary}
Recommendations: {recommendations}

Task: Identify gaps, inconsistencies, and areas for improvement.

Respond in JSON format:
{{
    "quality_score": 85,
    "gaps": ["gap1", "gap2"],
    "inconsistencies": ["issue1"],
    "improvements": ["suggestion1", "suggestion2"],
    "confidence": 0.85
}}""",
            
            PromptTemplate.EVALUATION: """You are a legal evaluation specialist. Assess the quality and completeness of the analysis.

Analysis Components:
- Retrieval: {retrieval_summary}
- Evidence: {evidence_summary}
- Timeline: {timeline_summary}
- Risk: {risk_summary}
- Recommendations: {recommendations}

Task: Evaluate completeness, accuracy, and actionability.

Respond in JSON format:
{{
    "scores": {{
        "completeness": 0.85,
        "accuracy": 0.90,
        "actionability": 0.80
    }},
    "overall_score": 0.85,
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "recommendations": ["improvement1"]
}}""",
            
            PromptTemplate.PLANNER: """You are an AI planning specialist. Create an execution plan for the case analysis.

Case Query: {query}
Case Type: {case_type}
Available Agents: {available_agents}

Memory Context:
{memory_context}

Task: Create a step-by-step execution plan selecting appropriate agents.

Respond in JSON format:
{{
    "steps": [
        {{
            "step": 1,
            "agent": "retrieval_agent",
            "description": "Retrieve relevant legal knowledge",
            "dependencies": []
        }}
    ],
    "estimated_duration_seconds": 30,
    "parallel_execution": true
}}"""
        }
    
    def get_prompt(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any]
    ) -> str:
        """Get formatted prompt with variables."""
        prompt_template = self.prompts.get(template)
        if not prompt_template:
            raise ValueError(f"Prompt template {template} not found")
        
        # Fill in variables, use empty string for missing
        filled_prompt = prompt_template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            filled_prompt = filled_prompt.replace(placeholder, str(value))
        
        # Replace any remaining placeholders with empty string
        import re
        filled_prompt = re.sub(r'\{[^}]+\}', '', filled_prompt)
        
        return filled_prompt
    
    def get_system_prompt(self, agent_type: str) -> str:
        """Get system prompt for agent type."""
        system_prompts = {
            "retrieval": "You are a legal knowledge retrieval specialist.",
            "evidence": "You are a legal evidence analyst.",
            "timeline": "You are a legal timeline specialist.",
            "risk": "You are a legal risk assessment expert.",
            "recommendation": "You are a senior legal strategist.",
            "reflection": "You are a legal quality assurance specialist.",
            "evaluation": "You are a legal evaluation expert.",
            "planner": "You are an AI planning and orchestration specialist.",
            "nba": "You are a senior legal strategist generating Next Best Actions.",
            "explainability": "You are a legal explainability specialist."
        }
        return system_prompts.get(agent_type, "You are a helpful legal AI assistant.")


_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get singleton prompt manager."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
