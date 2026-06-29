"""
Agent schemas for execution and orchestration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentExecutionStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class AgentResponse(BaseModel):
    """Agent execution response."""
    agent_id: str
    agent_name: str
    status: AgentExecutionStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace(BaseModel):
    """Single agent execution trace."""
    agent_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: AgentExecutionStatus
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class WorkflowStep(BaseModel):
    """Workflow execution step."""
    step_id: str
    agent_id: str
    agent_name: str
    required_capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    priority: int = 0
    can_skip: bool = False


class PlannerDecision(BaseModel):
    """Planner's decision and reasoning."""
    required_capabilities: List[str] = Field(default_factory=list)
    selected_agents: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    reasoning: str
    estimated_complexity: str = "medium"
    estimated_duration_ms: Optional[float] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class ExecutionPlan(BaseModel):
    """Complete execution plan from planner."""
    plan_id: str
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    decision: PlannerDecision
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Final execution result."""
    execution_id: str
    request_id: str
    case_id: Optional[str] = None
    status: AgentExecutionStatus
    plan: Optional[ExecutionPlan] = None
    agent_responses: List[AgentResponse] = Field(default_factory=list)
    execution_trace: List[ExecutionTrace] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    error: Optional[str] = None
    final_output: Dict[str, Any] = Field(default_factory=dict)
