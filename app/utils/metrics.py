"""
Metrics and observability for workflow execution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import defaultdict
import time

from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Collects and aggregates system metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
    
    def record_execution_time(self, operation: str, duration_ms: float):
        """Record execution time for an operation."""
        self.metrics[f"{operation}_duration"].append(duration_ms)
        logger.debug("Execution time recorded", operation=operation, duration_ms=duration_ms)
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric."""
        self.counters[name] += value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        self.gauges[name] = value
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        values = self.metrics.get(metric_name, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)] if count > 1 else sorted_values[0],
            "p99": sorted_values[int(count * 0.99)] if count > 1 else sorted_values[0],
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        stats = {}
        
        for metric_name in self.metrics:
            stats[metric_name] = self.get_stats(metric_name)
        
        return {
            "metrics": stats,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
        }
    
    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()


class WorkflowMetrics:
    """Specific metrics for workflow execution."""
    
    def __init__(self):
        self.executions = []
        self.agent_metrics = defaultdict(list)
    
    def record_workflow_execution(
        self,
        execution_id: str,
        case_id: str,
        status: str,
        duration_ms: float,
        agent_count: int,
    ):
        """Record workflow execution metrics."""
        self.executions.append({
            "execution_id": execution_id,
            "case_id": case_id,
            "status": status,
            "duration_ms": duration_ms,
            "agent_count": agent_count,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def record_agent_execution(
        self,
        agent_id: str,
        status: str,
        duration_ms: float,
    ):
        """Record agent execution metrics."""
        self.agent_metrics[agent_id].append({
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        if not self.executions:
            return {}
        
        total = len(self.executions)
        completed = sum(1 for e in self.executions if e["status"] == "completed")
        failed = sum(1 for e in self.executions if e["status"] == "failed")
        
        durations = [e["duration_ms"] for e in self.executions]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "avg_duration_ms": avg_duration,
        }
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        stats = {}
        
        for agent_id, executions in self.agent_metrics.items():
            total = len(executions)
            completed = sum(1 for e in executions if e["status"] == "completed")
            durations = [e["duration_ms"] for e in executions]
            
            stats[agent_id] = {
                "total_executions": total,
                "completed": completed,
                "success_rate": completed / total if total > 0 else 0,
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            }
        
        return stats


class PerformanceTracker:
    """Track performance of operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start tracking."""
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking and log."""
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        logger.info(
            "Operation completed",
            operation=self.operation_name,
            duration_ms=duration_ms,
            error=exc_type is not None,
        )
        
        metrics_collector.record_execution_time(self.operation_name, duration_ms)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        logger.info(
            "Async operation completed",
            operation=self.operation_name,
            duration_ms=duration_ms,
            error=exc_type is not None,
        )
        
        metrics_collector.record_execution_time(self.operation_name, duration_ms)


# Global instances
metrics_collector = MetricsCollector()
workflow_metrics = WorkflowMetrics()
