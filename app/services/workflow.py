"""
Complete workflow service integrating all components.
"""

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import ExecutionContext
from app.agents.orchestrator import Orchestrator, OrchestratorConfig
from app.agents.planner import PlannerAgent
from app.knowledge.ingestion import get_ingestion_service
from app.llm.openrouter_service import OpenRouterService
from app.memory.implementation import get_memory_manager
from app.models.planner_execution import PlannerExecution as DBPlannerExecution
from app.schemas.agent import ExecutionResult
from app.utils.logging.logger import get_logger
from app.utils.serialization import make_json_safe

logger = get_logger(__name__)


class WorkflowExecutionService:
    """
    End-to-end workflow execution service.
    
    Integrates:
    - Document ingestion
    - Planning
    - Orchestration
    - Agent execution
    - Retrieval
    - LLM processing
    - Memory updates
    - Database persistence
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.planner = PlannerAgent()
        self.orchestrator = Orchestrator(OrchestratorConfig())
        self.ingestion = get_ingestion_service()
        self.openrouter_service = OpenRouterService()
        self.memory_manager = get_memory_manager()

    async def execute_case_workflow(
        self,
        case_id: str,
        documents: Optional[List[Dict[str, Any]]] = None,
        workflow_type: str = "full_analysis",
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute complete case workflow with streaming updates.
        
        Args:
            case_id: Case ID
            documents: Optional documents to ingest
            workflow_type: Type of workflow to execute
            user_id: User ID
            
        Yields:
            Status updates during execution
        """
        execution_id = str(uuid4())
        request_id = str(uuid4())
        
        yield {
            "event": "workflow_started",
            "execution_id": execution_id,
            "case_id": case_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Step 1: Document Ingestion
            if documents:
                yield {"event": "ingestion_started", "document_count": len(documents)}
                
                for doc in documents:
                    # For now, we'll skip actual file ingestion in workflow
                    # In production, this would write files and call ingest_file
                    pass
                
                yield {"event": "ingestion_completed"}
            
            # Step 2: Build execution context (grounded with case metadata and document text content)
            from app.models.case import Case
            from app.models.case_document import CaseDocument
            from sqlalchemy import select
            import os

            case_result = await self.db.execute(select(Case).where(Case.id == case_id))
            db_case = case_result.scalar_one_or_none()

            case_description = ""
            case_type = ""
            jurisdiction = ""
            documents_data = []

            if db_case:
                case_description = db_case.description or ""
                case_type = db_case.case_type or ""
                jurisdiction = db_case.jurisdiction or ""
                
                # Fetch associated documents
                doc_result = await self.db.execute(select(CaseDocument).where(CaseDocument.case_id == case_id))
                db_docs = doc_result.scalars().all()
                
                from app.knowledge.ingestion import get_ingestion_service
                ingestion_service = get_ingestion_service()
                
                for doc in db_docs:
                    doc_content = ""
                    if doc.file_path and os.path.exists(doc.file_path):
                        try:
                            doc_content = ingestion_service._read_file(doc.file_path)
                        except Exception as parse_e:
                            logger.error("Failed to read document for workflow", file=doc.file_path, error=str(parse_e))
                    documents_data.append({
                        "id": doc.id,
                        "filename": doc.file_name,
                        "content": doc_content,
                        "document_type": doc.document_type,
                    })

            context = ExecutionContext(
                request_id=request_id,
                case_id=case_id,
                user_id=user_id,
                domain="legal",
                workflow=workflow_type,
                input_data={
                    "case_id": case_id,
                    "description": case_description,
                    "case_type": case_type,
                    "jurisdiction": jurisdiction,
                    "documents": documents_data,
                    "analyze_evidence": True,
                    "risk_assessment": True,
                    "generate_recommendation": True,
                },
            )
            
            # Step 3: Planning
            yield {"event": "planning_started"}
            
            planner_response = await self.planner.execute(context)
            
            if planner_response.status != "completed":
                raise Exception(f"Planning failed: {planner_response.error}")
            
            from app.schemas.agent import ExecutionPlan
            plan = ExecutionPlan(**planner_response.output["plan"])
            
            yield {
                "event": "planning_completed",
                "plan": {
                    "agent_count": len(plan.workflow_steps),
                    "agents": [s.agent_name for s in plan.workflow_steps],
                    "estimated_duration_ms": plan.decision.estimated_duration_ms,
                }
            }
            
            # Step 3.5: Retrieval Stage
            yield {"event": "retrieval_started"}
            
            from app.knowledge import get_retrieval_service
            retrieval_service = get_retrieval_service()
            
            query = case_description or "facts, evidence, events, and timeline"
            collection = "case_documents"
            filters = {"case_id": case_id}
            
            logger.info(
                "Workflow Retrieval Started",
                case_id=case_id,
                collection=collection,
                query=query,
                filter=filters,
            )
            
            retrieved_results = await retrieval_service.retrieve(
                query=query,
                collections=[collection],
                filters=filters,
                top_k=10,
            )
            
            logger.info(
                "Workflow Retrieval Completed",
                retrieved_chunks=len(retrieved_results) if retrieved_results else 0,
                chunk_ids=[c.chunk_id for c in retrieved_results] if retrieved_results else [],
                scores=[c.final_score for c in retrieved_results] if retrieved_results else [],
                document_ids=[c.document_id for c in retrieved_results] if retrieved_results else [],
                metadata=[c.metadata for c in retrieved_results] if retrieved_results else [],
            )
            
            if not retrieved_results:
                raise ValueError(
                    f"No evidence retrieved for case_id={case_id} in collection '{collection}' with filters {filters} for query '{query}'"
                )
            
            try:
                statute_results = await retrieval_service.retrieve(
                    query=query,
                    collections=["statutes"],
                    filters=None,
                    top_k=5,
                )
            except Exception:
                statute_results = []
                
            try:
                precedent_results = await retrieval_service.retrieve(
                    query=query,
                    collections=["precedents"],
                    filters=None,
                    top_k=5,
                )
            except Exception:
                precedent_results = []

            avg_retrieval_score = sum(r.final_score for r in retrieved_results) / len(retrieved_results) if retrieved_results else 0.0
            evidence_completeness = min(len(retrieved_results) / 10.0, 1.0)
            precedent_availability = 1.0 if precedent_results else 0.0
            statute_availability = 1.0 if statute_results else 0.0
            
            backend_confidence = (
                0.35 * avg_retrieval_score +
                0.30 * evidence_completeness +
                0.20 * precedent_availability +
                0.15 * statute_availability
            )
            backend_confidence = max(0.0, min(backend_confidence, 1.0))

            context.set_shared("retrieved_documents", retrieved_results)
            context.set_shared("retrieved_statutes", statute_results)
            context.set_shared("retrieved_precedents", precedent_results)
            context.set_shared("backend_confidence", backend_confidence)
            
            context.set_shared(
                "retrieved_knowledge_text",
                "\n\n".join([
                    f"[Doc: {getattr(doc, 'document_id', 'unknown')} | Type: {getattr(doc, 'metadata', {}).get('document_type', 'unknown')}]\n{getattr(doc, 'content', '')}"
                    for doc in retrieved_results
                ])
            )
            
            logger.info(
                "Shared Context Updated",
                retrieved_documents_count=len(retrieved_results),
                retrieved_statutes_count=len(statute_results),
                retrieved_precedents_count=len(precedent_results),
                backend_confidence=backend_confidence,
            )
            
            yield {"event": "retrieval_completed", "retrieved_chunks": len(retrieved_results)}
            
            # Step 4: Execute agents
            yield {"event": "orchestration_started"}
            
            # Execute with progress updates
            result = await self._execute_with_progress(plan, context)
            
            # Yield agent updates
            for trace in result.execution_trace:
                yield {
                    "event": "agent_completed",
                    "agent_name": trace.agent_name,
                    "status": trace.status,
                    "duration_ms": trace.duration_ms,
                }
            
            yield {
                "event": "orchestration_completed",
                "status": result.status,
                "total_duration_ms": result.total_duration_ms,
            }
            
            # Step 5: Persist execution
            await self._persist_execution(execution_id, case_id, result)
            
            yield {
                "event": "workflow_completed",
                "execution_id": execution_id,
                "status": result.status,
                "final_output": result.final_output,
            }
            
            # Yield final completion event to signal client to close SSE connection
            yield {
                "event": "completed",
                "status": "completed",
                "execution_id": execution_id,
            }
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e), execution_id=execution_id)
            yield {
                "event": "workflow_failed",
                "execution_id": execution_id,
                "error": str(e),
            }
            # Always emit terminal completed event so frontend stops spinner
            yield {
                "event": "completed",
                "status": "failed",
                "execution_id": execution_id,
                "error": str(e),
            }

    async def _execute_with_progress(
        self,
        plan: "ExecutionPlan",
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute plan with progress tracking."""
        result = await self.orchestrator.execute(plan, context)

        # --- FULL ORCHESTRATOR OUTPUT LOG (for diagnostics) ---
        logger.info(
            "Orchestrator raw result",
            status=str(result.status),
            agent_response_count=len(result.agent_responses),
            agent_ids=[r.agent_id for r in result.agent_responses],
            agent_statuses={r.agent_id: str(r.status) for r in result.agent_responses},
        )
        for resp in result.agent_responses:
            logger.info(
                "Agent raw output",
                agent_id=resp.agent_id,
                agent_name=resp.agent_name,
                status=str(resp.status),
                output=resp.output,
                error=resp.error,
            )
        logger.info(
            "final_output structure",
            final_output_keys=list(result.final_output.keys()),
            agent_outputs_keys=list(result.final_output.get("agent_outputs", {}).keys()),
        )

        return result

    async def _persist_execution(
        self,
        execution_id: str,
        case_id: str,
        result: ExecutionResult,
    ) -> None:
        """Persist execution to database and generate recommendations."""
        logger.info("Persisting execution", execution_id=execution_id, case_id=case_id)

        # Serialize all JSON payloads before touching the DB.
        # model_dump() may return datetime / UUID / Enum objects; make_json_safe
        # converts them recursively to ISO strings / str / .value.
        input_data = make_json_safe({"case_id": case_id})
        execution_plan = make_json_safe(result.plan.model_dump() if result.plan else {})
        agent_outputs = make_json_safe(result.model_dump().get("agent_responses", {}))
        final_output = make_json_safe(result.final_output)
        meta_data = make_json_safe({
            "execution_trace": result.model_dump().get("execution_trace", []),
            "workflow_type": "full_analysis",
        })

        try:
            execution = DBPlannerExecution(
                id=execution_id,
                case_id=case_id,
                status=result.status if isinstance(result.status, str) else result.status.value,
                execution_type="full_analysis",
                input_data=input_data,
                execution_plan=execution_plan,
                agent_outputs=agent_outputs,
                final_output=final_output,
                duration_ms=result.total_duration_ms,
                error_message=result.error,
                meta_data=meta_data,
            )

            self.db.add(execution)
            await self.db.flush()
            logger.info("PlannerExecution saved", execution_id=execution_id)

            # Generate recommendations — always pass the full result so we can
            # scan agent_responses directly by real agent_id.
            if result.status in ("completed", "COMPLETED") or (
                hasattr(result.status, "value") and result.status.value == "completed"
            ):
                await self._generate_recommendations(
                    case_id,
                    result.final_output,
                    execution_result=result,
                )


            await self.db.commit()
            logger.info("Workflow completed successfully", execution_id=execution_id)

        except Exception as persist_error:
            logger.error(
                "PlannerExecution persistence failed — rolling back",
                execution_id=execution_id,
                error=str(persist_error),
            )
            await self.db.rollback()
            raise RuntimeError(
                f"Failed to persist PlannerExecution {execution_id}: {persist_error}"
            ) from persist_error

    async def trigger_workflow_on_case_creation(
        self,
        case_id: str,
        case_data: Dict[str, Any],
    ) -> str:
        """
        Automatically trigger workflow when case is created.
        
        Args:
            case_id: Case ID
            case_data: Case creation data
            
        Returns:
            Execution ID
        """
        execution_id = str(uuid4())
        
        # Start workflow in background (would use celery/background tasks in production)
        logger.info("Auto-triggering workflow", case_id=case_id, execution_id=execution_id)
        
        return execution_id

    async def process_feedback_and_update_memory(
        self,
        recommendation_id: str,
        feedback: Dict[str, Any],
        case_id: str,
    ) -> None:
        """
        Process human feedback and update memory.
        
        Args:
            recommendation_id: Recommendation ID
            feedback: Feedback data
            case_id: Case ID
        """
        logger.info("Processing feedback", recommendation_id=recommendation_id)
        
        # Store in memory
        await self.memory_manager.store_feedback(
            case_id=case_id,
            feedback={
                "recommendation_id": recommendation_id,
                **feedback,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        
        logger.info("Feedback stored in memory")
    
    async def _generate_recommendations(
        self,
        case_id: str,
        agent_outputs: Dict[str, Any],
        execution_result: Optional["ExecutionResult"] = None,
    ) -> None:
        """
        Persist recommendations extracted from any agent that produced them.

        Strategy (in order):
        1. Scan every agent in result.agent_responses by actual agent_id
           (never assumes a fixed name like "nba_agent" or "recommendation_agent").
        2. Fall back to scanning final_output["agent_outputs"] dict.

        Handles both output formats:
        - List of dicts  (NBA-style: {action, reasoning, confidence_score, ...})
        - List of strings (RecommendationAgent-style: ["Do X", "Do Y"])
        """
        from app.models.recommendation import Recommendation

        # Log everything we received so issues are visible immediately.
        if execution_result is not None:
            logger.info(
                "[EXTRACTION] agent_responses received",
                count=len(execution_result.agent_responses),
                agents=[
                    {
                        "agent_id": r.agent_id,
                        "status": str(r.status),
                        "output_keys": list((r.output or {}).keys()),
                        "has_recommendations": bool((r.output or {}).get("recommendations")),
                    }
                    for r in execution_result.agent_responses
                ],
            )
        else:
            logger.warning("[EXTRACTION] execution_result is None — only final_output fallback available")

        logger.info(
            "[EXTRACTION] final_output snapshot",
            case_id=case_id,
            final_output_keys=list((agent_outputs or {}).keys()),
            agent_outputs_keys=list((agent_outputs or {}).get("agent_outputs", {}).keys()),
        )

        # candidate_sources: list of (agent_id, recs_list, shared_confidence, shared_reasoning)
        candidate_sources: List[Any] = []

        # --- Primary: scan live agent_responses from ExecutionResult ---
        if execution_result is not None:
            for resp in execution_result.agent_responses:
                out = resp.output or {}
                recs = out.get("recommendations")
                logger.info(
                    "[EXTRACTION] checking agent",
                    agent_id=resp.agent_id,
                    status=str(resp.status),
                    output_keys=list(out.keys()),
                    recommendations_found=bool(recs),
                    recommendations_count=len(recs) if recs else 0,
                    raw_output=out,
                )
                if recs:
                    candidate_sources.append((
                        resp.agent_id,
                        recs,
                        out.get("confidence", out.get("confidence_score", 0.8)),
                        out.get("reasoning", ""),
                        out
                    ))
                    logger.info(
                        "[EXTRACTION] Found recommendations from agent",
                        agent_id=resp.agent_id,
                        count=len(recs),
                        sample=str(recs[0]) if recs else None,
                    )
                else:
                    # Log the raw response so nothing is silently ignored
                    logger.warning(
                        "[EXTRACTION] Agent has no recommendations key in output",
                        agent_id=resp.agent_id,
                        status=str(resp.status),
                        raw_output=out,
                        error=resp.error,
                    )

        # --- Fallback: scan final_output["agent_outputs"] dict ---
        if not candidate_sources and agent_outputs:
            inner = agent_outputs.get("agent_outputs", {})
            logger.info(
                "[EXTRACTION] Falling back to final_output scan",
                agent_output_keys=list((inner or {}).keys()),
            )
            for agent_id, out in (inner or {}).items():
                if not isinstance(out, dict):
                    continue
                recs = out.get("recommendations")
                if recs:
                    candidate_sources.append((
                        agent_id,
                        recs,
                        out.get("confidence", out.get("confidence_score", 0.8)),
                        out.get("reasoning", ""),
                        out
                    ))
                    logger.info(
                        "[EXTRACTION] Found recommendations in final_output",
                        agent_id=agent_id,
                        count=len(recs),
                    )

        if not candidate_sources:
            # Dump full raw state so nothing is silently ignored
            raw_responses = [
                {"agent_id": r.agent_id, "status": str(r.status), "output": r.output, "error": r.error}
                for r in (execution_result.agent_responses if execution_result else [])
            ]
            logger.warning(
                "[EXTRACTION] No recommendations found in any agent output",
                case_id=case_id,
                raw_agent_responses=raw_responses,
                final_output=agent_outputs,
            )
            return

        total_saved = 0

        for agent_id, raw_recs, shared_confidence, shared_reasoning, full_output in candidate_sources:
            recs_to_save = raw_recs[:3]  # top 3 per agent

            top_level_data = {}
            if isinstance(full_output, dict):
                top_level_data = {
                    "risk_assessment": full_output.get("litigation_risk", {}),
                    "timeline": full_output.get("action_plan", []),
                    "contradictions": full_output.get("contradiction_analysis", []),
                    "executive_opinion": full_output.get("executive_opinion", {}),
                }

            # ── Loud summary log before saving (as requested) ──────────
            print(f"\\n[RECOMMENDATIONS] Found {len(recs_to_save)} recommendation(s) from agent '{agent_id}'")
            for idx, r in enumerate(recs_to_save):
                _t = r if isinstance(r, str) else r.get("action", r.get("title", str(r)))
                _p = "medium" if isinstance(r, str) else r.get("priority", "medium")
                _c = shared_confidence if isinstance(r, str) else r.get("confidence_score", r.get("confidence", shared_confidence))
                print(f"  Recommendation {idx + 1}:")
                print(f"    title:      {_t}")
                print(f"    priority:   {_p}")
                print(f"    confidence: {_c}")
            print()

            logger.info(
                "[EXTRACTION] Persisting recommendations",
                agent_id=agent_id,
                count=len(recs_to_save),
                titles=[
                    (r if isinstance(r, str) else r.get("action", r.get("title", str(r))))
                    for r in recs_to_save
                ],
                confidence=shared_confidence,
            )

            for i, rec in enumerate(recs_to_save):
                # --- Normalise to dict ---
                if hasattr(rec, "model_dump"):
                    rec_dict: Dict[str, Any] = make_json_safe(rec.model_dump())
                elif hasattr(rec, "dict") and callable(rec.dict):
                    rec_dict = make_json_safe(rec.dict())
                elif isinstance(rec, dict):
                    rec_dict = make_json_safe(rec)
                elif isinstance(rec, str):
                    # RecommendationAgent returns plain strings
                    rec_dict = {
                        "title": rec,
                        "description": rec,
                        "reasoning": shared_reasoning or rec,
                        "confidence_score": float(shared_confidence) if shared_confidence else 0.8,
                        "priority": "medium",
                    }
                else:
                    rec_dict = make_json_safe({"title": str(rec)})

                # Log fields detected, persisted, and dropped
                detected_fields = set(rec_dict.keys())
                persisted_keys = {
                    "action", "title", "description", "reasoning", "confidence_score", "confidence",
                    "priority", "supporting_evidence", "evidence", "executive_summary", "justification",
                    "missing_evidence", "applicable_laws", "detailed_applicable_laws", "relevant_precedents",
                    "detailed_precedents", "legal_risks", "counterarguments", "alternative_strategies",
                    "next_best_actions", "expected_outcome", "urgency", "priority_explanation",
                    "confidence_explanation", "validation", "legal_basis", "alternative_actions", 
                    "alternatives", "expected_impact", "impact", "evidence_completeness_score", 
                    "source_citations", "rank"
                }
                dropped_fields = detected_fields - persisted_keys
                
                logger.info(
                    f"Recommendation contains {len(detected_fields)} fields. Persisted {len(detected_fields) - len(dropped_fields)} fields. Dropped {len(dropped_fields)} fields.",
                    agent_id=agent_id,
                    detected_fields=list(detected_fields),
                    dropped_fields=list(dropped_fields)
                )

                # Map to valid Recommendation model columns only
                title = (
                    rec_dict.get("action")
                    or rec_dict.get("title")
                    or f"Recommendation {i + 1}"
                )
                description = (
                    rec_dict.get("reasoning")
                    or rec_dict.get("description")
                    or rec_dict.get("action")
                    or str(title)
                )
                reasoning = rec_dict.get("reasoning") or rec_dict.get("description") or str(title)
                confidence = float(
                    rec_dict.get("confidence_score", rec_dict.get("confidence", shared_confidence or 0.8))
                )
                priority = str(rec_dict.get("priority", "medium"))

                # supporting_evidence must be an array for the JSON column now
                raw_evidence = rec_dict.get("supporting_evidence") or rec_dict.get("evidence")
                if isinstance(raw_evidence, list):
                    supporting = make_json_safe(raw_evidence)
                elif isinstance(raw_evidence, dict) and "items" in raw_evidence:
                    supporting = make_json_safe(raw_evidence["items"])
                else:
                    supporting = []

                # Grounding Validation Layer
                if not supporting:
                    logger.warning(
                        "Validation Error: Recommendation rejected due to missing supporting evidence.",
                        case_id=case_id,
                        title=title
                    )
                    continue
                
                has_chunk_id = False
                for item in supporting:
                    if isinstance(item, dict) and item.get("chunk_id"):
                        has_chunk_id = True
                        break
                
                if not has_chunk_id:
                    logger.warning(
                        "Validation Error: Recommendation rejected due to missing chunk_id in citations.",
                        case_id=case_id,
                        title=title
                    )
                    continue
                
                backend_conf = None
                if execution_result and execution_result.context:
                    backend_conf = execution_result.context.get_shared("backend_confidence")
                if backend_conf is not None:
                    confidence = backend_conf

                recommendation = Recommendation(
                    case_id=case_id,
                    action_type="next_best_action",
                    title=str(title)[:500],
                    description=str(description),
                    reasoning=str(reasoning),
                    confidence_score=min(max(confidence, 0.0), 1.0),
                    priority=priority,
                    status="pending",
                    supporting_evidence=supporting,
                    executive_summary=rec_dict.get("executive_summary", ""),
                    justification=make_json_safe(rec_dict.get("justification", {})),
                    missing_evidence=make_json_safe(rec_dict.get("missing_evidence", [])),
                    applicable_laws=make_json_safe(rec_dict.get("applicable_laws", [])),
                    detailed_applicable_laws=make_json_safe(rec_dict.get("detailed_applicable_laws", [])),
                    relevant_precedents=make_json_safe(rec_dict.get("relevant_precedents", [])),
                    detailed_precedents=make_json_safe(rec_dict.get("detailed_precedents", [])),
                    legal_risks=make_json_safe(rec_dict.get("legal_risks", [])),
                    counterarguments=make_json_safe(rec_dict.get("counterarguments", [])),
                    alternative_strategies=make_json_safe(rec_dict.get("alternative_strategies", [])),
                    next_best_actions=make_json_safe(rec_dict.get("next_best_actions", [])),
                    expected_outcome=rec_dict.get("expected_outcome", ""),
                    urgency=rec_dict.get("urgency", ""),
                    priority_explanation=rec_dict.get("priority_explanation", ""),
                    confidence_explanation=rec_dict.get("confidence_explanation", ""),
                    risk_assessment=make_json_safe(top_level_data.get("risk_assessment", {})),
                    timeline=make_json_safe(top_level_data.get("timeline", [])),
                    validation=make_json_safe(rec_dict.get("validation", {})),
                    contradictions=make_json_safe(top_level_data.get("contradictions", [])),
                    executive_opinion=make_json_safe(top_level_data.get("executive_opinion", {})),
                    meta_data=make_json_safe({
                        "generated_by": agent_id,
                        "rank": i + 1,
                        "generated_at": datetime.utcnow().isoformat(),
                        "legal_basis": rec_dict.get("legal_basis", ""),
                        "alternative_actions": rec_dict.get(
                            "alternative_actions", rec_dict.get("alternatives", [])
                        ),
                        "expected_impact": rec_dict.get(
                            "expected_impact", rec_dict.get("impact", "")
                        ),
                    }),
                )
                
                # Explicitly log exactly what is being saved per the user's request
                print(f"\\n[PERSISTENCE] Recommendation '{recommendation.title[:50]}' field save status:")
                for field in [
                    "executive_summary", "justification", "applicable_laws", 
                    "relevant_precedents", "legal_risks", "alternative_strategies", 
                    "timeline", "expected_outcome", "risk_assessment", "contradictions"
                ]:
                    val = getattr(recommendation, field)
                    if val and val != "[]" and val != "{}":
                        print(f"  ✓ {field} saved")
                    else:
                        print(f"  ✗ {field} missing or empty")
                print()
                
                self.db.add(recommendation)
                total_saved += 1

        await self.db.flush()
        logger.info(
            "All recommendations saved",
            case_id=case_id,
            total=total_saved,
        )

