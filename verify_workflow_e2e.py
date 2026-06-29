import asyncio
import sys
import uuid
import os

# Ensure the app directory is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verify_e2e():
    print("Initializing components...")
    from app.database.session import AsyncSessionLocal
    from app.agents.init import initialize_agents
    
    # Initialize agent registry
    initialize_agents()
    from app.models.case import Case
    from app.models.case_document import CaseDocument
    from app.knowledge.ingestion import get_ingestion_service
    from app.services.workflow import WorkflowExecutionService
    
    case_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    
    print(f"Creating case {case_id}...")
    async with AsyncSessionLocal() as db:
        case = Case(
            id=case_id,
            case_number=f"TEST-{case_id[:8]}",
            client_name="Test Client",
            title="E2E Retrieval Fix Test",
            description="Testing if the workflow explicitly runs retrieval before RecommendationAgent.",
            case_type="test",
            status="open"
        )
        db.add(case)
        
        doc_path = f"/tmp/{doc_id}.txt"
        with open(doc_path, "w") as f:
            f.write("This is a mock document for testing retrieval. It contains evidence about a contract dispute over $50,000 where the defendant failed to deliver goods on time.")
            
        doc = CaseDocument(
            id=doc_id,
            case_id=case_id,
            title="Mock Evidence",
            file_name="test_evidence.txt",
            file_path=doc_path,
            document_type="evidence"
        )
        db.add(doc)
        await db.commit()
        print("DB commit successful.")
        
        print("Ingesting document...")
        ingestion_service = get_ingestion_service()
        await ingestion_service.ingest_file(
            file_path=doc_path,
            case_id=case_id,
            metadata={"case_id": case_id, "document_type": "evidence"}
        )
        print("Ingestion successful.")
        
        print("Running WorkflowExecutionService...")
        workflow = WorkflowExecutionService(db)
        
        docs = [{
            "id": doc_id,
            "filename": "test_evidence.txt",
            "content": "This is a mock document for testing retrieval. It contains evidence about a contract dispute over $50,000 where the defendant failed to deliver goods on time.",
            "document_type": "evidence"
        }]
        
        has_retrieval_started = False
        has_retrieval_completed = False
        has_orchestration_started = False
        retrieved_chunks = 0
        
        async for update in workflow.execute_case_workflow(case_id=case_id, documents=docs):
            event = update.get("event")
            print(f"Workflow Event: {event}")
            if event == "retrieval_started":
                has_retrieval_started = True
            elif event == "retrieval_completed":
                has_retrieval_completed = True
                retrieved_chunks = update.get("retrieved_chunks", 0)
            elif event == "orchestration_started":
                has_orchestration_started = True
                
        print(f"\n--- VERIFICATION RESULTS ---")
        print(f"Retrieval Started Event Emitted: {has_retrieval_started}")
        print(f"Retrieval Completed Event Emitted: {has_retrieval_completed}")
        print(f"Retrieved Chunks: {retrieved_chunks}")
        
        if has_retrieval_started and has_retrieval_completed and retrieved_chunks > 0:
            print("SUCCESS! Retrieval step explicitly runs and retrieves chunks.")
        else:
            print("FAILED! Retrieval step didn't run correctly or retrieved zero chunks.")

if __name__ == "__main__":
    asyncio.run(verify_e2e())
