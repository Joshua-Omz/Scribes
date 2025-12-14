"""
Manual Test Script - Scenario 3.1: Query with Relevant Context

This script runs a manual test of the AssistantService RAG pipeline for a query
that should have relevant context in the test notes created by
`scripts/testing/create_test_data.py`.

Usage (PowerShell):
    python .\scripts\testing\test_scenario_3_1_query_with_context.py

What it does:
- Connects to the database using `AsyncSessionLocal`
- Looks up an existing test user (by email or falls back to id=1)
- Calls the AssistantService.query(...) with a sample question that should
  return context from the sermon notes (e.g. about "grace")
- Prints answer, sources and metadata

Note: This is a manual validation helper. Make sure the DB has test data
and HF_API_KEY is configured if the textgen service is enabled.
"""

import sys
import asyncio
from pathlib import Path
import json

# Ensure project root is on sys.path so imports work when executed from repo root
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.user_model import User
from app.services.assistant_service import get_assistant_service


async def main():
    query = "What is grace according to the sermon notes?"

    async with AsyncSessionLocal() as db:  # type: AsyncSession
        # Try to find a test user by well-known test email
        result = await db.execute(select(User).where(User.email == "test@scribesapp.com"))
        user = result.scalars().first()

        if user is None:
            # Fall back to user id = 1
            print("Test user with email 'test@scribesapp.com' not found. Falling back to user_id=1.")
            user_id = 1
        else:
            user_id = user.id
            print(f"Using test user id: {user_id} (email={user.email})")

        assistant = get_assistant_service()

        print("Running AssistantService.query() with sample query...")
        response = await assistant.query(
            user_query=query,
            user_id=user_id,
            db=db,
            max_sources=5,
            include_metadata=True,
        )

        # Pretty-print results
        print("\n=== Assistant Response ===")
        print("Answer:\n", response.get("answer"))
        print("\nSources:\n", json.dumps(response.get("sources"), indent=2, default=str))
        print("\nMetadata:\n", json.dumps(response.get("metadata"), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
