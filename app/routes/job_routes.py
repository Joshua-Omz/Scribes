"""Background job routes for querying task status and progress.

This module provides endpoints for tracking async background jobs.
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user_model import User
from app.models.background_job_model import BackgroundJob
from app.schemas.background_job_schemas import (
    BackgroundJobResponse,
    BackgroundJobListResponse,
    BackgroundJobStatusResponse,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])


@router.get("/{job_id}", response_model=BackgroundJobResponse)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the status and progress of a background job.
    
    This endpoint allows users to check:
    - Current status (queued, running, completed, failed)
    - Progress percentage (0-100)
    - Items processed and failed
    - Error messages if failed
    - Result data if completed
    
    Args:
        job_id: Unique job identifier (UUID)
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BackgroundJobResponse with complete job details
        
    Raises:
        404: Job not found or doesn't belong to user
    """
    try:
        # Query for the job
        result = await db.execute(
            select(BackgroundJob)
            .where(
                BackgroundJob.job_id == job_id,
                BackgroundJob.user_id == current_user.id
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or access denied"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job status: {str(e)}"
        )


@router.get("/{job_id}/status", response_model=BackgroundJobStatusResponse)
async def get_job_simple_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a simplified status summary of a background job.
    
    This is a lighter endpoint that returns just the essential status info:
    - Job ID
    - Status
    - Progress percentage
    - Human-readable message
    
    Args:
        job_id: Unique job identifier (UUID)
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BackgroundJobStatusResponse with simplified status
        
    Raises:
        404: Job not found or doesn't belong to user
    """
    try:
        # Query for the job
        result = await db.execute(
            select(BackgroundJob)
            .where(
                BackgroundJob.job_id == job_id,
                BackgroundJob.user_id == current_user.id
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or access denied"
            )
        
        # Build human-readable message
        if job.status == "queued":
            message = "Job is queued and will start soon"
        elif job.status == "running":
            if job.total_items:
                message = f"Processing: {job.processed_items}/{job.total_items} completed"
                if job.failed_items > 0:
                    message += f", {job.failed_items} failed"
            else:
                message = f"Processing: {job.processed_items} items completed"
        elif job.status == "completed":
            message = f"Job completed successfully"
            if job.total_items:
                message += f": {job.processed_items} items processed"
                if job.failed_items > 0:
                    message += f", {job.failed_items} failed"
        elif job.status == "failed":
            message = f"Job failed: {job.error_message or 'Unknown error'}"
        elif job.status == "cancelled":
            message = "Job was cancelled"
        else:
            message = f"Job status: {job.status}"
        
        return BackgroundJobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            progress_percent=job.progress_percent or 0,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job status: {str(e)}"
        )


@router.get("", response_model=BackgroundJobListResponse)
async def list_user_jobs(
    limit: int = Query(20, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all background jobs for the current user.
    
    This endpoint supports:
    - Pagination via limit/offset
    - Filtering by job type (embedding_regeneration, export, etc.)
    - Filtering by status (queued, running, completed, failed)
    - Ordered by creation date (newest first)
    
    Args:
        limit: Maximum number of jobs to return (1-100)
        offset: Number of jobs to skip for pagination
        job_type: Optional filter by job type
        status: Optional filter by status
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BackgroundJobListResponse with list of jobs and total count
    """
    try:
        # Build base query
        query = select(BackgroundJob).where(BackgroundJob.user_id == current_user.id)
        
        # Apply filters
        if job_type:
            query = query.where(BackgroundJob.job_type == job_type)
        if status:
            query = query.where(BackgroundJob.status == status)
        
        # Get total count
        count_result = await db.execute(
            select(BackgroundJob.id).where(BackgroundJob.user_id == current_user.id)
        )
        total = len(count_result.all())
        
        # Apply ordering and pagination
        query = query.order_by(desc(BackgroundJob.created_at)).offset(offset).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return BackgroundJobListResponse(
            jobs=jobs,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )
