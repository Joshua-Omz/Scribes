"""
Quick test to verify background job implementation works.
Tests database models and schemas without requiring Redis.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_job_creation():
    """Test that we can create and query background jobs."""
    print("🧪 Testing Background Job System (Database Only)\n")
    
    from app.core.database import get_db
    from app.models.background_job_model import BackgroundJob
    from app.models.user_model import User
    from sqlalchemy import select
    
    # Get database session
    async for db in get_db():
        try:
            # Get or create a test user
            result = await db.execute(select(User).where(User.email == "test@example.com"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No test user found. Please create a user first via:")
                print("   POST /auth/register with email: test@example.com")
                return False
            
            print(f"✅ Using user: {user.email} (ID: {user.id})\n")
            
            # Test 1: Create a job
            print("Test 1: Creating background job...")
            job = BackgroundJob(
                user_id=user.id,
                job_type="embedding_regeneration",
                total_items=100,
                status="queued"
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Job created: {job.job_id}")
            print(f"     Type: {job.job_type}")
            print(f"     Status: {job.status}")
            print(f"     Progress: {job.progress_percent}%\n")
            
            # Test 2: Update progress
            print("Test 2: Simulating progress updates...")
            job.mark_running()
            await db.commit()
            print(f"  ✅ Job marked as running")
            print(f"     Started at: {job.started_at}\n")
            
            # Simulate processing
            for i in range(0, 101, 25):
                job.update_progress(processed=i, failed=0)
                await db.commit()
                print(f"  📊 Progress: {job.progress_percent}% ({i}/100 processed)")
            
            print()
            
            # Test 3: Mark complete
            print("Test 3: Marking job complete...")
            job.mark_completed(result_data={
                "embeddings_generated": 100,
                "failed_notes": 0
            })
            await db.commit()
            await db.refresh(job)
            
            print(f"  ✅ Job completed!")
            print(f"     Status: {job.status}")
            print(f"     Progress: {job.progress_percent}%")
            print(f"     Completed at: {job.completed_at}")
            print(f"     Result: {job.result_data}\n")
            
            # Test 4: Query the job
            print("Test 4: Querying job by job_id...")
            result = await db.execute(
                select(BackgroundJob).where(BackgroundJob.job_id == job.job_id)
            )
            queried_job = result.scalar_one_or_none()
            
            if queried_job:
                print(f"  ✅ Job found: {queried_job.job_id}")
                print(f"     Status: {queried_job.status}")
                print(f"     Progress: {queried_job.progress_percent}%\n")
            else:
                print(f"  ❌ Job not found!\n")
                return False
            
            print("="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
            print("\nDatabase schema is working correctly.")
            print("Next step: Install Redis and test ARQ worker integration.\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            break


async def test_api_imports():
    """Test that all API routes import correctly."""
    print("\n🧪 Testing API Imports...\n")
    
    try:
        from app.routes.job_routes import router as job_router
        print("  ✅ job_routes imports successfully")
        
        from app.routes.semantic_routes import router as semantic_router
        print("  ✅ semantic_routes imports successfully")
        
        from app.schemas.background_job_schemas import (
            BackgroundJobResponse,
            BackgroundJobStatusResponse,
            JobStatus
        )
        print("  ✅ background_job_schemas imports successfully")
        
        from app.models.background_job_model import BackgroundJob
        print("  ✅ background_job_model imports successfully")
        
        print("\n  ✅ All imports successful!\n")
        return True
        
    except Exception as e:
        print(f"\n  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("="*60)
    print("BACKGROUND JOB SYSTEM - DATABASE TEST")
    print("="*60)
    print()
    
    # Test imports first
    imports_ok = await test_api_imports()
    if not imports_ok:
        print("\n❌ Fix import errors before proceeding.")
        return
    
    # Test database operations
    db_ok = await test_job_creation()
    if not db_ok:
        print("\n❌ Fix database errors before proceeding.")
        return
    
    print("\n📋 Next Steps:")
    print("1. Install Redis: choco install redis-64")
    print("2. Start Redis: redis-server")
    print("3. Start ARQ worker: .\\run_worker.ps1")
    print("4. Start API server: uvicorn app.main:app --reload")
    print("5. Test via Swagger: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    asyncio.run(main())
