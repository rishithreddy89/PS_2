"""
Orchestrator for agent execution using LangGraph.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.agents.factory import agent_factory
from app.schemas.agent import (
    AgentExecutionStatus,
    AgentResponse,
    ExecutionPlan,
    ExecutionResult,
    ExecutionTrace,
    WorkflowStep,
)
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class OrchestratorConfig:
    """Orchestrator configuration."""
    
    max_retries: int = 3
    agent_timeout: int = 90
    workflow_timeout: int = 300
    enable_parallel: bool = False


class Orchestrator:
    """
    Agent orchestrator using LangGraph for dynamic execution.
    
    Responsibilities:
    - Build execution graph from plan
    - Execute agents in order
    - Handle failures and retries
    - Collect results and traces
    - Maintain execution context
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.logger = get_logger(__name__)

    async def execute(
        self,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute workflow based on plan.
        
        Args:
            plan: Execution plan from planner
            context: Execution context
            
        Returns:
            ExecutionResult with all outputs
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(
            "Orchestration started",
            execution_id=execution_id,
            plan_id=plan.plan_id,
            agent_count=len(plan.workflow_steps),
        )
        
        try:
            # Build execution graph
            graph = self._build_graph(plan, context)
            
            # Execute graph with hard timeout
            try:
                await asyncio.wait_for(
                    self._execute_graph(graph, plan, context),
                    timeout=self.config.workflow_timeout
                )
            except asyncio.TimeoutError:
                logger.error(
                    "Workflow timed out",
                    execution_id=execution_id,
                    timeout=self.config.workflow_timeout,
                )
                context.add_error("orchestrator", f"Workflow timed out after {self.config.workflow_timeout}s")
            
            # Collect results
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000
            
            result = ExecutionResult(
                execution_id=execution_id,
                request_id=context.request_id,
                case_id=context.case_id,
                status=AgentExecutionStatus.COMPLETED if not context.has_errors() else AgentExecutionStatus.FAILED,
                plan=plan,
                agent_responses=list(context.agent_outputs.values()),
                execution_trace=context.execution_trace,
                start_time=start_time,
                end_time=end_time,
                total_duration_ms=duration,
                error=context.errors[0]["error"] if context.has_errors() else None,
                final_output=self._aggregate_outputs(context),
            )
            
            logger.info(
                "Orchestration completed",
                execution_id=execution_id,
                status=result.status,
                duration_ms=duration,
            )
            
            return result
            
        except Exception as e:
            logger.error("Orchestration failed", execution_id=execution_id, error=str(e))
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                execution_id=execution_id,
                request_id=context.request_id,
                case_id=context.case_id,
                status=AgentExecutionStatus.FAILED,
                plan=plan,
                agent_responses=list(context.agent_outputs.values()),
                execution_trace=context.execution_trace,
                start_time=start_time,
                end_time=end_time,
                total_duration_ms=duration,
                error=str(e),
                final_output={},
            )

    def _build_graph(self, plan: ExecutionPlan, context: ExecutionContext) -> StateGraph:
        """
        Build LangGraph execution graph from plan.
        
        Args:
            plan: Execution plan
            context: Execution context
            
        Returns:
            StateGraph for execution
        """
        # Create state graph
        workflow = StateGraph(dict)
        
        # Add nodes for each agent
        for step in plan.workflow_steps:
            workflow.add_node(
                step.agent_id,
                self._create_agent_node(step, context)
            )
        
        # Add edges based on execution order
        execution_order = plan.decision.execution_order
        
        # Set entry point
        if execution_order:
            workflow.set_entry_point(execution_order[0])
        
        # Connect sequential steps
        for i in range(len(execution_order) - 1):
            workflow.add_edge(execution_order[i], execution_order[i + 1])
        
        # Last step goes to END
        if execution_order:
            workflow.add_edge(execution_order[-1], END)
        
        return workflow.compile()

    def _create_agent_node(self, step: WorkflowStep, context: ExecutionContext):
        """
        Create agent execution node.
        
        Args:
            step: Workflow step
            context: Execution context
            
        Returns:
            Callable agent node function
        """
        async def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute single agent."""
            agent = agent_factory.get_agent(step.agent_id)
            
            if not agent:
                logger.error("Agent not found", agent_id=step.agent_id)
                response = AgentResponse(
                    agent_id=step.agent_id,
                    agent_name=step.agent_name,
                    status=AgentExecutionStatus.FAILED,
                    error="Agent not found",
                )
                context.add_agent_output(step.agent_id, response)
                return state
            
            # Execute with retry
            response = await self._execute_with_retry(agent, context, step)
            
            # Add to context
            context.add_agent_output(step.agent_id, response)
            
            # Add trace
            trace = ExecutionTrace(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_ms=response.duration_ms,
                status=response.status,
                output_summary=str(response.output)[:200] if response.output else None,
                error=response.error,
                retry_count=0,
            )
            context.add_trace(trace)
            
            if response.status == AgentExecutionStatus.FAILED:
                context.add_error(agent.agent_id, response.error or "Unknown error")
                
            return state
        
        return agent_node

    async def _execute_graph(
        self,
        graph: StateGraph,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> None:
        """
        Execute compiled graph.
        
        Args:
            graph: Compiled state graph
            plan: Execution plan
            context: Execution context
        """
        initial_state = {
            "execution_id": str(uuid.uuid4()),
            "plan_id": plan.plan_id,
        }
        
        # Run graph
        async for state in graph.astream(initial_state):
            logger.debug("Graph state updated", state=state)

    async def _execute_with_retry(
        self,
        agent: BaseAgent,
        context: ExecutionContext,
        step: WorkflowStep,
    ) -> AgentResponse:
        """
        Execute agent with retry logic.
        
        Args:
            agent: Agent to execute
            context: Execution context
            step: Workflow step
            
        Returns:
            AgentResponse
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Validate
                if not await agent.validate(context):
                    return AgentResponse(
                        agent_id=agent.agent_id,
                        agent_name=agent.name,
                        status=AgentExecutionStatus.FAILED,
                        error="Validation failed",
                    )
                
                # Execute with per-agent timeout
                try:
                    response = await asyncio.wait_for(
                        agent.execute(context),
                        timeout=self.config.agent_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error("Agent timed out", agent_id=agent.agent_id, timeout=self.config.agent_timeout)
                    return AgentResponse(
                        agent_id=agent.agent_id,
                        agent_name=agent.name,
                        status=AgentExecutionStatus.FAILED,
                        error=f"Agent timed out after {self.config.agent_timeout}s",
                    )
                
                if response.status == AgentExecutionStatus.COMPLETED:
                    return response
                
                last_error = response.error
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Agent execution attempt failed",
                    agent_id=agent.agent_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
        
        # All retries failed
        return AgentResponse(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            status=AgentExecutionStatus.FAILED,
            error=f"Failed after {self.config.max_retries} retries: {last_error}",
        )

    def _aggregate_outputs(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Aggregate all agent outputs.
        
        Args:
            context: Execution context
            
        Returns:
            Aggregated outputs
        """
        outputs = {}
        
        for agent_id, response in context.agent_outputs.items():
            if response.status == AgentExecutionStatus.COMPLETED:
                outputs[agent_id] = response.output
        
        return {
            "agent_outputs": outputs,
            "shared_context": context.shared_context,
            "execution_summary": {
                "total_agents": len(context.agent_outputs),
                "successful": sum(
                    1 for r in context.agent_outputs.values()
                    if r.status == AgentExecutionStatus.COMPLETED
                ),
                "failed": sum(
                    1 for r in context.agent_outputs.values()
                    if r.status == AgentExecutionStatus.FAILED
                ),
            },
        }
