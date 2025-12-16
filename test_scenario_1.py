"""
Manual Test Script - Scenario 3.1: Query with Relevant Context

This script tests the AssistantService RAG pipeline with a query that should
retrieve relevant context from the test notes.

Test Query: "What is grace according to the sermon notes?"

Expected Behavior:
- ✅ Retrieve high-relevance chunks from "Understanding God's Grace" note
- ✅ Build context within 1200-token budget
- ✅ Generate answer citing the note
- ✅ Include source metadata

Usage:
    python test_scenario_1.py
"""

import sys
import asyncio
from pathlib import Path
import json
from datetime import datetime

# Ensure project root is on sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.user_model import User
from app.services.ai.assistant_service import get_assistant_service


async def main():
    """Run Test Scenario 3.1 - Query with Relevant Context"""
    
    print("=" * 80)
    print("TEST SCENARIO 3.1: Query with Relevant Context")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test query about grace - should match "Understanding God's Grace" note
    query = "What is grace according to the sermon notes?"
    
    print(f"📝 Query: {query}")
    print()
    
    async with AsyncSessionLocal() as db:  # type: 
        # Try to find test user (created by create_test_data.py)
        result = await db.execute(
            select(User).where(User.email == "test@scribes.local")
        )
        user = result.scalars().first()
        
        if user is None:
            print("⚠️  Test user 'test@scribes.local' not found. Using user_id=1")
            print("💡 Run 'create_test_data.py' first to create test user and notes")
            user_id = 1
        else:
            user_id = user.id
            print(f"✅ Using test user: {user.username} (id={user_id}, email={user.email})")
        
        print()
        print("-" * 80)
        print("CALLING ASSISTANT SERVICE...")
        print("-" * 80)
        
        # Initialize assistant service
        assistant = get_assistant_service()
        
        # Run query through RAG pipeline
        start_time = datetime.now()
        response = await assistant.query(
            user_query=query,
            user_id=user_id,
            db=db,
            max_sources=5,
            include_metadata=True,
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()
        
        # Print Answer
        print("📖 ANSWER:")
        print("-" * 80)
        print(response.get("answer", "No answer generated"))
        print()
        
        # Print Sources
        sources = response.get("sources", [])
        print(f"📚 SOURCES ({len(sources)} found):")
        print("-" * 80)
        if sources:
            for idx, source in enumerate(sources, 1):
                print(f"\n{idx}. {source.get('title', 'Untitled')}")
                print(f"   Note ID: {source.get('note_id')}")
                print(f"   Relevance Score: {source.get('relevance_score', 0):.4f}")
                preview = source.get('preview', '')
                if preview:
                    print(f"   Preview: {preview[:100]}...")
        else:
            print("   No sources found")
        print()
        
        # Print Metadata
        metadata = response.get("metadata", {})
        print("📊 METADATA:")
        print("-" * 80)
        if metadata:
            print(f"   Query Tokens: {metadata.get('query_tokens', 'N/A')}")
            print(f"   Context Tokens: {metadata.get('context_tokens', 'N/A')}")
            print(f"   Chunks Retrieved: {metadata.get('chunks_used', 0) + metadata.get('chunks_skipped', 0)}")
            print(f"   Chunks Used: {metadata.get('chunks_used', 'N/A')}")
            print(f"   Chunks Skipped: {metadata.get('chunks_skipped', 'N/A')}")
            print(f"   Context Truncated: {metadata.get('truncated', False)}")
            print(f"   Duration: {metadata.get('duration_ms', 0):.0f}ms")
            print(f"   Sources Count: {metadata.get('sources_count', 0)}")
            
            if 'error' in metadata:
                print(f"   ⚠️  Error: {metadata.get('error')}")
                if 'error_message' in metadata:
                    print(f"   Error Message: {metadata.get('error_message')}")
        else:
            print("   No metadata available")
        
        print()
        print("=" * 80)
        print(f"✅ Test completed in {duration:.2f}s")
        print("=" * 80)
        
        # Validation checks
        print()
        print("VALIDATION CHECKS:")
        print("-" * 80)
        
        checks = [
            ("Answer generated", bool(response.get("answer"))),
            ("Sources retrieved", len(sources) > 0),
            ("Metadata present", bool(metadata)),
            ("No errors", 'error' not in metadata if metadata else False),
            ("Context within budget", metadata.get('context_tokens', 0) <= settings.assistant_max_context_tokens if metadata else False),
        ]
        
        for check_name, check_passed in checks:
            status = "✅ PASS" if check_passed else "❌ FAIL"
            print(f"   {status}: {check_name}")
        
        print()
        
        # Print full JSON for debugging (optional)
        print("📋 FULL RESPONSE JSON:")
        print("-" * 80)
        print(json.dumps(response, indent=2, default=str))
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
