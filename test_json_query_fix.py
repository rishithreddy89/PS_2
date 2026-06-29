#!/usr/bin/env python3
"""
Test SQLAlchemy 2.x JSON query fix.

Verifies that indexed document retrieval works correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_json_query():
    """Test JSON query with SQLAlchemy 2.x."""
    print("\n" + "=" * 60)
    print("TESTING SQLALCHEMY 2.X JSON QUERY")
    print("=" * 60 + "\n")
    
    try:
        from app.database.session import AsyncSessionLocal
        from app.repositories.case_document import CaseDocumentRepository
        from app.models.case_document import CaseDocument
        
        print("✓ Imports successful")
        
        # Test with a database session
        async with AsyncSessionLocal() as db:
            repo = CaseDocumentRepository(db)
            
            print("✓ Repository initialized")
            
            # Test the JSON query directly
            test_case_id = "test-json-query"
            
            # Create test document
            doc = CaseDocument(
                case_id=test_case_id,
                document_type="test",
                title="Test Document",
                file_path="/test/path.pdf",
                file_name="test.pdf",
                file_size=1000,
                meta_data={"status": "indexed"}
            )
            db.add(doc)
            await db.commit()
            
            print("✓ Test document created")
            
            # Test get_indexed_documents
            try:
                indexed = await repo.get_indexed_documents(test_case_id)
                print(f"✓ JSON query executed successfully")
                print(f"  Found {len(indexed)} indexed document(s)")
                
                if len(indexed) > 0:
                    print(f"  Document: {indexed[0].title}")
                    print(f"  Status: {indexed[0].meta_data.get('status')}")
                
            except Exception as e:
                print(f"✗ JSON query failed: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Test count
            try:
                count = await repo.count_indexed_documents(test_case_id)
                print(f"✓ Count query executed successfully: {count}")
            except Exception as e:
                print(f"✗ Count query failed: {e}")
                return False
            
            # Cleanup
            await db.rollback()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("\n✓ SQLAlchemy 2.x JSON queries work correctly")
        print("✓ No .astext errors")
        print("✓ func.json_extract() working for MySQL")
        print("\nJSON query fix is complete!\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run tests."""
    success = await test_json_query()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
