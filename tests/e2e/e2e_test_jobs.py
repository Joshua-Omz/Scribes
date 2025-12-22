"""
End-to-end test script for the background job system.

This script simulates a user action to test the full workflow:
1. Logs in to get an authentication token.
2. Triggers the embedding regeneration background job.
3. Polls the job status endpoint until the job is complete or fails.
4. Prints the final status and results.
"""
import asyncio
import httpx
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
REGENERATE_URL = f"{BASE_URL}/semantic/regenerate-embeddings"
JOB_STATUS_URL = f"{BASE_URL}/jobs"

# Get user credentials from environment variables
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "password")

# --- Helper Functions ---

async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Authenticate and get a JWT access token."""
    print("1. Authenticating to get access token...")
    try:
        response = await client.post(
            LOGIN_URL,
            data={"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Access token not found in login response.")
        print(f"   ✅ Successfully authenticated. Token received.\n")
        return access_token
    except httpx.HTTPStatusError as e:
        print(f"   ❌ Authentication failed: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"   ❌ An unexpected error occurred during authentication: {e}")
        raise

async def trigger_regeneration(client: httpx.AsyncClient, token: str) -> str:
    """Trigger the embedding regeneration job."""
    print("2. Triggering embedding regeneration job...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = await client.post(REGENERATE_URL, headers=headers, timeout=30)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("task_id")
        if not job_id:
            raise ValueError("Job ID (task_id) not found in regeneration response.")
        print(f"   ✅ Job successfully queued. Job ID: {job_id}\n")
        return job_id
    except httpx.HTTPStatusError as e:
        print(f"   ❌ Failed to trigger job: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"   ❌ An unexpected error occurred while triggering the job: {e}")
        raise

async def poll_job_status(client: httpx.AsyncClient, job_id: str, token: str):
    """Poll the job status endpoint until completion."""
    print(f"3. Polling job status for Job ID: {job_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{JOB_STATUS_URL}/{job_id}"
    
    while True:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            job_status = response.json()
            
            status = job_status.get("status")
            progress = job_status.get("progress_percent", 0)
            processed = job_status.get("processed_items", 0)
            total = job_status.get("total_items", "?")
            
            print(f"   - Status: {status.upper()} | Progress: {progress}% ({processed}/{total})")
            
            if status in ["completed", "failed"]:
                print("\n4. Final Job Status:")
                print(f"   - Job ID: {job_status.get('job_id')}")
                print(f"   - Status: {job_status.get('status').upper()}")
                print(f"   - Started: {job_status.get('started_at')}")
                print(f"   - Completed: {job_status.get('completed_at')}")
                if status == "completed":
                    print(f"   - Result: {job_status.get('result_data')}")
                    print("\n✅ End-to-end test PASSED!")
                else:
                    print(f"   - Error: {job_status.get('error_message')}")
                    print("\n❌ End-to-end test FAILED.")
                break
                
            await asyncio.sleep(5)  # Poll every 5 seconds
            
        except httpx.HTTPStatusError as e:
            print(f"   ❌ Error polling job status: {e.response.status_code} - {e.response.text}")
            break
        except Exception as e:
            print(f"   ❌ An unexpected error occurred while polling: {e}")
            break

async def main():
    """Main function to run the end-to-end test."""
    print("🚀 Starting Background Job End-to-End Test...")
    print("============================================\n")
    
    # Check for credentials
    if not TEST_USER_EMAIL or not TEST_USER_PASSWORD or TEST_USER_EMAIL == "test@example.com":
        print("⚠️  WARNING: Test credentials not found in .env file.")
        print("    Please create a .env file with TEST_USER_EMAIL and TEST_USER_PASSWORD.")
        print("    You can use the credentials from 'login.json'.")
        return

    async with httpx.AsyncClient() as client:
        try:
            token = await get_auth_token(client)
            job_id = await trigger_regeneration(client, token)
            await poll_job_status(client, job_id, token)
        except Exception as e:
            print(f"\n🛑 Test execution stopped due to an error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
