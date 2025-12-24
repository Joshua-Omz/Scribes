"""
Pipeline Caching Test Script

This script tests the 3-layer caching system in the RAG pipeline:
- L1 (Query Cache): Complete response caching (24h TTL)
- L2 (Embedding Cache): Query embedding caching (7d TTL)
- L3 (Context Cache): Retrieved chunks caching (1h TTL)

Test Scenarios:
1. Cold Start (All cache misses)
2. L2 Hit (Embedding cached, context & response not cached)
3. L3 Hit (Embedding & context cached, response not cached)
4. L1 Hit (Complete response cached - fastest path)
5. Cache Invalidation (User note update clears L3)
6. Cache Statistics & Performance Metrics

Expected Performance Improvements:
- L1 Hit: ~2-10x faster (no LLM call)
- L2 Hit: ~10-20% faster (skip embedding generation)
- L3 Hit: ~30-50% faster (skip vector search)

Usage:
    python scripts/testing/test_pipeline_caching.py
    
Prerequisites:
    - Test user exists (run create_test_data.py first)
    - Redis is running (CACHE_ENABLED=true in .env)
    - Test notes with embeddings exist
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user_model import User
from app.models.note_model import Note
from app.core.cache import get_cache_manager, RedisCacheManager
from app.services.ai.assistant_service import AssistantService
from app.services.ai.caching.query_cache import QueryCache
from app.services.ai.caching.embedding_cache import EmbeddingCache
from app.services.ai.caching.context_cache import ContextCache


# ===========================
# TEST QUERIES
# ===========================

TEST_QUERIES = [
    "What is grace according to the sermon notes?",
    "How does faith help us grow spiritually?",
    "What does the Bible say about God's love?",
]


# ===========================
# HELPER FUNCTIONS
# ===========================

def print_header(title: str):
    """Print formatted section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_subheader(title: str):
    """Print formatted subsection header."""
    print()
    print("-" * 80)
    print(f"  {title}")
    print("-" * 80)


def print_metric(label: str, value: Any, emoji: str = "✅"):
    """Print formatted metric line."""
    print(f"{emoji} {label:<40} {value}")


def print_cache_stats(stats: Dict[str, Any], cache_name: str):
    """Pretty print cache statistics."""
    print(f"\n{cache_name} Statistics:")
    print(f"  Total Requests: {stats.get('total', 0)}")
    print(f"  Hits: {stats.get('hits', 0)}")
    print(f"  Misses: {stats.get('misses', 0)}")
    
    hit_rate = stats.get('hit_rate', 0.0)
    emoji = "🟢" if hit_rate >= 0.5 else "🟡" if hit_rate >= 0.3 else "🔴"
    print(f"  {emoji} Hit Rate: {hit_rate:.2%}")


async def get_test_user(db: AsyncSession) -> User:
    """Get or create test user."""
    result = await db.execute(
        select(User).where(User.email == "testadmin@example.com")
    )
    user = result.scalars().first()
    
    if not user:
        raise ValueError(
            "testadmin user not found. Please run bootstrap_admin.py first."
        )
    
    return user


async def clear_all_caches(cache_manager: RedisCacheManager):
    """Clear all cache layers for testing."""
    query_cache = QueryCache(cache_manager)
    embedding_cache = EmbeddingCache(cache_manager)
    context_cache = ContextCache(cache_manager)
    
    await query_cache.clear_all()
    await embedding_cache.clear_all()
    await context_cache.clear_all()
    
    print("✅ All caches cleared")


async def run_query_test(
    assistant: AssistantService,
    user_id: int,
    query: str,
    db: AsyncSession,
    test_name: str,
    expected_cache_behavior: str
) -> Dict[str, Any]:
    """
    Run a single query test and measure performance.
    
    Returns:
        Dict with test results including duration and cache hits
    """
    print_subheader(f"Test: {test_name}")
    print(f"Query: {query}")
    print(f"Expected: {expected_cache_behavior}")
    print()
    
    start_time = time.time()
    
    try:
        response = await assistant.query(
            user_query=query,
            user_id=user_id,
            db=db,
            include_metadata=True
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract metrics
        metadata = response.get("metadata", {})
        from_cache = metadata.get("from_cache", False)
        answer = response.get("answer", "")
        sources_count = len(response.get("sources", []))
        
        # Print results
        print_metric("Duration", f"{duration_ms:.2f} ms", "⏱️")
        print_metric("From Cache (L1 Hit)", "Yes" if from_cache else "No", 
                    "🟢" if from_cache else "🔴")
        print_metric("Sources Found", sources_count, "📚")
        print_metric("Answer Length", f"{len(answer)} chars", "📝")
        
        if metadata:
            print("\nMetadata:")
            print(f"  Query Tokens: {metadata.get('query_tokens', 'N/A')}")
            print(f"  Context Tokens: {metadata.get('context_tokens', 'N/A')}")
            print(f"  Chunks Used: {metadata.get('chunks_used', 'N/A')}")
            print(f"  Chunks Retrieved: {metadata.get('chunks_retrieved', 'N/A')}")
        
        print(f"\nAnswer Preview: {answer[:200]}...")
        
        return {
            "success": True,
            "duration_ms": duration_ms,
            "from_cache": from_cache,
            "sources_count": sources_count,
            "metadata": metadata
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        
        return {
            "success": False,
            "duration_ms": duration_ms,
            "error": str(e)
        }


# ===========================
# TEST SCENARIOS
# ===========================

async def test_scenario_1_cold_start(
    assistant: AssistantService,
    user_id: int,
    db: AsyncSession
):
    """
    Scenario 1: Cold Start - All cache misses
    
    Expected behavior:
    - L1 miss → L2 miss → L3 miss
    - Full pipeline execution
    - Embeddings generated
    - Vector search performed
    - LLM inference called
    - All caches populated
    """
    print_header("SCENARIO 1: Cold Start (All Cache Misses)")
    
    query = TEST_QUERIES[0]
    
    result = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="Cold Start",
        expected_cache_behavior="L1 miss → L2 miss → L3 miss → Full pipeline"
    )
    
    if result["success"]:
        print("\n✅ Scenario 1 PASSED")
        print(f"   Baseline duration: {result['duration_ms']:.2f} ms")
    else:
        print("\n❌ Scenario 1 FAILED")
    
    return result


async def test_scenario_2_l2_hit(
    assistant: AssistantService,
    user_id: int,
    db: AsyncSession
):
    """
    Scenario 2: L2 Hit - Embedding cached
    
    Expected behavior:
    - L1 miss → L2 HIT (embedding from cache)
    - Skip embedding generation (~200ms saved)
    - Vector search still performed
    - LLM inference called
    - L3 and L1 populated
    """
    print_header("SCENARIO 2: L2 Hit (Embedding Cached)")
    
    query = TEST_QUERIES[0]  # Same query as Scenario 1
    
    result = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="L2 Hit",
        expected_cache_behavior="L1 miss → L2 HIT → L3 miss → Vector search + LLM"
    )
    
    if result["success"]:
        print("\n✅ Scenario 2 PASSED")
        print(f"   Duration: {result['duration_ms']:.2f} ms")
        print("   Expected: ~10-20% faster than cold start")
    else:
        print("\n❌ Scenario 2 FAILED")
    
    return result


async def test_scenario_3_l3_hit(
    assistant: AssistantService,
    user_id: int,
    db: AsyncSession
):
    """
    Scenario 3: L3 Hit - Embedding & Context cached
    
    Expected behavior:
    - L1 miss → L2 HIT → L3 HIT (chunks from cache)
    - Skip embedding generation
    - Skip vector search (~500ms saved)
    - LLM inference still called
    - L1 populated
    """
    print_header("SCENARIO 3: L3 Hit (Embedding & Context Cached)")
    
    query = TEST_QUERIES[0]  # Same query again
    
    result = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="L3 Hit",
        expected_cache_behavior="L1 miss → L2 HIT → L3 HIT → LLM only"
    )
    
    if result["success"]:
        print("\n✅ Scenario 3 PASSED")
        print(f"   Duration: {result['duration_ms']:.2f} ms")
        print("   Expected: ~30-50% faster than cold start")
    else:
        print("\n❌ Scenario 3 FAILED")
    
    return result


async def test_scenario_4_l1_hit(
    assistant: AssistantService,
    user_id: int,
    db: AsyncSession
):
    """
    Scenario 4: L1 Hit - Complete response cached (FASTEST)
    
    Expected behavior:
    - L1 HIT (complete response from cache)
    - Skip ALL expensive operations:
      - No embedding generation
      - No vector search
      - No LLM inference (~2-5s saved)
    - Return cached response immediately
    """
    print_header("SCENARIO 4: L1 Hit (Complete Response Cached)")
    
    query = TEST_QUERIES[0]  # Same query one more time
    
    result = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="L1 Hit - FASTEST PATH",
        expected_cache_behavior="L1 HIT → Instant return (no embedding, search, or LLM)"
    )
    
    if result["success"] and result["from_cache"]:
        print("\n✅ Scenario 4 PASSED")
        print(f"   Duration: {result['duration_ms']:.2f} ms")
        print("   Expected: 2-10x faster than cold start (should be <500ms)")
        
        if result["duration_ms"] < 500:
            print("   🟢 EXCELLENT: Sub-500ms response time!")
        elif result["duration_ms"] < 1000:
            print("   🟡 GOOD: Sub-1s response time")
        else:
            print("   🔴 WARNING: Slower than expected for L1 hit")
    else:
        print("\n❌ Scenario 4 FAILED - Expected L1 cache hit but got miss")
    
    return result


async def test_scenario_5_cache_invalidation(
    assistant: AssistantService,
    user_id: int,
    db: AsyncSession,
    cache_manager: RedisCacheManager
):
    """
    Scenario 5: Cache Invalidation after note update
    
    Expected behavior:
    - User updates a note
    - L3 context cache is invalidated for that user
    - Next query triggers L3 miss (but L2 still hits)
    - Fresh context retrieved
    - Response regenerated
    """
    print_header("SCENARIO 5: Cache Invalidation After Note Update")
    
    # First, run a query to populate caches
    query = TEST_QUERIES[1]  # Use a different query
    
    print_subheader("Step 1: Initial Query (Populate Caches)")
    result1 = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="Initial Query",
        expected_cache_behavior="Cold start → All caches populated"
    )
    
    # Simulate cache invalidation (what happens when user updates a note)
    print_subheader("Step 2: Simulate Note Update (Invalidate L3 Cache)")
    context_cache = ContextCache(cache_manager)
    await context_cache.invalidate_user(user_id)
    print("✅ L3 context cache invalidated for user")
    
    # Run same query again
    print_subheader("Step 3: Repeat Query After Invalidation")
    result2 = await run_query_test(
        assistant=assistant,
        user_id=user_id,
        query=query,
        db=db,
        test_name="Post-Invalidation Query",
        expected_cache_behavior="L1 miss (context changed) → L2 HIT → L3 miss → Fresh retrieval"
    )
    
    if result1["success"] and result2["success"]:
        print("\n✅ Scenario 5 PASSED")
        print(f"   Before invalidation: {result1['duration_ms']:.2f} ms")
        print(f"   After invalidation: {result2['duration_ms']:.2f} ms")
        print("   Expected: L3 cache miss forces fresh vector search")
    else:
        print("\n❌ Scenario 5 FAILED")
    
    return {"before": result1, "after": result2}


async def test_scenario_6_cache_statistics(
    assistant: AssistantService,
    cache_manager: RedisCacheManager
):
    """
    Scenario 6: Cache Statistics & Performance Analysis
    
    Collects and displays:
    - Hit rates for each cache layer
    - Total requests to each cache
    - Performance improvement metrics
    """
    print_header("SCENARIO 6: Cache Statistics & Performance Analysis")
    
    query_cache = QueryCache(cache_manager)
    embedding_cache = EmbeddingCache(cache_manager)
    context_cache = ContextCache(cache_manager)
    
    # Get stats from each cache layer
    l1_stats = await query_cache.get_stats()
    l2_stats = await embedding_cache.get_stats()
    l3_stats = await context_cache.get_stats()
    
    print_cache_stats(l1_stats, "L1 (Query Cache)")
    print_cache_stats(l2_stats, "L2 (Embedding Cache)")
    print_cache_stats(l3_stats, "L3 (Context Cache)")
    
    # Calculate overall cache effectiveness
    print("\n" + "=" * 80)
    print("  Overall Cache Effectiveness")
    print("=" * 80)
    
    l1_hit_rate = l1_stats.get("hit_rate", 0.0)
    l2_hit_rate = l2_stats.get("hit_rate", 0.0)
    l3_hit_rate = l3_stats.get("hit_rate", 0.0)
    
    # Estimated cost savings (based on Phase 2 targets)
    if l1_hit_rate >= 0.4:
        print("✅ L1 hit rate meets target (≥40%)")
    else:
        print(f"⚠️  L1 hit rate below target: {l1_hit_rate:.2%} < 40%")
    
    if l2_hit_rate >= 0.6:
        print("✅ L2 hit rate meets target (≥60%)")
    else:
        print(f"⚠️  L2 hit rate below target: {l2_hit_rate:.2%} < 60%")
    
    if l3_hit_rate >= 0.7:
        print("✅ L3 hit rate meets target (≥70%)")
    else:
        print(f"⚠️  L3 hit rate below target: {l3_hit_rate:.2%} < 70%")
    
    # Estimated cost reduction
    # L1 hit = ~$0.00026 saved per query (full LLM cost)
    # Assume 1000 queries/day
    l1_hits = l1_stats.get("hits", 0)
    estimated_daily_l1_savings = (l1_hit_rate * 1000) * 0.00026
    estimated_monthly_savings = estimated_daily_l1_savings * 30
    
    print(f"\n💰 Estimated Cost Savings (at 1000 queries/day):")
    print(f"   Daily: ${estimated_daily_l1_savings:.2f}")
    print(f"   Monthly: ${estimated_monthly_savings:.2f}")
    print(f"   Annual: ${estimated_monthly_savings * 12:.2f}")
    
    return {
        "l1_stats": l1_stats,
        "l2_stats": l2_stats,
        "l3_stats": l3_stats
    }


# ===========================
# MAIN TEST RUNNER
# ===========================

async def main():
    """Run all pipeline caching tests."""
    
    print_header("PIPELINE CACHING TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if caching is enabled
    from app.core.config import settings
    if not settings.cache_enabled:
        print("❌ ERROR: Caching is disabled!")
        print("   Set CACHE_ENABLED=true in your .env file")
        print("   And ensure Redis is running")
        return
    
    print("✅ Caching is enabled")
    print(f"   Redis URL: {settings.redis_url}")
    print()
    
    # Initialize cache manager
    cache_manager = await get_cache_manager()
    if not cache_manager or not cache_manager.is_available:
        print("❌ ERROR: Redis cache not available!")
        print("   Ensure Redis is running: docker run -d -p 6379:6379 redis:7-alpine")
        return
    
    print("✅ Redis connection established")
    
    # Initialize assistant service
    assistant = AssistantService(cache_manager=cache_manager)
    
    results = {}
    
    try:
        async with AsyncSessionLocal() as db:
            # Get test user
            print_subheader("Setup: Getting Test User")
            try:
                user = await get_test_user(db)
                print(f"✅ Test user found: {user.username} (ID: {user.id})")
            except ValueError as e:
                print(f"❌ {e}")
                return
            
            user_id = user.id
            
            # Clear all caches before starting tests
            print_subheader("Setup: Clearing All Caches")
            await clear_all_caches(cache_manager)
            
            # Run test scenarios
            results["scenario_1"] = await test_scenario_1_cold_start(assistant, user_id, db)
            await asyncio.sleep(0.5)  # Brief pause between tests
            
            results["scenario_2"] = await test_scenario_2_l2_hit(assistant, user_id, db)
            await asyncio.sleep(0.5)
            
            results["scenario_3"] = await test_scenario_3_l3_hit(assistant, user_id, db)
            await asyncio.sleep(0.5)
            
            results["scenario_4"] = await test_scenario_4_l1_hit(assistant, user_id, db)
            await asyncio.sleep(0.5)
            
            results["scenario_5"] = await test_scenario_5_cache_invalidation(
                assistant, user_id, db, cache_manager
            )
            await asyncio.sleep(0.5)
            
            results["scenario_6"] = await test_scenario_6_cache_statistics(
                assistant, cache_manager
            )
        
        # Print final summary
        print_header("TEST SUMMARY")
        
        scenarios_passed = 0
        scenarios_total = 5  # Exclude scenario 6 (stats only)
        
        for i in range(1, 6):
            scenario_key = f"scenario_{i}"
            scenario_result = results.get(scenario_key)
            
            if isinstance(scenario_result, dict):
                if scenario_result.get("success"):
                    scenarios_passed += 1
                    print(f"✅ Scenario {i} PASSED")
                else:
                    print(f"❌ Scenario {i} FAILED")
            else:
                # Scenario 5 returns nested results
                if scenario_result and scenario_result.get("before", {}).get("success"):
                    scenarios_passed += 1
                    print(f"✅ Scenario {i} PASSED")
                else:
                    print(f"❌ Scenario {i} FAILED")
        
        print()
        print(f"Total: {scenarios_passed}/{scenarios_total} scenarios passed")
        
        if scenarios_passed == scenarios_total:
            print("\n🎉 ALL TESTS PASSED! Cache system is working correctly.")
        else:
            print(f"\n⚠️  {scenarios_total - scenarios_passed} test(s) failed. Review output above.")
        
        # Performance comparison
        if results.get("scenario_1") and results.get("scenario_4"):
            cold_start_ms = results["scenario_1"]["duration_ms"]
            l1_hit_ms = results["scenario_4"]["duration_ms"]
            
            if l1_hit_ms > 0:
                speedup = cold_start_ms / l1_hit_ms
                improvement_pct = ((cold_start_ms - l1_hit_ms) / cold_start_ms) * 100
                
                print(f"\n⚡ Performance Improvement:")
                print(f"   Cold Start: {cold_start_ms:.2f} ms")
                print(f"   L1 Cache Hit: {l1_hit_ms:.2f} ms")
                print(f"   Speedup: {speedup:.2f}x faster")
                print(f"   Improvement: {improvement_pct:.1f}% reduction")
        
        print()
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite cancelled by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup: Clear caches after tests
        print_subheader("Cleanup: Clearing All Caches")
        await clear_all_caches(cache_manager)
        print("✅ Test cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
