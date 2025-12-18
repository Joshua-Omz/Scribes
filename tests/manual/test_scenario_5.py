"""
Test Scenario 3.5: Answer Quality Validation
=============================================

This test validates the quality, accuracy, and pastoral tone of generated answers.
The system should:
1. Cite specific sermon notes
2. Include scripture references
3. Be theologically sound
4. Maintain warm, pastoral tone
5. Stay within provided context (no hallucination)

Expected: High-quality answers with proper citations
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


# Test queries with expected content
TEST_QUERIES = [
    {
        "query": "What is faith according to my sermon notes?",
        "expected_keywords": ["hebrews", "substance", "evidence", "trust", "belief", "faith"],
        "expected_scripture": ["Hebrews 11:1", "James 2:17"],
        "expected_note_topics": ["faith", "works", "trust"],
        "min_length": 150,  # Minimum answer length in chars
    },
    {
        "query": "How does God demonstrate His love?",
        "expected_keywords": ["christ", "died", "sinners", "sacrifice", "romans", "love"],
        "expected_scripture": ["Romans 5:8", "1 John 4:8"],
        "expected_note_topics": ["love", "sacrifice"],
        "min_length": 150,
    },
    {
        "query": "What is the fruit of the Spirit?",
        "expected_keywords": ["love", "joy", "peace", "patience", "galatians", "spirit"],
        "expected_scripture": ["Galatians 5:22"],
        "expected_note_topics": ["holy spirit", "fruit", "gifts"],
        "min_length": 150,
    },
    {
        "query": "Explain grace from my notes",
        "expected_keywords": ["grace", "unmerited", "favor", "ephesians", "gift"],
        "expected_scripture": ["Ephesians 2:8-9"],
        "expected_note_topics": ["grace", "mercy", "salvation"],
        "min_length": 150,
    },
    {
        "query": "What do my notes say about prayer?",
        "expected_keywords": ["prayer", "father", "relationship", "communion", "thessalonians"],
        "expected_scripture": ["1 Thessalonians 5:17", "Matthew 6:9"],
        "expected_note_topics": ["prayer", "intimacy"],
        "min_length": 150,
    }
]


async def test_single_query_quality(assistant, db, test_case: dict, test_num: int):
    """Test quality of a single query response."""
    
    print(f"\n{'='*80}")
    print(f"TEST {test_num}: {test_case['query']}")
    print('='*80)
    
    user_id = 7  # Replace with your test user ID
    
    try:
        response = await assistant.query(
            user_query=test_case["query"],
            user_id=user_id,
            db=db,
            max_sources=5,
            include_metadata=True
        )
        
        answer = response["answer"]
        answer_lower = answer.lower()
        sources = response.get("sources", [])
        metadata = response.get("metadata", {})
        
        print(f"\n📝 ANSWER ({len(answer)} chars):")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
        print(f"\n📚 SOURCES ({len(sources)}):")
        for i, source in enumerate(sources, 1):
            print(f"{i}. {source['note_title']} by {source.get('preacher', 'Unknown')}")
        
        print(f"\n📊 METADATA:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        
        # ============================================================
        # QUALITY ASSESSMENT
        # ============================================================
        print(f"\n{'='*80}")
        print("QUALITY ASSESSMENT:")
        print('='*80)
        
        score = 0
        max_score = 0
        
        # Check 1: Keyword Relevance (20 points)
        max_score += 20
        keyword_matches = sum(1 for kw in test_case["expected_keywords"] if kw in answer_lower)
        keyword_score = min(20, (keyword_matches / len(test_case["expected_keywords"])) * 20)
        score += keyword_score
        
        print(f"\n1. KEYWORD RELEVANCE: {keyword_score:.0f}/20")
        print(f"   Found {keyword_matches}/{len(test_case['expected_keywords'])} expected keywords")
        matched = [kw for kw in test_case["expected_keywords"] if kw in answer_lower]
        missing = [kw for kw in test_case["expected_keywords"] if kw not in answer_lower]
        if matched:
            print(f"   ✅ Matched: {', '.join(matched)}")
        if missing:
            print(f"   ⚠️  Missing: {', '.join(missing)}")
        
        # Check 2: Scripture Citations (25 points)
        max_score += 25
        scripture_found = []
        for scripture in test_case["expected_scripture"]:
            # Check various formats (e.g., "Hebrews 11:1" or "hebrews 11")
            scripture_normalized = scripture.lower().replace(":", " ")
            if scripture.lower() in answer_lower or scripture_normalized in answer_lower:
                scripture_found.append(scripture)
        
        scripture_score = (len(scripture_found) / len(test_case["expected_scripture"])) * 25
        score += scripture_score
        
        print(f"\n2. SCRIPTURE CITATIONS: {scripture_score:.0f}/25")
        print(f"   Found {len(scripture_found)}/{len(test_case['expected_scripture'])} expected scriptures")
        if scripture_found:
            print(f"   ✅ Cited: {', '.join(scripture_found)}")
        missing_scripture = [s for s in test_case["expected_scripture"] if s not in scripture_found]
        if missing_scripture:
            print(f"   ⚠️  Missing: {', '.join(missing_scripture)}")
        
        # Check 3: Source Citations (15 points)
        max_score += 15
        source_citation_score = 0
        
        if len(sources) > 0:
            # Check if answer mentions source titles
            sources_cited = sum(1 for source in sources if source['note_title'].lower() in answer_lower)
            source_citation_score = (sources_cited / len(sources)) * 15
        
        score += source_citation_score
        
        print(f"\n3. SOURCE CITATIONS: {source_citation_score:.0f}/15")
        if len(sources) > 0:
            print(f"   {sources_cited}/{len(sources)} source titles mentioned in answer")
            if sources_cited > 0:
                print(f"   ✅ Cites sermon notes by title")
            else:
                print(f"   ⚠️  No note titles mentioned")
        else:
            print(f"   ⚠️  No sources retrieved")
        
        # Check 4: Answer Length/Completeness (10 points)
        max_score += 10
        length_score = 0
        
        if len(answer) >= test_case["min_length"]:
            length_score = 10
        elif len(answer) >= test_case["min_length"] * 0.5:
            length_score = 5
        
        score += length_score
        
        print(f"\n4. COMPLETENESS: {length_score:.0f}/10")
        print(f"   Answer length: {len(answer)} chars (min: {test_case['min_length']})")
        if length_score == 10:
            print(f"   ✅ Substantive and detailed")
        elif length_score == 5:
            print(f"   ⚠️  Somewhat brief")
        else:
            print(f"   ❌ Too short")
        
        # Check 5: Pastoral Tone (15 points)
        max_score += 15
        pastoral_indicators = [
            "you", "your", "we", "our", "us",
            "god's", "help", "bless", "encourage",
            "understand", "explore", "learn"
        ]
        
        pastoral_count = sum(1 for indicator in pastoral_indicators if indicator in answer_lower)
        pastoral_score = min(15, (pastoral_count / 5) * 15)  # Need at least 5 pastoral indicators
        score += pastoral_score
        
        print(f"\n5. PASTORAL TONE: {pastoral_score:.0f}/15")
        print(f"   Found {pastoral_count} pastoral indicators")
        if pastoral_score >= 12:
            print(f"   ✅ Warm and relational")
        elif pastoral_score >= 7:
            print(f"   ⚠️  Somewhat pastoral")
        else:
            print(f"   ❌ Too formal/impersonal")
        
        # Check 6: No Hallucination (15 points)
        max_score += 15
        hallucination_score = 15  # Start with full points, deduct for issues
        
        # Check for common hallucination indicators
        hallucination_flags = [
            "i don't have access",
            "as an ai",
            "i cannot",
            "my training data",
            "i apologize, but"
        ]
        
        has_hallucination_flag = any(flag in answer_lower for flag in hallucination_flags)
        
        # Check if answer stays on topic
        has_topic_words = any(topic in answer_lower for topic in test_case["expected_note_topics"])
        
        if has_hallucination_flag:
            hallucination_score -= 5
            print(f"\n6. CONTEXT FIDELITY: {hallucination_score:.0f}/15")
            print(f"   ⚠️  Contains AI self-reference")
        elif not has_topic_words and len(sources) > 0:
            hallucination_score -= 10
            print(f"\n6. CONTEXT FIDELITY: {hallucination_score:.0f}/15")
            print(f"   ⚠️  Answer may be off-topic")
        else:
            print(f"\n6. CONTEXT FIDELITY: {hallucination_score:.0f}/15")
            print(f"   ✅ Stays within sermon note context")
        
        score += hallucination_score
        
        # ============================================================
        # FINAL SCORE
        # ============================================================
        percentage = (score / max_score) * 100
        
        print(f"\n{'='*80}")
        print(f"FINAL SCORE: {score:.1f}/{max_score} ({percentage:.1f}%)")
        print('='*80)
        
        if percentage >= 90:
            grade = "A (Excellent)"
            emoji = "🌟"
        elif percentage >= 80:
            grade = "B (Good)"
            emoji = "✅"
        elif percentage >= 70:
            grade = "C (Acceptable)"
            emoji = "👍"
        elif percentage >= 60:
            grade = "D (Needs Improvement)"
            emoji = "⚠️"
        else:
            grade = "F (Poor)"
            emoji = "❌"
        
        print(f"{emoji} GRADE: {grade}")
        
        return {
            "query": test_case["query"],
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "grade": grade,
            "answer_length": len(answer),
            "sources_count": len(sources),
            "passed": percentage >= 70  # 70% is passing
        }
        
    except Exception as e:
        print(f"\n❌ ERROR during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "query": test_case["query"],
            "score": 0,
            "max_score": 100,
            "percentage": 0,
            "grade": "F (Error)",
            "error": str(e),
            "passed": False
        }


async def test_answer_quality():
    """Test answer quality across multiple queries."""
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    assistant = get_assistant_service()
    
    print("\n" + "🌟 " * 20)
    print("ANSWER QUALITY VALIDATION TEST SUITE")
    print("🌟 " * 20)
    
    print(f"\nTesting {len(TEST_QUERIES)} queries for quality metrics:")
    print("  - Keyword relevance (theological terms)")
    print("  - Scripture citations")
    print("  - Source citations (note titles)")
    print("  - Completeness (length)")
    print("  - Pastoral tone")
    print("  - Context fidelity (no hallucination)")
    
    results = []
    
    async with async_session() as db:
        for i, test_case in enumerate(TEST_QUERIES, 1):
            result = await test_single_query_quality(assistant, db, test_case, i)
            results.append(result)
    
    # ============================================================
    # OVERALL SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("OVERALL QUALITY SUMMARY")
    print("="*80)
    
    total_score = sum(r["score"] for r in results)
    total_max = sum(r["max_score"] for r in results)
    overall_percentage = (total_score / total_max) * 100
    
    print(f"\n📊 AGGREGATE SCORES:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{i}. {result['query'][:50]:50} | {result['percentage']:5.1f}% | {status}")
    
    print(f"\n{'='*80}")
    print(f"OVERALL SCORE: {total_score:.1f}/{total_max} ({overall_percentage:.1f}%)")
    print(f"PASSED: {sum(1 for r in results if r['passed'])}/{len(results)} tests")
    print('='*80)
    
    # Determine overall grade
    if overall_percentage >= 90:
        overall_grade = "A (Excellent)"
        print("\n🌟 🌟 🌟 EXCELLENT QUALITY 🌟 🌟 🌟")
        print("Answers are highly accurate, well-cited, and pastorally sound!")
    elif overall_percentage >= 80:
        overall_grade = "B (Good)"
        print("\n✅ ✅ ✅ GOOD QUALITY ✅ ✅ ✅")
        print("Answers are generally good with minor areas for improvement.")
    elif overall_percentage >= 70:
        overall_grade = "C (Acceptable)"
        print("\n👍 ACCEPTABLE QUALITY")
        print("Answers meet basic standards but need improvement.")
    else:
        overall_grade = "F (Poor)"
        print("\n❌ QUALITY NEEDS IMPROVEMENT")
        print("Answers require significant enhancement.")
    
    print(f"\nOVERALL GRADE: {overall_grade}")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS:")
    print('='*80)
    
    # Analyze weak areas
    avg_keyword = sum(1 for r in results if r.get("percentage", 0) >= 70) / len(results) * 100
    
    if overall_percentage < 80:
        print("\n💡 Areas for Improvement:")
        if overall_percentage < 70:
            print("   - Review system prompt for better instruction clarity")
            print("   - Ensure sermon notes have rich theological content")
            print("   - Verify context builder is retrieving best chunks")
        print("   - Consider adjusting temperature (currently: {:.1f})".format(settings.hf_generation_temperature))
        print("   - Review PromptEngine instructions for citation requirements")
    else:
        print("\n✅ System is performing well!")
        print("   - Continue monitoring answer quality")
        print("   - Consider A/B testing different prompts for optimization")
    
    return results


if __name__ == "__main__":
    print("\n" + "🔬 " * 20)
    print("AssistantService Test Suite - Scenario 3.5")
    print("ANSWER QUALITY VALIDATION")
    print("🔬 " * 20 + "\n")
    
    asyncio.run(test_answer_quality())
    
    print("\n" + "="*80)
    print("Quality validation complete! Review scores above.")
    print("="*80 + "\n")
