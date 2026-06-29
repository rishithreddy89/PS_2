"""
Centralized JSON serialization utility.

Converts non-JSON-serializable Python objects to JSON-safe equivalents
before they are written to SQLAlchemy JSON columns.

Supports:
- datetime / date  → ISO 8601 string
- UUID             → str
- Enum             → .value
- Decimal          → float
- Path             → str
- Pydantic models  → dict (then recursed)
- dict / list      → recursed
- All other types  → left unchanged (must already be JSON-safe)
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


def make_json_safe(value: Any) -> Any:
    """
    Recursively convert *value* into a fully JSON-serializable structure.

    Args:
        value: Any Python object.

    Returns:
        A JSON-serializable equivalent of *value*.
    """
    # datetime must come before date because datetime is a subclass of date.
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, Path):
        return str(value)

    # Pydantic v1 (has .dict()) and v2 (has .model_dump())
    if hasattr(value, "model_dump"):
        return make_json_safe(value.model_dump())

    if hasattr(value, "dict") and callable(value.dict):
        try:
            return make_json_safe(value.dict())
        except Exception:
            pass

    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set, frozenset)):
        return [make_json_safe(item) for item in value]

    # Primitives (str, int, float, bool, None) are already JSON-safe.
    return value


def serialize_for_db(*fields: Any) -> tuple:
    """
    Convenience helper: serialize multiple top-level JSON field values at once.

    Usage::

        input_data, execution_plan, agent_outputs, final_output, meta_data = (
            serialize_for_db(
                raw_input_data,
                raw_execution_plan,
                raw_agent_outputs,
                raw_final_output,
                raw_meta_data,
            )
        )

    Args:
        *fields: Any number of values to serialize.

    Returns:
        A tuple of JSON-safe equivalents in the same order.
    """
    return tuple(make_json_safe(f) for f in fields)
