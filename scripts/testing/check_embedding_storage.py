"""
Check if stored embeddings match freshly generated embeddings.

This will help us understand if the issue is with:
1. How embeddings are stored in the database
2. How pgvector computes similarity
3. The embedding model itself
"""

import sys
import asyncio
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.ai.embedding_service import EmbeddingService


async def main():
    print("=" * 80)
    print("CHECKING STORED VS FRESH EMBEDDINGS")
    print("=" * 80)
    print()
    
    embedding_service = EmbeddingService()
    
    async with AsyncSessionLocal() as db:
        # Get testadmin user first
        from app.models.user_model import User
        from sqlalchemy import select
        
        result = await db.execute(
            select(User).where(User.email == "testadmin@example.com")
        )
        user = result.scalars().first()
        
        if not user:
            print("❌ testadmin user not found. Run bootstrap_admin.py first.")
            return
        
        print(f"✅ Using testadmin user (ID: {user.id})\n")
        
        # Get a chunk and its stored embedding
        sql = text("""
            SELECT 
                nc.chunk_text,
                nc.embedding
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = :user_id
              AND n.title LIKE '%Grace%'
            LIMIT 1
        """)
        
        result = await db.execute(sql, {"user_id": user.id})
        row = result.fetchone()
        
        if not row:
            print("❌ No chunks found")
            return
        
        chunk_text = row.chunk_text
        stored_embedding_str = row.embedding
        
        print(f"Chunk text: {chunk_text[:100]}...")
        print()
        
        # Generate fresh embedding
        fresh_embedding = embedding_service.generate(chunk_text)
        
        print(f"✅ Fresh embedding dimension: {len(fresh_embedding)}")
        print(f"✅ Stored embedding type: {type(stored_embedding_str)}")
        print(f"✅ Stored embedding length (as string): {len(stored_embedding_str)}")
        print()
        
        # Parse stored embedding string back to list
        # pgvector returns it as a string like "[0.1, 0.2, 0.3]"
        try:
            import json
            stored_embedding = json.loads(stored_embedding_str.replace("'", '"'))
            print(f"✅ Parsed stored embedding dimension: {len(stored_embedding)}")
        except:
            print(f"❌ Failed to parse stored embedding")
            print(f"   First 100 chars: {stored_embedding_str[:100]}")
            return
        
        print()
        print("COMPARING EMBEDDINGS:")
        print("-" * 80)
        
        # Compare first 5 values
        print(f"{'Index':<8} {'Fresh':<15} {'Stored':<15} {'Match?'}")
        print("-" * 80)
        
        matches = 0
        for i in range(min(10, len(fresh_embedding))):
            fresh_val = fresh_embedding[i]
            stored_val = stored_embedding[i]
            diff = abs(fresh_val - stored_val)
            match = "✅" if diff < 0.0001 else "❌"
            
            if diff < 0.0001:
                matches += 1
            
            print(f"{i:<8} {fresh_val:<15.6f} {stored_val:<15.6f} {match} (diff: {diff:.8f})")
        
        print()
        print(f"Matches: {matches}/10")
        
        if matches < 8:
            print("\n⚠️  WARNING: Stored embeddings don't match fresh embeddings!")
            print("   This could mean:")
            print("   1. Embeddings are being corrupted during storage")
            print("   2. Different embedding model version")
            print("   3. Non-deterministic embedding generation")
        else:
            print("\n✅ Stored embeddings match fresh embeddings")
            print("   The low similarity scores must be due to something else")
        
        # Compute cosine similarity manually
        fresh_arr = np.array(fresh_embedding)
        stored_arr = np.array(stored_embedding)
        
        cos_sim = np.dot(fresh_arr, stored_arr) / (np.linalg.norm(fresh_arr) * np.linalg.norm(stored_arr))
        
        print(f"\n Manual cosine similarity (fresh vs stored): {cos_sim:.4f}")
        
        if cos_sim < 0.99:
            print("   ⚠️  Embeddings are different!")
        else:
            print("   ✅ Embeddings are identical")


if __name__ == "__main__":
    asyncio.run(main())
