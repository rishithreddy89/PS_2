"""
OpenRouter-powered Recommendation Agent.

Reads case documents and description from ExecutionContext,
builds a detailed legal analysis prompt, calls the OpenRouter API,
and returns structured recommendations in a single pass.

NEVER returns mock data.  On any OpenRouter failure the agent
returns AgentExecutionStatus.FAILED with the real error so
the caller can surface it to the user.
"""

import json
import time
from typing import Any, Dict, List
from fastapi.encoders import jsonable_encoder

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.utils.logging.logger import get_logger
from app.schemas.nba import NBAResponse

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an elite, highly experienced litigation attorney embedded inside LexMind AI.
Your task is to analyse a legal case and produce specific, actionable, heavily grounded recommendations.
Do not act like a generic LLM. You must provide a senior attorney's executive legal opinion and robust strategic litigation planning.

You MUST respond with a single valid JSON object exactly matching the provided JSON schema.

### Core Reasoning Directives:
1. **Recommendation Prioritization**: Never assign Priority arbitrarily. Calculate dynamically using factors like upcoming court deadlines, limitation periods, risk of losing evidence, probability of success, financial impact, and urgency.
2. **Confidence Scoring**: A backend computed confidence score is provided in the prompt context. Use it and explain WHY it is appropriate based on evidence quality. Do not invent your own confidence numbers.
3. **Legal Issue Identification**: Dynamically identify every legal issue supported by evidence. Do not invent issues.
4. **Recommendation Justification**: Explain: Why appropriate? Why now? What evidence supports it? What facts weaken it? What assumptions were required?
5. **Evidence Traceability (STRICT GUIDELINE)**: Every recommendation must cite supporting evidence explicitly (Document, Chunk ID, Quote). Never fabricate citations. You MUST ONLY use the provided `chunk_id` values from the retrieval results.
6. **Contradiction Analysis**: Automatically identify conflicts and explain why this matters legally.
7. **Counterarguments**: Generate likely opposing counsel arguments. Evaluate the strength and likelihood of success.
8. **No Hallucinations (CRITICAL)**: You MUST NOT invent: laws, sections, precedents, case IDs, court names, confidence, similarity, probabilities, dates, litigation risks. Reason ONLY using retrieved evidence.
9. **Action Plan**: Generate a chronological, dynamically calculated litigation plan.
10. **Executive Legal Opinion**: At the top level, generate a concise, senior-level assessment including overall case strength, primary claim, strongest/weakest evidence, primary recommendation, and overall confidence.
11. **Output Quality**: Every recommendation must be unique, evidence-backed, fact-specific, explainable, traceable, and professional.
12. **Complete Data Generation**: Do not leave any field empty. If unavailable, explicitly state "Not retrieved from knowledge base."

Return ONLY a valid JSON object matching the requested schema. Do not include markdown formatting or explanations outside of the JSON.
"""


def _build_prompt(
    case_id: str,
    case_description: str,
    case_type: str,
    jurisdiction: str,
    shared_context: Dict[str, Any]
) -> str:
    """Build a targeted legal analysis prompt injecting the JSON schema."""
    
    timeline = shared_context.get("timeline", [])
    evidence = shared_context.get("evidence_matrix", [])
    backend_conf = shared_context.get("backend_confidence", 0.0)
    
    statutes = shared_context.get("retrieved_statutes", [])
    precedents = shared_context.get("retrieved_precedents", [])
    
    # Trim retrieved knowledge to top chunks to save tokens
    knowledge_text = shared_context.get("retrieved_knowledge_text", "")
    knowledge_chunks = knowledge_text.split("\n\n")
    trimmed_knowledge = "\n\n".join(knowledge_chunks[:10])
    
    # Extract JSON schema from NBAResponse dynamically
    try:
        schema = NBAResponse.model_json_schema()
    except Exception:
        schema = NBAResponse.schema()
        
    def _format_docs(docs) -> str:
        if not docs:
            return "No matching records retrieved."
        return "\n\n".join([
            f"[Chunk ID: {getattr(d, 'chunk_id', 'unknown')} | Score: {getattr(d, 'final_score', 0.0):.2f}]\n{getattr(d, 'content', '')}"
            for d in docs[:5]
        ])
        
    return f"""## Legal Case Analysis Request
**Case ID:** {case_id}
**Case Type:** {case_type or 'Not specified'}
**Jurisdiction:** {jurisdiction or 'Not specified'}

## Backend Metrics
**Backend Computed Confidence:** {backend_conf:.2f} (Use this value for your reasoning)

## Context
### Evidence Matrix (Summary)
{json.dumps(jsonable_encoder(evidence[:15]), indent=2)}

### Timeline (Summary)
{json.dumps(jsonable_encoder(timeline[:15]), indent=2)}

### Retrieved Knowledge (Top Case Document Chunks)
{trimmed_knowledge}

### Retrieved Statutes
{_format_docs(statutes)}

### Retrieved Precedents
{_format_docs(precedents)}

## Task
Generate a comprehensive Next Best Action (NBA) report based on the provided context.
You MUST output EXACTLY one valid JSON object conforming to the following JSON schema:

```json
{json.dumps(schema, indent=2)}
```

Ensure all required fields are present and correctly typed. Return ONLY valid JSON.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Agent class
# ──────────────────────────────────────────────────────────────────────────────


class RecommendationAgent(BaseAgent):
    """
    Production recommendation agent powered by OpenRouter.

    Returns structured JSON recommendations grounded in case documents in a single pass.
    Raises / returns FAILED on any LLM error — never falls back to mock data.
    """

    def __init__(self):
        super().__init__(
            agent_id="recommendation_agent",
            name="Recommendation Agent",
            description=(
                "Produces AI-powered legal recommendations by analysing case "
                "documents and description via OpenRouter."
            ),
            version="3.0.0",
            supported_domains=["*"],
            priority=5,
        )

    @property
    def capabilities(self) -> List[str]:
        return ["recommendation", "decision_support", "legal_analysis", "nba_generation"]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def validate(self, context: ExecutionContext) -> bool:
        """Always executable — LLM errors are surfaced in execute()."""
        return True

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """
        Call OpenRouter to generate legal recommendations in a single pass.

        On success:  AgentExecutionStatus.COMPLETED with structured output.
        On failure:  AgentExecutionStatus.FAILED with the real error message.
                     Never returns mock data.
        """
        start_time = time.time()
        input_data = context.input_data or {}

        case_id = context.case_id or input_data.get("case_id", "unknown")
        case_description = input_data.get("description", "")
        case_type = input_data.get("case_type", "")
        jurisdiction = input_data.get("jurisdiction", "")
        
        # Log retrieved chunks
        retrieved_docs = context.get_shared("retrieved_documents", [])
        statutes = context.get_shared("retrieved_statutes", [])
        precedents = context.get_shared("retrieved_precedents", [])
        backend_conf = context.get_shared("backend_confidence", 0.0)
        knowledge_text = context.get_shared("retrieved_knowledge_text", "")
        
        chunk_ids = [getattr(doc, "chunk_id", "unknown") for doc in retrieved_docs]
        if not chunk_ids and isinstance(retrieved_docs, list) and len(retrieved_docs) > 0 and isinstance(retrieved_docs[0], dict):
            chunk_ids = [doc.get("chunk_id", "unknown") for doc in retrieved_docs]
            
        logger.info(
            "RecommendationAgent Input",
            agent_id=self.agent_id,
            case_id=case_id,
            retrieved_chunks=len(retrieved_docs),
            retrieved_statutes=len(statutes),
            retrieved_precedents=len(precedents),
            backend_confidence=backend_conf,
            retrieved_knowledge_length=len(knowledge_text),
            retrieved_chunk_ids=chunk_ids
        )

        if not retrieved_docs:
            error_msg = "RetrievalError: No supporting evidence retrieved from indexed documents. Cannot generate recommendations without evidence."
            logger.error(error_msg, agent_id=self.agent_id, case_id=case_id)
            raise ValueError(error_msg)

        try:
            from app.llm import get_openrouter_service
            from app.llm.normalization import normalize_nba_response
            openrouter_service = get_openrouter_service()

            prompt = _build_prompt(
                case_id=case_id,
                case_description=case_description,
                case_type=case_type,
                jurisdiction=jurisdiction,
                shared_context=context.shared_context
            )
            
            logger.info("Executing single-pass recommendation generation", agent_id=self.agent_id)
            
            # Request completion with meta tracking enabled (robust schema + max 1 retry)
            ai_response, meta = await openrouter_service.complete_structured(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                response_model=NBAResponse,
                normalize_func=normalize_nba_response,
                return_meta=True
            )
            
            if hasattr(ai_response, 'model_dump'):
                parsed = ai_response.model_dump(mode="json")
            else:
                parsed = jsonable_encoder(ai_response.dict())

            total_duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "OpenRouter single-pass generation completed",
                agent_id=self.agent_id,
                case_id=case_id,
                prompt_tokens=meta.get("input_tokens", 0),
                completion_tokens=meta.get("output_tokens", 0),
                openrouter_latency_ms=round(meta.get("duration_ms", 0), 1),
                validation_retries=meta.get("validation_retries", 0),
                total_duration_ms=round(total_duration_ms, 1),
            )

        except Exception as llm_err:
            total_duration_ms = (time.time() - start_time) * 1000
            error_msg = f"OpenRouter API call failed during generation/validation: {llm_err}"

            logger.error(
                "OpenRouter API error — NO fallback, returning VALIDATION_ERROR/FAILED",
                agent_id=self.agent_id,
                case_id=case_id,
                error=error_msg,
                duration_ms=round(total_duration_ms, 1),
            )

            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=error_msg,
                duration_ms=total_duration_ms,
            )

        raw_recs = parsed.get("recommendations", [])
        
        # Log OpenRouter parsed response payload to verify all fields are present
        logger.info(
            "OpenRouter raw parsed response fields",
            agent_id=self.agent_id,
            case_id=case_id,
            top_level_keys=list(parsed.keys()),
            first_rec_keys=list(raw_recs[0].keys()) if raw_recs else [],
            first_rec_empty_keys=[k for k, v in (raw_recs[0].items() if raw_recs else {}) if not v]
        )
        
        logger.info(
            "OpenRouter recommendations ready",
            agent_id=self.agent_id,
            case_id=case_id,
            count=len(raw_recs),
            titles=[r.get("title") for r in raw_recs],
        )
        
        context.set_shared("recommendations", raw_recs)

        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            status=AgentExecutionStatus.COMPLETED,
            output=parsed,
            duration_ms=(time.time() - start_time) * 1000,
        )

