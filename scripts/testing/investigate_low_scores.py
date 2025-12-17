"""
Investigate Low Relevance Scores

This script checks why relevance scores are so low by:
1. Examining the actual chunk text vs query
2. Testing embedding quality
3. Comparing query embedding to chunk embeddings
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.ai.embedding_service import EmbeddingService
from app.services.ai.tokenizer_service import get_tokenizer_service
import numpy as np


async def main():
    print("=" * 80)
    print("INVESTIGATING LOW RELEVANCE SCORES")
    print("=" * 80)
    print()
    
    # Test queries
    queries = [
        "What is grace?",
        "grace",
        "God's grace",
        "What is grace according to the sermon notes?"
    ]
    
    embedding_service = EmbeddingService()
    tokenizer = get_tokenizer_service()
    
    async with AsyncSessionLocal() as db:
        # Get a sample chunk about grace
        chunk_sql = text("""
            SELECT 
                nc.chunk_text,
                nc.embedding
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = 7
              AND n.title LIKE '%Grace%'
            LIMIT 1
        """)
        
        result = await db.execute(chunk_sql)
        chunk = result.fetchone()
        
        if not chunk:
            print("❌ No grace-related chunks found")
            return
        
        print("CHUNK TEXT (first 200 chars):")
        print("-" * 80)
        print(chunk.chunk_text[:200] + "...")
        print()
        
        # Get chunk embedding as list
        chunk_embedding = chunk.embedding
        
        print("TESTING DIFFERENT QUERIES:")
        print("-" * 80)
        print(f"{'Query':<45} {'Tokens':<8} {'Score':<8} {'Status'}")
        print("-" * 80)
        
        for query in queries:
            # Generate query embedding
            query_embedding = embedding_service.generate(query)
            query_tokens = tokenizer.count_tokens(query)
            
            # Calculate cosine similarity manually
            # pgvector uses <-> which is 1 - cosine_similarity
            # So we need to calculate: 1 - distance
            
            # Query database for score
            score_sql = text("""
                SELECT 1 - (nc.embedding <-> :query_vec) as score
                FROM note_chunks nc
                INNER JOIN notes n ON nc.note_id = n.id
                WHERE n.user_id = 7
                  AND n.title LIKE '%Grace%'
                LIMIT 1
            """)
            
            score_result = await db.execute(score_sql, {"query_vec": str(query_embedding)})
            score_row = score_result.fetchone()
            score = score_row.score if score_row else 0.0
            
            # Status
            if score >= 0.6:
                status = "🟢 Good"
            elif score >= 0.4:
                status = "🟡 Medium"
            elif score >= 0.2:
                status = "🟠 Low"
            else:
                status = "🔴 Poor"
            
            print(f"{query:<45} {query_tokens:<8} {score:.4f}   {status}")
        
        print()
        print("=" * 80)
        print("DIAGNOSIS:")
        print("=" * 80)
        
        # Check if embeddings are normalized
        print("\nChecking embedding properties...")
        
        # Sample multiple embeddings
        sample_sql = text("""
            SELECT nc.embedding
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = 7
            LIMIT 3
        """)
        
        sample_result = await db.execute(sample_sql)
        sample_embeddings = sample_result.fetchall()
        
        print(f"✅ Found {len(sample_embeddings)} sample embeddings")
        print(f"✅ Embedding type: {type(sample_embeddings[0].embedding)}")
        
        # Test direct similarity between two grace-related texts
        print("\n" + "=" * 80)
        print("TESTING DIRECT TEXT SIMILARITY:")
        print("=" * 80)
        
        text1 = "grace is the unmerited favor of God"
        text2 = "what is grace"
        
        emb1 = embedding_service.generate(text1)
        emb2 = embedding_service.generate(text2)
        
        # Calculate cosine similarity using numpy
        emb1_arr = np.array(emb1)
        emb2_arr = np.array(emb2)
        
        # Normalize
        emb1_norm = emb1_arr / np.linalg.norm(emb1_arr)
        emb2_norm = emb2_arr / np.linalg.norm(emb2_arr)
        
        # Cosine similarity
        cos_sim = np.dot(emb1_norm, emb2_norm)
        
        print(f"\nText 1: '{text1}'")
        print(f"Text 2: '{text2}'")
        print(f"Direct Cosine Similarity: {cos_sim:.4f}")
        
        if cos_sim < 0.5:
            print("\n⚠️  WARNING: Even direct text similarity is low!")
            print("   This suggests the embedding model might not be loaded correctly")
            print("   or there's an issue with how embeddings are being generated.")
        
        print()


if __name__ == "__main__":
    asyncio.run(main())
