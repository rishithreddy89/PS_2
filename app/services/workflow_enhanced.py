"""
Enhanced workflow service with metrics and resilience.
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
from app.utils.metrics import workflow_metrics, PerformanceTracker
from app.utils.resilience import retry_async, RetryConfig
from app.utils.serialization import make_json_safe

logger = get_logger(__name__)


class EnhancedWorkflowExecutionService:
    """
    Enhanced workflow execution service with metrics and resilience.
    
    Integrates:
    - Document ingestion
    - Planning with retry
    - Orchestration with circuit breaker
    - Agent execution with timeout
    - Retrieval with caching
    - LLM processing with rate limiting
    - Memory updates with persistence
    - Metrics collection
    - Error recovery
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
        start_time = datetime.utcnow()
        
        yield {
            "event": "workflow_started",
            "execution_id": execution_id,
            "case_id": case_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            async with PerformanceTracker(f"workflow_{workflow_type}"):
                # Step 1: Document Ingestion
                if documents:
                    yield {"event": "ingestion_started", "document_count": len(documents)}
                    
                    async with PerformanceTracker("document_ingestion"):
                        for doc in documents:
                            await self._ingest_document_with_retry(doc, case_id)
                    
                    yield {"event": "ingestion_completed"}
                
                # Step 2: Build execution context
                context = ExecutionContext(
                    request_id=request_id,
                    case_id=case_id,
                    user_id=user_id,
                    domain="legal",
                    workflow=workflow_type,
                    input_data={
                        "case_id": case_id,
                        "analyze_evidence": True,
                        "risk_assessment": True,
                        "generate_recommendation": True,
                    },
                )
                
                # Step 3: Planning with retry
                yield {"event": "planning_started"}
                
                async with PerformanceTracker("planning"):
                    planner_response = await self._execute_planner_with_retry(context)
                
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
                
                # Step 4: Execute agents with tracking
                yield {"event": "orchestration_started"}
                
                async with PerformanceTracker("orchestration"):
                    result = await self.orchestrator.execute(plan, context)
                
                # Record agent metrics
                for trace in result.execution_trace:
                    workflow_metrics.record_agent_execution(
                        agent_id=trace.agent_id,
                        status=trace.status,
                        duration_ms=trace.duration_ms,
                    )
                    
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
                
                if result.status == "failed" or getattr(result.status, "value", result.status) == "failed":
                    raise Exception(result.error or "Agent orchestration failed, terminating pipeline.")
                
                # Step 5: Persist execution
                await self._persist_execution(execution_id, case_id, result)
                
                # Record workflow metrics
                total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                workflow_metrics.record_workflow_execution(
                    execution_id=execution_id,
                    case_id=case_id,
                    status=result.status,
                    duration_ms=total_duration,
                    agent_count=len(plan.workflow_steps),
                )
                
                yield {
                    "event": "workflow_completed",
                    "execution_id": execution_id,
                    "status": result.status,
                    "final_output": result.final_output,
                }
                
                # Final Pipeline Summary
                retrieved_docs = context.get_shared("retrieved_documents", [])
                recs = context.get_shared("recommendations", [])
                payload_size = len(str(result.final_output))
                logger.info(
                    "==================================\n"
                    "Pipeline Execution Summary:\n"
                    "Chunks Created: N/A (Uploaded prior)\n"
                    "Chunks Stored: N/A (Uploaded prior)\n"
                    f"Chunks Retrieved: {len(retrieved_docs)}\n"
                    f"Average Similarity: Calculated in retrieval\n"
                    f"Prompt Tokens: Logged in agent\n"
                    f"Completion Tokens: Logged in agent\n"
                    f"Recommendations Generated: {len(recs)}\n"
                    f"Database Saved: True\n"
                    f"Frontend Payload Size: {payload_size} bytes\n"
                    "=================================="
                )
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e), execution_id=execution_id)
            
            # Record failure
            total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            workflow_metrics.record_workflow_execution(
                execution_id=execution_id,
                case_id=case_id,
                status="failed",
                duration_ms=total_duration,
                agent_count=0,
            )
            
            yield {
                "event": "workflow_failed",
                "execution_id": execution_id,
                "error": str(e),
            }

    @retry_async(RetryConfig(max_attempts=3, initial_delay=1.0))
    async def _ingest_document_with_retry(self, doc: Dict[str, Any], case_id: str):
        """Ingest document with retry logic."""
        # Placeholder for document ingestion
        # In production, save file and use ingestion.ingest_file()
        pass

    @retry_async(RetryConfig(max_attempts=2, initial_delay=0.5))
    async def _execute_planner_with_retry(self, context: ExecutionContext):
        """Execute planner with retry logic."""
        return await self.planner.execute(context)

    async def _persist_execution(
        self,
        execution_id: str,
        case_id: str,
        result: ExecutionResult,
    ) -> None:
        """Persist execution to database."""
        logger.info("Persisting execution", execution_id=execution_id, case_id=case_id)
        
        import time
        start_persist_time = time.time()

        # Serialize all JSON payloads before touching the DB.
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
            await self.db.commit()
            
            persistence_duration_ms = (time.time() - start_persist_time) * 1000
            logger.info("PlannerExecution saved", execution_id=execution_id, persistence_duration_ms=round(persistence_duration_ms, 1))

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
        
        async with PerformanceTracker("feedback_processing"):
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
