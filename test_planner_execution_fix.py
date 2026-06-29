#!/usr/bin/env python3
"""
Test PlannerExecution database persistence.

Verifies that PlannerExecution can be created with correct field names.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_planner_execution_persistence():
    """Test PlannerExecution can be created and saved."""
    print("\n" + "=" * 60)
    print("TESTING PLANNEREXECUTION PERSISTENCE")
    print("=" * 60 + "\n")
    
    try:
        from app.database.session import AsyncSessionLocal
        from app.models.planner_execution import PlannerExecution
        from uuid import uuid4
        
        print("✓ Imports successful")
        
        async with AsyncSessionLocal() as db:
            # Create test execution with correct field names
            execution_id = str(uuid4())
            case_id = str(uuid4())
            
            execution = PlannerExecution(
                id=execution_id,
                case_id=case_id,
                status="completed",
                execution_type="full_analysis",
                input_data={"case_id": case_id},
                execution_plan={
                    "workflow_steps": [
                        {"agent_name": "retrieval_agent"},
                        {"agent_name": "nba_agent"}
                    ]
                },
                agent_outputs={
                    "retrieval_agent": {"status": "completed"},
                    "nba_agent": {"recommendations": []}
                },
                final_output={"status": "success"},
                duration_ms=1500,
                error_message=None,
                meta_data={
                    "execution_trace": [
                        {"agent_name": "retrieval_agent", "duration_ms": 800},
                        {"agent_name": "nba_agent", "duration_ms": 700}
                    ],
                    "workflow_type": "full_analysis"
                }
            )
            
            print("✓ PlannerExecution object created")
            print(f"  ID: {execution_id}")
            print(f"  Status: {execution.status}")
            print(f"  Type: {execution.execution_type}")
            
            # Add to session
            db.add(execution)
            await db.flush()
            
            print("✓ PlannerExecution added to session")
            
            # Commit to database
            await db.commit()
            
            print("✓ PlannerExecution saved to database")
            
            # Retrieve and verify
            from sqlalchemy import select
            result = await db.execute(
                select(PlannerExecution).where(PlannerExecution.id == execution_id)
            )
            saved_execution = result.scalar_one_or_none()
            
            if saved_execution:
                print("✓ PlannerExecution retrieved from database")
                print(f"  Status: {saved_execution.status}")
                print(f"  Duration: {saved_execution.duration_ms}ms")
                print(f"  Agent outputs: {len(saved_execution.agent_outputs or {})} agents")
                print(f"  Execution plan: {len(saved_execution.execution_plan.get('workflow_steps', []))} steps")
                
                # Check meta_data
                if saved_execution.meta_data:
                    trace_count = len(saved_execution.meta_data.get("execution_trace", []))
                    print(f"  Execution trace: {trace_count} entries")
            else:
                print("✗ Could not retrieve execution")
                return False
            
            # Cleanup
            await db.rollback()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("\n✓ No 'plan_data is an invalid keyword argument' error")
        print("✓ All field names match model definition")
        print("✓ PlannerExecution persisted successfully")
        print("✓ Database operations work correctly")
        print("\nPlannerExecution persistence fix is complete!\n")
        
        return True
        
    except TypeError as e:
        if "invalid keyword argument" in str(e):
            print(f"\n✗ Field mismatch error: {e}")
            print("\nCheck that all field names match the model definition.")
        else:
            print(f"\n✗ TypeError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests."""
    success = await test_planner_execution_persistence()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
