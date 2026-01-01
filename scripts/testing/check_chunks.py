"""Check for duplicate chunks in database."""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        # Get testadmin user
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
        
        # Check unique chunks
        sql = text("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT chunk_text) as unique_chunks,
                COUNT(DISTINCT note_id) as unique_notes
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = :user_id
        """)
        
        result = await db.execute(sql, {"user_id": user.id})
        row = result.fetchone()
        
        print(f"Total chunks: {row.total_chunks}")
        print(f"Unique chunk texts: {row.unique_chunks}")
        print(f"Unique notes: {row.unique_notes}")
        
        if row.total_chunks != row.unique_chunks:
            print(f"\n⚠️  WARNING: {row.total_chunks - row.unique_chunks} duplicate chunks found!")
        
        # Show some chunk samples
        sql2 = text("""
            SELECT 
                nc.id,
                n.title,
                nc.chunk_idx,
                LEFT(nc.chunk_text, 80) as preview
            FROM note_chunks nc
            INNER JOIN notes n ON nc.note_id = n.id
            WHERE n.user_id = :user_id
            ORDER BY n.id, nc.chunk_idx
            LIMIT 10
        """)
        
        result2 = await db.execute(sql2, {"user_id": user.id})
        rows = result2.fetchall()
        
        print("\nSample chunks:")
        print("-" * 100)
        for row in rows:
            print(f"[{row.id}] {row.title} (chunk {row.chunk_idx})")
            print(f"  {row.preview}...")
            print()


if __name__ == "__main__":
    asyncio.run(main())
