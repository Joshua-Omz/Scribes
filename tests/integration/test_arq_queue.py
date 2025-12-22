"""
Quick test to verify ARQ job enqueuing works correctly.
This script tests the Redis queue integration without needing full authentication.
"""
import asyncio
from arq import create_pool
from arq.connections import RedisSettings

async def test_queue():
    """Test enqueuing a job to the ARQ queue."""
    print("🧪 Testing ARQ job enqueuing...\n")
    
    # Connect to Redis
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    redis = await create_pool(redis_settings)
    
    try:
        # Enqueue a test job with the correct queue name
        job = await redis.enqueue_job(
            'regenerate_embeddings_arq',
            1,  # user_id
            'test-job-id-123',  # job_id
            _queue_name="scribes:queue"  # Must match WorkerSettings.queue_name
        )
        
        if job:
            print(f"✅ Job enqueued successfully!")
            print(f"   Job ID: {job.job_id}")
            print(f"   Queue: scribes:queue")
            print(f"\n📊 Now check the ARQ worker terminal - it should pick up this job!")
        else:
            print("❌ Failed to enqueue job - job is None")
            
    except Exception as e:
        print(f"❌ Error enqueuing job: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await redis.close()
        print("\n🔌 Redis connection closed")

if __name__ == "__main__":
    asyncio.run(test_queue())
