"""
Test script for background job tracking system.
Tests Phase 1 implementation with database-backed job tracking.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import get_db
from app.models.background_job_model import BackgroundJob
from app.models.user_model import User


async def test_background_job_tracking():
    """Test background job model and helper methods."""
    
    print("🧪 Testing Background Job Tracking System\n")
    
    async for db in get_db():
        try:
            # Get a test user
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No users found. Please create a user first.")
                return
            
            print(f"✅ Using test user: {user.email} (ID: {user.id})\n")
            
            # Test 1: Create a job
            print("Test 1: Creating a background job...")
            job = BackgroundJob(
                user_id=user.id,
                job_type="test_job",
                total_items=100
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Job created: {job.job_id}")
            print(f"     Status: {job.status}")
            print(f"     Progress: {job.progress_percent}%\n")
            
            # Test 2: Mark as running
            print("Test 2: Marking job as running...")
            job.mark_running()
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Job status: {job.status}")
            print(f"     Started at: {job.started_at}\n")
            
            # Test 3: Update progress
            print("Test 3: Updating progress...")
            job.update_progress(processed=50, failed=2)
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Progress: {job.progress_percent}%")
            print(f"     Processed: {job.processed_items}/{job.total_items}")
            print(f"     Failed: {job.failed_items}\n")
            
            # Test 4: Mark as completed
            print("Test 4: Marking job as completed...")
            job.mark_completed(result_data={"items_processed": 98, "items_failed": 2})
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Job status: {job.status}")
            print(f"     Progress: {job.progress_percent}%")
            print(f"     Completed at: {job.completed_at}")
            print(f"     Result data: {job.result_data}\n")
            
            # Test 5: Create a failed job
            print("Test 5: Creating a failed job...")
            failed_job = BackgroundJob(
                user_id=user.id,
                job_type="test_failed_job",
                total_items=50
            )
            db.add(failed_job)
            await db.commit()
            await db.refresh(failed_job)
            
            failed_job.mark_running()
            failed_job.update_progress(processed=25, failed=5)
            failed_job.mark_failed("Test error: Something went wrong")
            await db.commit()
            await db.refresh(failed_job)
            
            print(f"  ✅ Failed job created: {failed_job.job_id}")
            print(f"     Status: {failed_job.status}")
            print(f"     Error: {failed_job.error_message}\n")
            
            # Test 6: Query jobs
            print("Test 6: Querying user's jobs...")
            result = await db.execute(
                select(BackgroundJob)
                .where(BackgroundJob.user_id == user.id)
                .order_by(BackgroundJob.created_at.desc())
            )
            jobs = result.scalars().all()
            
            print(f"  ✅ Found {len(jobs)} jobs for user {user.id}:")
            for j in jobs:
                print(f"     - {j.job_id}: {j.job_type} ({j.status}) - {j.progress_percent}%")
            
            print("\n" + "="*60)
            print("✅ All tests passed! Background job tracking system working.")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        break


if __name__ == "__main__":
    asyncio.run(test_background_job_tracking())
