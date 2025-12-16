"""
Debug script to check actual relevance scores returned by semantic search.

This helps identify if the relevance_threshold (currently 0.6) is too strict.
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user_model import User
from app.services.ai.embedding_service import EmbeddingService


async def main():
    """Check relevance scores for grace query."""
    
    query = "What is grace according to the sermon notes?"
    
    print("=" * 80)
    print("DEBUG: Relevance Score Analysis")
    print("=" * 80)
    print(f"Query: {query}\n")
    
    # Generate query embedding
    embedding_service = EmbeddingService()
    query_embedding = embedding_service.generate(query)
    print(f"✅ Generated query embedding ({len(query_embedding)} dims)\n")
    
    async with AsyncSessionLocal() as db:
        # Get test user
        result = await db.execute(
            select(User).where(User.email == "test@scribes.local")
        )
        user = result.scalars().first()
        
        if not user:
            print("❌ Test user not found. Run create_test_data.py first.")
            return
        
        print(f"✅ Found test user: {user.username} (id={user.id})\n")
        
        # Run vector search
        query_sql = text("""
            SELECT 
                nc.id as chunk_id,
                nc.note_id,
                nc.chunk_idx,
                nc.chunk_text,
                1 - (nc.embedding <-> :query_vec) as relevance_score,
                n.title as note_title
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE 
                n.user_id = :user_id
                AND nc.embedding IS NOT NULL
            ORDER BY nc.embedding <-> :query_vec
            LIMIT 10
        """)
        
        result = await db.execute(
            query_sql,
            {
                "query_vec": str(query_embedding),
                "user_id": user.id
            }
        )
        
        chunks = result.fetchall()
        
        print(f"Retrieved {len(chunks)} chunks\n")
        print("-" * 80)
        print(f"{'Rank':<6} {'Score':<8} {'Note Title':<30} {'Preview':<40}")
        print("-" * 80)
        
        for idx, chunk in enumerate(chunks, 1):
            score = chunk.relevance_score
            title = chunk.note_title[:28]
            preview = chunk.chunk_text[:37] + "..."
            
            # Highlight scores above threshold
            marker = "🟢" if score >= 0.6 else "🔴" if score >= 0.4 else "⚪"
            
            print(f"{marker} {idx:<4} {score:.4f}   {title:<30} {preview}")
        
        print("-" * 80)
        print("\nLegend:")
        print("  🟢 = Score >= 0.6 (HIGH relevance - currently used)")
        print("  🔴 = Score >= 0.4 (MEDIUM relevance - currently skipped)")
        print("  ⚪ = Score < 0.4 (LOW relevance)")
        print("\n💡 If most scores are in the 0.4-0.6 range, consider lowering the threshold.")


if __name__ == "__main__":
    asyncio.run(main())
