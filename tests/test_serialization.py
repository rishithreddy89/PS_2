"""Tests for JSON serialization of datetime objects."""

import json
from datetime import datetime
from fastapi.encoders import jsonable_encoder

def test_jsonable_encoder_with_datetime():
    """Test that jsonable_encoder correctly handles datetime objects for JSON serialization."""
    
    # Create a mock event with nested datetime objects
    mock_event = {
        "event": "workflow_completed",
        "case_id": "case_123",
        "generated_at": datetime.utcnow(),
        "details": {
            "started_at": datetime.utcnow(),
            "status": "success",
            "nested": [
                {"timestamp": datetime.utcnow()}
            ]
        }
    }
    
    # Attempting to directly json.dumps should fail
    try:
        json.dumps(mock_event)
        assert False, "json.dumps should fail with raw datetime"
    except TypeError:
        pass  # Expected behavior
        
    # Using jsonable_encoder should succeed
    try:
        safe_event = jsonable_encoder(mock_event)
        json_str = json.dumps(safe_event)
        
        # Verify the result
        parsed = json.loads(json_str)
        assert parsed["event"] == "workflow_completed"
        assert isinstance(parsed["generated_at"], str)
        assert isinstance(parsed["details"]["started_at"], str)
        assert isinstance(parsed["details"]["nested"][0]["timestamp"], str)
    except Exception as e:
        assert False, f"Serialization failed: {str(e)}"
