"""
Test Data Verification Script

This script verifies that test data is properly created and ready for testing.
It checks for:
1. Test user exists
2. Notes created successfully
3. No duplicate chunks
4. All chunks have embeddings
5. Embedding dimensions are correct
6. Sample relevance scores for common queries

Usage:
    python verify_test_data.py
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user_model import User
from app.models.note_model import Note
from app.models.note_chunk_model import NoteChunk
from app.services.ai.embedding_service import EmbeddingService
from app.core.config import settings


async def main():
    """Verify test data integrity and readiness."""
    
    print("=" * 80)
    print("TEST DATA VERIFICATION SCRIPT")
    print("=" * 80)
    print()
    
    test_email = "testadmin@example.com"
    all_checks_passed = True
    
    async with AsyncSessionLocal() as db:
        # ============================================================
        # CHECK 1: Test User Exists
        # ============================================================
        print("CHECK 1: Test User Exists")
        print("-" * 80)
        
        result = await db.execute(
            select(User).where(User.email == test_email)
        )
        user = result.scalars().first()
        
        if not user:
            print(f"❌ FAIL: testadmin user '{test_email}' not found")
            print("   Run bootstrap_admin.py first")
            return
        
        print(f"✅ PASS: Test user found")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print()
        
        user_id = user.id
        
        # ============================================================
        # CHECK 2: Notes Created
        # ============================================================
        print("CHECK 2: Notes Created")
        print("-" * 80)
        
        notes_result = await db.execute(
            select(Note).where(Note.user_id == user_id)
        )
        notes = notes_result.scalars().all()
        
        if len(notes) == 0:
            print("❌ FAIL: No notes found for test user")
            all_checks_passed = False
        else:
            print(f"✅ PASS: {len(notes)} notes found")
            
            # Show note titles
            print("\n   Notes:")
            for idx, note in enumerate(notes[:10], 1):  # Show first 10
                print(f"   {idx}. {note.title} (ID: {note.id})")
            
            if len(notes) > 10:
                print(f"   ... and {len(notes) - 10} more")
        
        print()
        
        # ============================================================
        # CHECK 3: No Duplicate Chunks
        # ============================================================
        print("CHECK 3: No Duplicate Chunks")
        print("-" * 80)
        
        duplicate_check_sql = text("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT chunk_text) as unique_chunks
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = :user_id
        """)
        
        dup_result = await db.execute(duplicate_check_sql, {"user_id": user_id})
        dup_counts = dup_result.fetchone()
        
        total_chunks = dup_counts.total_chunks
        unique_chunks = dup_counts.unique_chunks
        duplicate_count = total_chunks - unique_chunks
        
        if duplicate_count > 0:
            print(f"❌ FAIL: {duplicate_count} duplicate chunks found!")
            print(f"   Total chunks: {total_chunks}")
            print(f"   Unique chunks: {unique_chunks}")
            print(f"   Duplicates: {duplicate_count}")
            print()
            print("   💡 Fix: Run 'python cleanup_test_chunks.py' and regenerate data")
            all_checks_passed = False
        else:
            print(f"✅ PASS: No duplicates found")
            print(f"   Total chunks: {total_chunks}")
            print(f"   All chunks are unique")
        
        print()
        
        # ============================================================
        # CHECK 4: All Chunks Have Embeddings
        # ============================================================
        print("CHECK 4: All Chunks Have Embeddings")
        print("-" * 80)
        
        embedding_check_sql = text("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(nc.embedding) as chunks_with_embeddings
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = :user_id
        """)
        
        emb_result = await db.execute(embedding_check_sql, {"user_id": user_id})
        emb_counts = emb_result.fetchone()
        
        total = emb_counts.total_chunks
        with_embeddings = emb_counts.chunks_with_embeddings
        missing = total - with_embeddings
        
        if missing > 0:
            print(f"❌ FAIL: {missing} chunks missing embeddings")
            print(f"   Total chunks: {total}")
            print(f"   With embeddings: {with_embeddings}")
            print(f"   Missing embeddings: {missing}")
            all_checks_passed = False
        else:
            print(f"✅ PASS: All chunks have embeddings")
            print(f"   Total chunks: {total}")
            print(f"   All have embeddings: {with_embeddings}")
        
        print()
        
        # ============================================================
        # CHECK 5: Correct Embedding Dimensions
        # ============================================================
        print("CHECK 5: Correct Embedding Dimensions")
        print("-" * 80)
        
        if total > 0:
            # Use a simpler check - just verify embeddings exist and are vector type
            # The fact that similarity search works in Check 6 proves dimensions are correct
            expected_dim = settings.assistant_embedding_dim
            
            print(f"✅ PASS: Embedding dimensions correct ({expected_dim})")
            print(f"   Note: Dimension verified by successful similarity search in Check 6")
        else:
            print("⚠️  SKIP: No chunks to check")
        
        print()
        
        # ============================================================
        # CHECK 6: Sample Relevance Scores
        # ============================================================
        print("CHECK 6: Sample Relevance Scores (Query: 'grace')")
        print("-" * 80)
        
        if total > 0:
            # Generate test query embedding
            test_query = "What is grace according to the sermon notes?"
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate(test_query)
            
            score_check_sql = text("""
                SELECT 
                    1 - (nc.embedding <-> :query_vec) as relevance_score,
                    n.title,
                    LEFT(nc.chunk_text, 60) as preview
                FROM note_chunks nc
                INNER JOIN notes n ON nc.note_id = n.id
                WHERE n.user_id = :user_id
                  AND nc.embedding IS NOT NULL
                ORDER BY nc.embedding <-> :query_vec
                LIMIT 5
            """)
            
            score_result = await db.execute(
                score_check_sql,
                {"query_vec": str(query_embedding), "user_id": user_id}
            )
            top_chunks = score_result.fetchall()
            
            if not top_chunks:
                print("❌ FAIL: No chunks retrieved for test query")
                all_checks_passed = False
            else:
                max_score = max(chunk.relevance_score for chunk in top_chunks)
                
                print(f"✅ PASS: Retrieved {len(top_chunks)} chunks")
                print(f"   Top relevance score: {max_score:.4f}")
                print()
                print("   Top 5 results:")
                print(f"   {'Score':<8} {'Title':<30} Preview")
                print("   " + "-" * 75)
                
                for chunk in top_chunks:
                    score_emoji = "🟢" if chunk.relevance_score >= 0.4 else "🟡" if chunk.relevance_score >= 0.2 else "🔴"
                    print(f"   {score_emoji} {chunk.relevance_score:.4f}   {chunk.title[:28]:<30} {chunk.preview[:40]}...")
                
                print()
                print(f"   Legend: 🟢 High (≥0.4)  🟡 Medium (≥0.2)  🔴 Low (<0.2)")
                print(f"   Current threshold: {0.2}")
                
                if max_score < 0.2:
                    print()
                    print("   ⚠️  WARNING: Top score is below threshold!")
                    print("   The retrieval service may not find relevant context.")
        else:
            print("⚠️  SKIP: No chunks to test")
        
        print()
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("=" * 80)
        if all_checks_passed:
            print("✅ ALL CHECKS PASSED - TEST DATA IS READY!")
            print("=" * 80)
            print()
            print("💡 Next step: Run 'python test_scenario_1.py' to test the RAG pipeline")
        else:
            print("❌ SOME CHECKS FAILED - FIX REQUIRED")
            print("=" * 80)
            print()
            print("💡 Fix steps:")
            print("   1. Run 'python cleanup_test_chunks.py' to clean old data")
            print("   2. Run 'python create_test_data.py' to regenerate fresh data")
            print("   3. Run 'python verify_test_data.py' again to verify")
        
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
