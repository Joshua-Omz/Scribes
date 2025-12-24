"""
Cleanup Script - Delete All Test User Notes and Chunks

This script deletes all notes and chunks for the test user to allow
clean regeneration of test data without duplicates.

Usage:
    python cleanup_test_chunks.py
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user_model import User
from app.models.note_model import Note
from app.models.note_chunk_model import NoteChunk


async def main():
    """Delete all notes and chunks for test user."""
    
    print("=" * 80)
    print("TEST DATA CLEANUP SCRIPT")
    print("=" * 80)
    print()
    
    test_email = "testadmin@example.com"
    
    async with AsyncSessionLocal() as db:
        # Find test user
        result = await db.execute(
            select(User).where(User.email == test_email)
        )
        user = result.scalars().first()
        
        if not user:
            print(f"❌ Test user '{test_email}' not found.")
            print("   Nothing to clean up.")
            return
        
        print(f"✅ Found test user: {user.username} (id={user.id}, email={user.email})")
        print()
        
        # Count existing data before deletion
        count_sql = text("""
            SELECT 
                COUNT(DISTINCT n.id) as note_count,
                COUNT(nc.id) as chunk_count,
                COUNT(DISTINCT nc.chunk_text) as unique_chunk_count
            FROM notes n
            LEFT JOIN note_chunks nc ON nc.note_id = n.id
            WHERE n.user_id = :user_id
        """)
        
        count_result = await db.execute(count_sql, {"user_id": user.id})
        counts = count_result.fetchone()
        
        print(f"📊 Current state:")
        print(f"   Notes: {counts.note_count}")
        print(f"   Total Chunks: {counts.chunk_count}")
        print(f"   Unique Chunks: {counts.unique_chunk_count}")
        
        if counts.chunk_count != counts.unique_chunk_count:
            duplicates = counts.chunk_count - counts.unique_chunk_count
            print(f"   ⚠️  Duplicate Chunks: {duplicates}")
        
        print()
        
        if counts.note_count == 0:
            print("✅ No notes found. Database is already clean for this user.")
            return
        
        # Confirm deletion
        print("⚠️  WARNING: This will DELETE ALL notes and chunks for the test user!")
        print()
        response = input("Type 'YES' to confirm deletion: ").strip().upper()
        
        if response != "YES":
            print("\n❌ Cleanup cancelled.")
            return
        
        print()
        print("-" * 80)
        print("DELETING DATA...")
        print("-" * 80)
        
        # Delete chunks first (foreign key constraint)
        chunks_deleted_result = await db.execute(
            text("""
                DELETE FROM note_chunks
                WHERE note_id IN (
                    SELECT id FROM notes WHERE user_id = :user_id
                )
            """),
            {"user_id": user.id}
        )
        chunks_deleted = chunks_deleted_result.rowcount
        await db.commit()
        print(f"✅ Deleted {chunks_deleted} chunks")
        
        # Delete notes
        notes_deleted_result = await db.execute(
            delete(Note).where(Note.user_id == user.id)
        )
        notes_deleted = notes_deleted_result.rowcount
        await db.commit()
        print(f"✅ Deleted {notes_deleted} notes")
        
        print()
        print("=" * 80)
        print("✅ CLEANUP COMPLETE!")
        print("=" * 80)
        print()
        print("💡 Next step: Run 'python create_test_data.py' to generate fresh test data.")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
