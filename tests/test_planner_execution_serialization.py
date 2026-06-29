"""
Tests for PlannerExecution JSON serialization.

Verifies that:
- make_json_safe converts datetime, nested datetime, UUID, Enum, Decimal,
  nested dicts, and lists to JSON-safe equivalents.
- PlannerExecution can be instantiated with serialized JSON column values
  without raising TypeError.
"""

import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

import pytest

from app.utils.serialization import make_json_safe, serialize_for_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_json_serializable(value, label: str = "value") -> None:
    """Raise AssertionError if *value* is not JSON-serializable."""
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise AssertionError(
            f"{label} is not JSON-serializable: {exc}\nvalue={value!r}"
        ) from exc


# ---------------------------------------------------------------------------
# Unit tests for make_json_safe
# ---------------------------------------------------------------------------

class TestMakeJsonSafe:
    """Unit tests for the make_json_safe utility."""

    def test_datetime_becomes_iso_string(self):
        dt = datetime(2026, 6, 27, 19, 18, 55, 381718)
        result = make_json_safe(dt)
        assert result == "2026-06-27T19:18:55.381718"
        assert_json_serializable(result, "datetime result")

    def test_datetime_with_timezone(self):
        from datetime import timezone
        dt = datetime(2026, 6, 27, 19, 18, 55, 381718, tzinfo=timezone.utc)
        result = make_json_safe(dt)
        assert "+00:00" in result or result.endswith("Z") or "UTC" not in result
        assert_json_serializable(result, "tz-aware datetime result")

    def test_date_becomes_iso_string(self):
        d = date(2026, 6, 27)
        result = make_json_safe(d)
        assert result == "2026-06-27"
        assert_json_serializable(result, "date result")

    def test_uuid_becomes_string(self):
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = make_json_safe(uid)
        assert result == "12345678-1234-5678-1234-567812345678"
        assert isinstance(result, str)
        assert_json_serializable(result, "UUID result")

    def test_enum_becomes_value(self):
        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        result = make_json_safe(Color.RED)
        assert result == "red"
        assert_json_serializable(result, "Enum result")

    def test_decimal_becomes_float(self):
        d = Decimal("3.14159")
        result = make_json_safe(d)
        assert isinstance(result, float)
        assert abs(result - 3.14159) < 1e-5
        assert_json_serializable(result, "Decimal result")

    def test_path_becomes_string(self):
        p = Path("/tmp/some/file.txt")
        result = make_json_safe(p)
        assert isinstance(result, str)
        assert_json_serializable(result, "Path result")

    def test_nested_dict_with_datetime(self):
        payload = {
            "created_at": datetime(2026, 6, 27, 10, 0, 0),
            "nested": {
                "updated_at": datetime(2026, 6, 27, 11, 0, 0),
                "value": 42,
            },
        }
        result = make_json_safe(payload)
        assert result["created_at"] == "2026-06-27T10:00:00"
        assert result["nested"]["updated_at"] == "2026-06-27T11:00:00"
        assert result["nested"]["value"] == 42
        assert_json_serializable(result, "nested dict result")

    def test_list_with_mixed_types(self):
        payload = [
            datetime(2026, 1, 1),
            uuid.uuid4(),
            {"key": Decimal("1.5")},
            "plain string",
            123,
        ]
        result = make_json_safe(payload)
        assert isinstance(result[0], str)  # datetime → str
        assert isinstance(result[1], str)  # UUID → str
        assert isinstance(result[2]["key"], float)  # Decimal → float
        assert result[3] == "plain string"
        assert result[4] == 123
        assert_json_serializable(result, "list result")

    def test_primitives_pass_through(self):
        for value in (None, True, False, 0, 1, 3.14, "hello"):
            result = make_json_safe(value)
            assert result == value
            assert_json_serializable(result, f"primitive {value!r}")

    def test_nested_list_of_dicts(self):
        payload = [
            {"ts": datetime(2026, 6, 1, 0, 0, 0), "id": uuid.uuid4()},
            {"ts": datetime(2026, 6, 2, 0, 0, 0), "id": uuid.uuid4()},
        ]
        result = make_json_safe(payload)
        assert isinstance(result[0]["ts"], str)
        assert isinstance(result[0]["id"], str)
        assert_json_serializable(result, "nested list result")

    def test_serialize_for_db_multiple_fields(self):
        a = {"ts": datetime(2026, 1, 1)}
        b = [uuid.uuid4()]
        c = Decimal("99.9")
        ra, rb, rc = serialize_for_db(a, b, c)
        assert isinstance(ra["ts"], str)
        assert isinstance(rb[0], str)
        assert isinstance(rc, float)


# ---------------------------------------------------------------------------
# Integration-style tests: PlannerExecution column assignment
# ---------------------------------------------------------------------------

class TestPlannerExecutionColumnSafety:
    """
    Verify that PlannerExecution JSON columns can receive serialized payloads.

    These tests do NOT require a live database — they only instantiate the
    model in-memory and confirm that no TypeError is raised during assignment.
    """

    def _build_raw_payloads(self):
        """Return realistic raw payloads that contain non-JSON-safe objects."""
        exec_uuid = uuid.uuid4()
        now = datetime.utcnow()

        class Status(Enum):
            COMPLETED = "completed"

        input_data = {"case_id": str(exec_uuid), "ts": now}
        execution_plan = {
            "plan_id": exec_uuid,
            "workflow_steps": [
                {
                    "step_id": "step_1",
                    "agent_id": "nba_agent",
                    "start_time": now,
                }
            ],
            "decision": {
                "status": Status.COMPLETED,
                "estimated_duration_ms": Decimal("1500.0"),
            },
        }
        agent_outputs = {
            "nba_agent": {
                "duration_ms": Decimal("800.5"),
                "started_at": now,
                "id": exec_uuid,
            }
        }
        final_output = {
            "status": Status.COMPLETED,
            "completed_at": now,
            "result_id": exec_uuid,
        }
        meta_data = {
            "execution_trace": [
                {"agent_id": "nba_agent", "start_time": now, "end_time": now},
            ],
            "workflow_type": "full_analysis",
            "run_id": exec_uuid,
        }
        return input_data, execution_plan, agent_outputs, final_output, meta_data

    def test_serialized_payloads_are_json_safe(self):
        """All serialized JSON column values must be json.dumps-able."""
        raw = self._build_raw_payloads()
        serialized = serialize_for_db(*raw)
        labels = [
            "input_data", "execution_plan", "agent_outputs",
            "final_output", "meta_data",
        ]
        for value, label in zip(serialized, labels):
            assert_json_serializable(value, label)

    def test_planner_execution_instantiation_with_serialized_data(self):
        """PlannerExecution can be created without TypeError using serialized data."""
        from app.models.planner_execution import PlannerExecution

        raw = self._build_raw_payloads()
        input_data, execution_plan, agent_outputs, final_output, meta_data = (
            serialize_for_db(*raw)
        )

        execution_id = str(uuid.uuid4())
        case_id = str(uuid.uuid4())

        # Must not raise TypeError
        execution = PlannerExecution(
            id=execution_id,
            case_id=case_id,
            status="completed",
            execution_type="full_analysis",
            input_data=input_data,
            execution_plan=execution_plan,
            agent_outputs=agent_outputs,
            final_output=final_output,
            duration_ms=1500,
            error_message=None,
            meta_data=meta_data,
        )

        assert execution.id == execution_id
        assert execution.status == "completed"
        assert_json_serializable(execution.input_data, "input_data")
        assert_json_serializable(execution.execution_plan, "execution_plan")
        assert_json_serializable(execution.agent_outputs, "agent_outputs")
        assert_json_serializable(execution.final_output, "final_output")
        assert_json_serializable(execution.meta_data, "meta_data")

    def test_datetime_in_execution_trace_is_serializable(self):
        """Execution trace containing datetime objects is safely serialized."""
        trace = [
            {
                "agent_id": "nba_agent",
                "agent_name": "Next Best Action Agent",
                "start_time": datetime.utcnow(),
                "end_time": datetime.utcnow(),
                "duration_ms": 800.0,
                "status": "completed",
            }
        ]
        meta_data = make_json_safe({
            "execution_trace": trace,
            "workflow_type": "full_analysis",
        })
        assert_json_serializable(meta_data, "meta_data with execution_trace")
        assert isinstance(meta_data["execution_trace"][0]["start_time"], str)

    def test_uuid_in_execution_plan_is_serializable(self):
        """Execution plan containing UUID objects is safely serialized."""
        plan = {
            "plan_id": uuid.uuid4(),
            "workflow_steps": [{"step_id": uuid.uuid4(), "agent_id": "nba_agent"}],
        }
        result = make_json_safe(plan)
        assert_json_serializable(result, "execution_plan with UUID")
        assert isinstance(result["plan_id"], str)
        assert isinstance(result["workflow_steps"][0]["step_id"], str)

    def test_enum_in_agent_outputs_is_serializable(self):
        """Agent outputs containing Enum values are safely serialized."""
        class AgentStatus(Enum):
            COMPLETED = "completed"
            FAILED = "failed"

        agent_outputs = {
            "nba_agent": {
                "status": AgentStatus.COMPLETED,
                "score": Decimal("0.95"),
            }
        }
        result = make_json_safe(agent_outputs)
        assert_json_serializable(result, "agent_outputs with Enum")
        assert result["nba_agent"]["status"] == "completed"
        assert isinstance(result["nba_agent"]["score"], float)
