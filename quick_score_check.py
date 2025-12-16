"""Quick SQL query to check relevance scores directly."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.ai.embedding_service import EmbeddingService


async def main():
    query = "What is grace according to the sermon notes?"
    
    print(f"Query: {query}\n")
    
    # Generate embedding
    embedding_service = EmbeddingService()
    query_vec = embedding_service.generate(query)
    
    async with AsyncSessionLocal() as db:
        # Direct SQL query
        sql = text("""
            SELECT 
                1 - (nc.embedding <-> :query_vec) as score,
                n.title,
                LEFT(nc.chunk_text, 60) as preview
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = 7
            ORDER BY nc.embedding <-> :query_vec
            LIMIT 10
        """)
        
        result = await db.execute(sql, {"query_vec": str(query_vec)})
        rows = result.fetchall()
        
        print(f"{'Score':<10} {'Title':<30} Preview")
        print("-" * 100)
        for row in rows:
            print(f"{row.score:.4f}     {row.title:<30} {row.preview}...")


if __name__ == "__main__":
    asyncio.run(main())
