"""ARQ Worker Configuration.

This module configures the ARQ worker with Redis connection settings,
task functions, cron jobs, and worker behavior.
"""
from arq.connections import RedisSettings
from arq import cron

from app.core.config import settings


async def startup(ctx):
    """Worker startup hook - runs once when worker starts."""
    print("🚀 ARQ Worker starting up...")
    print(f"📍 Redis URL: {settings.redis_url}")
    print(f"⚙️  Max jobs: {settings.arq_max_jobs}")
    print(f"⏱️  Job timeout: {settings.arq_job_timeout}s")


async def shutdown(ctx):
    """Worker shutdown hook - runs when worker stops."""
    print("🛑 ARQ Worker shutting down...")


class WorkerSettings:
    """ARQ Worker Settings Configuration."""
    
    # Parse Redis URL
    redis_url_parts = settings.redis_url.replace("redis://", "").split(":")
    redis_host = redis_url_parts[0] if redis_url_parts else "localhost"
    redis_port = int(redis_url_parts[1]) if len(redis_url_parts) > 1 else 6379
    
    # Redis connection settings
    redis_settings = RedisSettings(
        host=redis_host,
        port=redis_port,
        database=0
    )
    
    # Task functions (imported dynamically to avoid circular imports)
    functions = []  # Will be populated by tasks.py
    
    # Cron jobs for scheduled tasks
    cron_jobs = []  # Will be populated by tasks.py
    
    # Worker behavior
    max_jobs = settings.arq_max_jobs
    job_timeout = settings.arq_job_timeout
    keep_result = settings.arq_keep_result
    
    # Polling interval for checking for new jobs (milliseconds)
    poll_delay = 500  # 0.5 seconds
    
    # Worker lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown
    
    # Queue name
    queue_name = "scribes:queue"
