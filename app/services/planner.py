"""
Planner service for agent orchestration.
"""

from typing import Any, Dict, Optional
from uuid import uuid4

from app.agents.context import ExecutionContext
from app.agents.orchestrator import Orchestrator, OrchestratorConfig
from app.agents.planner import PlannerAgent
from app.schemas.agent import ExecutionResult
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class PlannerService:
    """
    Planner service for dynamic agent orchestration.
    
    Handles:
    - Request analysis
    - Plan creation
    - Agent orchestration
    - Result aggregation
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.orchestrator = Orchestrator(OrchestratorConfig())

    async def execute_workflow(
        self,
        input_data: Dict[str, Any],
        case_id: Optional[str] = None,
        user_id: Optional[str] = None,
        domain: str = "general",
        workflow: str = "default",
    ) -> ExecutionResult:
        """
        Execute complete workflow with planning and orchestration.

        Args:
            input_data: Input data for workflow
            case_id: Optional case ID
            user_id: Optional user ID
            domain: Target domain
            workflow: Workflow type

        Returns:
            ExecutionResult with all outputs
        """
        # Create execution context
        context = ExecutionContext(
            request_id=str(uuid4()),
            case_id=case_id,
            user_id=user_id,
            domain=domain,
            workflow=workflow,
            input_data=input_data,
        )

        logger.info(
            "Workflow execution started",
            request_id=context.request_id,
            domain=domain,
            workflow=workflow,
        )

        try:
            # Step 1: Create plan
            planner_response = await self.planner.execute(context)
            
            if planner_response.status != "completed":
                raise Exception(f"Planning failed: {planner_response.error}")

            # Extract plan
            from app.schemas.agent import ExecutionPlan
            plan_data = planner_response.output.get("plan")
            plan = ExecutionPlan(**plan_data)

            # Step 2: Execute plan
            result = await self.orchestrator.execute(plan, context)

            logger.info(
                "Workflow execution completed",
                request_id=context.request_id,
                status=result.status,
            )

            return result

        except Exception as e:
            logger.error(
                "Workflow execution failed",
                request_id=context.request_id,
                error=str(e),
            )
            raise

    async def create_plan(
        self,
        task_requirements: Dict[str, Any],
        domain: str = "general",
    ) -> Dict[str, Any]:
        """
        Create execution plan without executing.

        Args:
            task_requirements: Task requirements
            domain: Target domain

        Returns:
            Execution plan
        """
        context = ExecutionContext(
            domain=domain,
            input_data=task_requirements,
        )

        planner_response = await self.planner.execute(context)
        
        if planner_response.status != "completed":
            raise Exception(f"Planning failed: {planner_response.error}")

        return planner_response.output.get("plan", {})

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get execution status (placeholder for future implementation).

        Args:
            execution_id: Execution ID

        Returns:
            Execution status
        """
        # TODO: Implement execution tracking in database
        return {
            "execution_id": execution_id,
            "status": "unknown",
            "message": "Execution tracking not yet implemented",
        }


# Global planner service instance
planner_service = PlannerService()
