"""ARQ Background Tasks.

This module defines all background tasks that run in the ARQ worker:
- Embedding regeneration
- Reminder scheduling and sending
- Export generation
- Other async operations
"""
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from arq import cron

from app.core.config import settings
from app.models.background_job_model import BackgroundJob
from app.models.note_model import Note
from app.models.reminder_model import Reminder
from app.models.user_model import User
from app.services.embedding_service import get_embedding_service, EmbeddingGenerationError

logger = logging.getLogger(__name__)

# Create async database engine for worker
worker_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    worker_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_worker_db() -> AsyncSession:
    """Get database session for worker tasks."""
    async with AsyncSessionLocal() as session:
        return session


# ============================================================================
# Embedding Regeneration Task
# ============================================================================

async def regenerate_embeddings_arq(ctx, user_id: int, job_id: str):
    """
    ARQ task to regenerate embeddings for all user notes.
    
    This is the ARQ-compatible version of regenerate_embeddings_task.
    Processes notes in batches and updates job progress in database.
    
    Args:
        ctx: ARQ context (provides access to Redis, job info, etc.)
        user_id: User ID whose notes to regenerate
        job_id: Background job UUID for tracking progress
        
    Returns:
        dict: Result data with summary statistics
    """
    job_uuid = UUID(job_id)
    batch_size = 100
    offset = 0
    total_processed = 0
    total_failed = 0
    
    embedding_service = get_embedding_service()
    
    logger.info(f"[ARQ] Starting embedding regeneration task for user {user_id}, job {job_id}")
    
    db = await get_worker_db()
    
    try:
        # Get the job record
        result = await db.execute(
            select(BackgroundJob).where(BackgroundJob.job_id == job_uuid)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"[ARQ] Job {job_id} not found for user {user_id}")
            return {"error": "Job not found"}
        
        # Mark job as running
        job.mark_running()
        await db.commit()
        
        # Count total notes to process
        count_result = await db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        total_notes = count_result.scalar()
        job.total_items = total_notes
        await db.commit()
        
        logger.info(f"[ARQ] Processing {total_notes} notes for user {user_id}")
        
        # Process notes in batches
        while True:
            # Fetch notes batch
            result = await db.execute(
                select(Note)
                .where(Note.user_id == user_id)
                .offset(offset)
                .limit(batch_size)
            )
            notes = result.scalars().all()
            
            if not notes:
                break  # No more notes
            
            # Process each note
            for note in notes:
                try:
                    if not note.content or not note.content.strip():
                        continue
                    
                    # Generate embedding
                    combined_text = embedding_service.combine_text_for_embedding(
                        content=note.content,
                        scripture_refs=note.scripture_refs,
                        tags=note.tags.split(',') if note.tags else None
                    )
                    
                    # Use generate_with_chunking for long notes
                    embedding = embedding_service.generate_with_chunking(combined_text)
                    note.embedding = embedding
                    total_processed += 1
                    
                except EmbeddingGenerationError as e:
                    logger.error(f"[ARQ] Failed to generate embedding for note {note.id}: {e}")
                    total_failed += 1
                except Exception as e:
                    logger.error(f"[ARQ] Unexpected error for note {note.id}: {e}", exc_info=True)
                    total_failed += 1
            
            # Commit batch and update progress
            await db.commit()
            
            # Refresh job to get latest state
            await db.refresh(job)
            job.update_progress(total_processed, total_failed)
            await db.commit()
            
            logger.info(f"[ARQ] Batch complete: {total_processed}/{total_notes} processed, " +
                       f"{total_failed} failed, {job.progress_percent}% done")
            
            offset += batch_size
        
        # Mark job as completed
        result_data = {
            "embeddings_generated": total_processed,
            "failed_notes": total_failed,
            "total_notes": total_notes,
            "completion_time": datetime.now(timezone.utc).isoformat()
        }
        
        job.mark_completed(result_data=result_data)
        await db.commit()
        
        logger.info(f"[ARQ] Embedding regeneration complete for job {job_id}: " +
                   f"{total_processed} succeeded, {total_failed} failed")
        
        return result_data
        
    except Exception as e:
        logger.error(f"[ARQ] Fatal error in embedding regeneration job {job_id}: {e}", exc_info=True)
        
        # Mark job as failed
        try:
            if job:
                job.mark_failed(str(e))
                await db.commit()
        except Exception as commit_error:
            logger.error(f"[ARQ] Failed to mark job as failed: {commit_error}")
        
        return {"error": str(e)}
    
    finally:
        await db.close()


# ============================================================================
# Reminder Scheduling Task
# ============================================================================

async def check_and_send_reminders(ctx):
    """
    ARQ cron task to check for due reminders and send them.
    
    Runs periodically (every 15 minutes by default) to:
    1. Query reminders WHERE scheduled_at <= now() AND status='pending'
    2. Send notifications/emails for each reminder
    3. Update status to 'sent'
    
    Args:
        ctx: ARQ context
        
    Returns:
        dict: Summary of reminders processed
    """
    logger.info("[ARQ CRON] Checking for due reminders...")
    
    db = await get_worker_db()
    sent_count = 0
    failed_count = 0
    
    try:
        # Query due reminders
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Reminder)
            .where(
                Reminder.scheduled_at <= now,
                Reminder.status == "pending"
            )
            .limit(100)  # Process max 100 per run
        )
        due_reminders = result.scalars().all()
        
        if not due_reminders:
            logger.info("[ARQ CRON] No due reminders found")
            return {"sent": 0, "failed": 0}
        
        logger.info(f"[ARQ CRON] Found {len(due_reminders)} due reminders")
        
        # Process each reminder
        for reminder in due_reminders:
            try:
                # TODO: Implement actual notification sending
                # For now, just mark as sent
                # Future: Send email, push notification, in-app notification
                
                logger.info(f"[ARQ CRON] Sending reminder {reminder.id} for note {reminder.note_id} to user {reminder.user_id}")
                
                # Update status to sent
                reminder.status = "sent"
                sent_count += 1
                
            except Exception as e:
                logger.error(f"[ARQ CRON] Failed to send reminder {reminder.id}: {e}", exc_info=True)
                failed_count += 1
        
        # Commit all updates
        await db.commit()
        
        logger.info(f"[ARQ CRON] Reminder processing complete: {sent_count} sent, {failed_count} failed")
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ARQ CRON] Fatal error in reminder checking: {e}", exc_info=True)
        return {"error": str(e)}
    
    finally:
        await db.close()


# ============================================================================
# Worker Configuration - Register Tasks
# ============================================================================

# Import WorkerSettings to register tasks
from app.worker.arq_config import WorkerSettings

# Register task functions
WorkerSettings.functions = [
    regenerate_embeddings_arq,
]

# Register cron jobs (every 15 minutes)
WorkerSettings.cron_jobs = [
    cron(check_and_send_reminders, minute={0, 15, 30, 45}, run_at_startup=True)
]

logger.info("✅ ARQ tasks registered: regenerate_embeddings_arq, check_and_send_reminders")
