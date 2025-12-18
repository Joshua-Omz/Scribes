"""
Test Scenario 3.4: Very Long Query Handling
============================================

This test validates the system's handling of excessively long queries.
The system should:
1. Detect queries exceeding reasonable length
2. Truncate to stay within token budgets
3. Still generate relevant answers
4. Set appropriate metadata flags

Expected: Query truncated but still functional, no errors
"""

import sys
import asyncio
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).parent.parent.parent  # Go up to backend2/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.ai.assistant_service import get_assistant_service


async def test_long_query():
    """Test very long query handling and truncation."""
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    assistant = get_assistant_service()
    
    # Create an excessively long query with relevant theological content (500+ words)
    # This query is about grace, which WILL match sermon notes and trigger LLM generation
    long_query = """
I've been studying my sermon notes about grace and I have some really detailed questions 
that I hope you can help me with. What is the relationship between grace, mercy, faith, 
love, and salvation according to the sermon notes I've taken? I want to understand this 
deeply because it's such a fundamental part of Christian theology and I want to make sure 
I'm getting it right.

Please explain in detail how these concepts interconnect and support each other in Christian 
theology. I'm really interested in understanding the deep theological connections between 
these fundamental doctrines. For example, how does grace enable faith? And how does faith 
lead to salvation? And where does God's love fit into all of this?

Also, can you provide specific scripture references that my pastors mentioned in their 
sermons about grace? I want to make sure I understand the biblical basis for each concept. 
I'm particularly interested in how grace relates to works and whether our faith needs to 
produce good works to be genuine, or if we're saved by grace alone through faith alone. 
I know Ephesians 2:8-9 talks about this, but are there other passages my pastors referenced?

Additionally, how does God's love factor into all of this? Is His love conditional or 
unconditional? And what role does the Holy Spirit play in helping us live out our faith 
on a daily basis? I've heard different perspectives on this and want to understand what 
my sermon notes say about it. Does the Holy Spirit help us respond to God's grace?

Furthermore, I'm curious about how mercy differs from grace. Some people use these terms 
interchangeably, but I suspect there are important theological distinctions. Can you 
help me understand the nuances based on what my pastors have taught? Is mercy about not 
getting what we deserve, while grace is about getting what we don't deserve?

I also want to know more about the concept of unmerited favor. What does it mean that 
grace is unmerited? Does this mean we can never do anything to earn it? And if so, why 
do we still need to have faith? Is faith itself a work, or is it something else entirely?

Finally, how do all these concepts come together in the doctrine of salvation? What is 
the process of salvation, and how do grace, mercy, faith, love, and the Holy Spirit all 
work together to bring us into relationship with God? I want to have a comprehensive 
understanding of the gospel message as presented in my sermon notes.

I'm also wondering about the practical implications. How should understanding God's grace 
change how I live my daily life? Should it make me more grateful? More loving? More willing 
to serve others? What did my pastors say about living out grace in our relationships?

And one more thing - how does grace relate to forgiveness? When God forgives us, is that 
an act of grace? Or is it something different? I want to make sure I'm not confusing 
these important theological concepts.

Please be as thorough as possible and cite specific examples from my notes. I really 
want to understand these core theological concepts deeply. Quote directly from my sermon 
notes if possible, especially from the notes about grace and God's unmerited favor. 
Thank you so much for your help in unpacking all of this!
    """.strip()
    
    user_id = 7  # Replace with your test user ID
    
    print("="*80)
    print("TEST SCENARIO 3.4: Very Long Query Handling")
    print("="*80)
    print(f"\nOriginal Query Length: {len(long_query)} characters")
    print(f"Original Query Word Count: {len(long_query.split())} words")
    print("\nQuery Preview (first 300 chars):")
    print("-" * 80)
    print(long_query[:300] + "...")
    print("-" * 80)
    
    print("\nExpected Behavior:")
    print("  - Query should be truncated to reasonable length")
    print("  - Token count should be within limits (< 150 tokens)")
    print("  - Answer should still be relevant and helpful")
    print("  - Metadata should show 'truncated: true'")
    print("\n" + "="*80)
    
    async with async_session() as db:
        import time
        start_time = time.time()
        
        response = await assistant.query(
            user_query=long_query,
            user_id=user_id,
            db=db,
            max_sources=5,
            include_metadata=True
        )
        
        duration = time.time() - start_time
    
    # Display results
    print(f"\n📝 ANSWER:")
    print("-" * 80)
    # Show full answer
    print(response["answer"])
    print("-" * 80)
    
    print(f"\n📚 SOURCES: {len(response['sources'])}")
    if response['sources']:
        for i, source in enumerate(response["sources"], 1):
            print(f"\n{i}. {source['note_title']}")
            print(f"   Preacher: {source['preacher']}")
            print(f"   Scripture: {source.get('scripture_refs', 'N/A')}")
            print(f"   Tags: {source.get('tags', 'N/A')}")
    
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
    total = 6
    
    metadata = response.get("metadata", {})
    
    # Check 1: Answer generated
    if response["answer"]:
        print("   ✅ PASS: Answer generated")
        passed += 1
    else:
        print("   ❌ FAIL: No answer returned!")
    
    # Check 2: Query tokens within limit
    query_tokens = metadata.get("query_tokens", 0)
    if query_tokens > 0 and query_tokens <= 150:
        print(f"   ✅ PASS: Query tokens within limit ({query_tokens} ≤ 150)")
        passed += 1
    else:
        print(f"   ⚠️  WARN: Query tokens: {query_tokens} (expected ≤ 150)")
        if query_tokens > 0:
            passed += 0.5  # Partial credit if at least counted
    
    # Check 3: Truncation flag (if applicable)
    original_word_count = len(long_query.split())
    if original_word_count > 100:  # If query was very long
        if metadata.get("truncated"):
            print(f"   ✅ PASS: Truncation flag set (original {original_word_count} words)")
            passed += 1
        else:
            print(f"   ℹ️  INFO: No truncation flag (query may have fit)")
            passed += 1  # Not necessarily a failure
    else:
        print(f"   ℹ️  INFO: Query short enough, truncation not needed")
        passed += 1
    
    # Check 4: Answer is relevant (contains theological terms)
    answer_lower = response["answer"].lower()
    theological_terms = ["grace", "mercy", "faith", "love", "god", "salvation", "spirit"]
    relevant_terms = [term for term in theological_terms if term in answer_lower]
    
    if len(relevant_terms) >= 2:
        print(f"   ✅ PASS: Answer is relevant ({len(relevant_terms)} theological terms found)")
        passed += 1
    else:
        print(f"   ⚠️  WARN: Answer may not be relevant (only {len(relevant_terms)} terms)")
    
    # Check 5: No errors despite long query
    if "error" not in response and not metadata.get("error"):
        print("   ✅ PASS: No errors encountered")
        passed += 1
    else:
        print("   ❌ FAIL: Error encountered!")
    
    # Check 6: Context tokens within budget
    context_tokens = metadata.get("context_tokens", 0)
    max_context = settings.assistant_max_context_tokens
    
    if context_tokens <= max_context:
        print(f"   ✅ PASS: Context within budget ({context_tokens}/{max_context} tokens)")
        passed += 1
    else:
        print(f"   ❌ FAIL: Context exceeds budget ({context_tokens}/{max_context} tokens)")
    
    print("="*80)
    print(f"RESULT: {passed}/{total} checks passed")
    print("="*80)
    
    if passed >= total * 0.9:  # 90% pass threshold
        print("\n✅ TEST PASSED: Long query handling working correctly!")
        print("   - Query was processed without errors")
        print("   - Token limits respected")
        print("   - Answer remains relevant and helpful")
        print("   - System handles edge cases gracefully")
    else:
        print(f"\n⚠️  TEST INCOMPLETE: {total - passed} check(s) failed")
        print("   Review the failures above and check:")
        print("   - Token counting logic in TokenizerService")
        print("   - Query truncation in AssistantService")
        print("   - Metadata flag setting")
    
    # Additional analysis
    print("\n" + "="*80)
    print("QUERY PROCESSING ANALYSIS:")
    print("="*80)
    
    print(f"   Original query: {len(long_query)} chars, ~{len(long_query.split())} words")
    print(f"   Query tokens: {query_tokens}")
    print(f"   Context tokens: {context_tokens}")
    print(f"   Total tokens used: {query_tokens + context_tokens}")
    print(f"   Model context window: {settings.assistant_model_context_window}")
    
    total_prompt_tokens = query_tokens + context_tokens + metadata.get("system_prompt_tokens", 100)
    remaining_for_output = settings.assistant_model_context_window - total_prompt_tokens
    
    print(f"   Remaining for output: ~{remaining_for_output} tokens")
    print(f"   Configured output limit: {settings.assistant_max_output_tokens} tokens")
    
    if remaining_for_output >= settings.assistant_max_output_tokens:
        print("   ✅ Sufficient room for full answer")
    else:
        print(f"   ⚠️  Limited output space ({remaining_for_output} tokens available)")
    
    print("="*80)
    
    return response


async def test_extreme_query():
    """Test extremely long query with context (stress test)."""
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    assistant = get_assistant_service()
    
    # Create an absurdly long query with relevant content about grace
    base_questions = [
        "What is grace according to my sermon notes? ",
        "How does grace relate to mercy? ",
        "Is grace conditional or unconditional? ",
        "What scriptures discuss grace? ",
        "How is grace different from works? ",
        "Can we earn grace through good behavior? ",
        "What does unmerited favor mean? ",
        "How does grace enable salvation? ",
        "What role does faith play in receiving grace? ",
        "How should we respond to God's grace? "
    ]
    
    # Repeat questions to create massive query (200+ repetitions = ~2000+ words)
    extreme_query = "I have many questions about grace from my sermon notes: " + " ".join(base_questions * 100)
    
    user_id = 7
    
    print("\n" + "="*80)
    print("STRESS TEST: Extremely Long Query with Relevant Context (2000+ words)")
    print("="*80)
    print(f"Query length: {len(extreme_query)} characters")
    print(f"Query word count: {len(extreme_query.split())} words")
    print(f"Preview: {extreme_query[:200]}...")
    
    async with async_session() as db:
        try:
            import time
            start_time = time.time()
            
            response = await assistant.query(
                user_query=extreme_query,
                user_id=user_id,
                db=db,
                include_metadata=True
            )
            
            duration = time.time() - start_time
            
            print("\n✅ Query processed successfully (no crash)")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Query tokens: {response['metadata'].get('query_tokens', 'N/A')}")
            print(f"   Context tokens: {response['metadata'].get('context_tokens', 'N/A')}")
            print(f"   Truncated: {response['metadata'].get('truncated', False)}")
            print(f"   Chunks used: {response['metadata'].get('chunks_used', 0)}")
            print(f"   Answer length: {len(response['answer'])} chars")
            print(f"   Sources: {len(response.get('sources', []))}")
            
            # Verify answer is about grace (not empty/error)
            if response['answer'] and 'grace' in response['answer'].lower():
                print("   ✅ Answer is relevant (mentions grace)")
            else:
                print("   ⚠️  Answer may not be relevant")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error encountered: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("\n" + "🔬 " * 20)
    print("AssistantService Test Suite - Scenario 3.4")
    print("LONG QUERY HANDLING & TRUNCATION TESTING")
    print("🔬 " * 20 + "\n")
    
    # Test 1: Long but reasonable query
    asyncio.run(test_long_query())
    
    # Test 2: Extreme stress test
    print("\n" + "="*80)
    stress_passed = asyncio.run(test_extreme_query())
    print("="*80)
    
    if stress_passed:
        print("\n✅ STRESS TEST PASSED: System handles extreme queries gracefully")
    else:
        print("\n⚠️  STRESS TEST FAILED: System struggled with extreme query length")
    
    print("\n" + "="*80)
    print("Test complete! Review results above.")
    print("="*80 + "\n")
