"""
Test Scenario 3.2: Query with No Relevant Context
===================================================

This test validates the system's behavior when a user asks about something
completely unrelated to their sermon notes. The system should:
1. Detect low relevance scores (no good matches)
2. Skip LLM generation to save API costs
3. Return a helpful "no context" message
4. Set metadata flags appropriately

Expected: No-context response WITHOUT calling the LLM API
"""

import sys
import asyncio
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.ai.assistant_service import get_assistant_service


async def test_query_no_context():
    """Test query with no relevant context in sermon notes."""
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    assistant = get_assistant_service()
    
    # Query about quantum physics - completely unrelated to theology/sermon notes
    query = "How does quantum entanglement work and what are its applications in quantum computing?"
    user_id = 7  # Replace with your test user ID
    
    print("="*80)
    print("TEST SCENARIO 3.2: Query with No Relevant Context")
    print("="*80)
    print(f"\nQuery: {query}")
    print(f"User ID: {user_id}")
    print("\nExpected Behavior:")
    print("  - Low relevance scores (no theological content match)")
    print("  - Skip LLM generation (save API costs)")
    print("  - Return 'no context' message")
    print("  - Metadata: no_context=true, chunks_used=0")
    print("\n" + "="*80)
    
    async with async_session() as db:
        import time
        start_time = time.time()
        
        response = await assistant.query(
            user_query=query,
            user_id=user_id,
            db=db,
            max_sources=5,
            include_metadata=True
        )
        
        duration = time.time() - start_time
    
    # Display results
    print(f"\n📝 ANSWER:")
    print("-" * 80)
    print(response["answer"])
    print("-" * 80)
    
    print(f"\n📚 SOURCES: {len(response['sources'])}")
    if response['sources']:
        for i, source in enumerate(response["sources"], 1):
            print(f"\n{i}. {source['note_title']}")
            print(f"   Preacher: {source['preacher']}")
    else:
        print("   (None - as expected)")
    
    print(f"\n📊 METADATA:")
    print("-" * 80)
    if response["metadata"]:
        for key, value in response["metadata"].items():
            print(f"   {key}: {value}")
    print("-" * 80)
    
    print(f"\n⏱️  DURATION: {duration:.2f}s")
    
    # Validation checks
    print("\n" + "="*80)
    print("VALIDATION CHECKS:")
    print("="*80)
    
    passed = 0
    total = 5
    
    # Check 1: Answer exists
    if response["answer"]:
        print("   ✅ PASS: Answer generated (helpful 'no context' message)")
        passed += 1
    else:
        print("   ❌ FAIL: No answer returned!")
    
    # Check 2: No sources
    if len(response["sources"]) == 0:
        print("   ✅ PASS: No sources returned (as expected)")
        passed += 1
    else:
        print(f"   ❌ FAIL: Should have 0 sources, got {len(response['sources'])}")
    
    # Check 3: no_context flag
    if response["metadata"] and response["metadata"].get("no_context") is True:
        print("   ✅ PASS: Metadata has no_context=True")
        passed += 1
    else:
        print("   ❌ FAIL: no_context flag missing or false!")
    
    # Check 4: No chunks used
    if response["metadata"] and response["metadata"].get("chunks_used") == 0:
        print("   ✅ PASS: chunks_used=0 (LLM not called)")
        passed += 1
    else:
        chunks_used = response["metadata"].get("chunks_used", "?")
        print(f"   ❌ FAIL: Should use 0 chunks, got {chunks_used}")
    
    # Check 5: Fast response (no LLM call should be < 2 seconds)
    if duration < 2.0:
        print(f"   ✅ PASS: Fast response ({duration:.2f}s - no LLM API call)")
        passed += 1
    else:
        print(f"   ⚠️  WARN: Slow response ({duration:.2f}s - may have called LLM unnecessarily)")
    
    print("="*80)
    print(f"RESULT: {passed}/{total} checks passed")
    print("="*80)
    
    if passed == total:
        print("\n✅ TEST PASSED: No-context handling working correctly!")
        print("   - Detected irrelevant query")
        print("   - Skipped expensive LLM call")
        print("   - Returned helpful message")
        print("   - Set appropriate metadata")
    else:
        print(f"\n⚠️  TEST INCOMPLETE: {total - passed} check(s) failed")
        print("   Review the failures above and check:")
        print("   - RetrievalService relevance threshold")
        print("   - AssistantService no-context logic")
        print("   - Metadata flag setting")
    
    # Additional context check
    print("\n" + "="*80)
    print("ADDITIONAL CHECKS:")
    print("="*80)
    
    # Verify the answer is helpful (not just empty)
    answer_lower = response["answer"].lower()
    helpful_indicators = ["don't see", "not in", "notes", "sermon", "help", "add", "specific"]
    is_helpful = any(indicator in answer_lower for indicator in helpful_indicators)
    
    if is_helpful:
        print("   ✅ Answer is helpful and constructive")
    else:
        print("   ⚠️  Answer may not be user-friendly")
    
    # Verify it doesn't try to answer the quantum physics question
    quantum_terms = ["entanglement", "quantum", "superposition", "qubit"]
    tries_to_answer = any(term in answer_lower for term in quantum_terms)
    
    if not tries_to_answer:
        print("   ✅ Doesn't hallucinate answer to unrelated topic")
    else:
        print("   ⚠️  WARNING: May be attempting to answer unrelated topic!")
    
    # Check for theological grounding
    theological_terms = ["god", "bible", "scripture", "faith", "sermon"]
    stays_theological = any(term in answer_lower for term in theological_terms)
    
    if stays_theological:
        print("   ✅ Stays grounded in theological/pastoral context")
    else:
        print("   ⚠️  Answer may have drifted from pastoral context")
    
    print("="*80)
    
    return response


if __name__ == "__main__":
    print("\n" + "🔬 " * 20)
    print("AssistantService Test Suite - Scenario 3.2")
    print("🔬 " * 20 + "\n")
    
    asyncio.run(test_query_no_context())
    
    print("\n" + "="*80)
    print("Test complete! Review results above.")
    print("="*80 + "\n")
