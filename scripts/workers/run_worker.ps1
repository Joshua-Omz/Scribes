# ARQ Worker Startup Script
# Starts the ARQ worker for background task processing

Write-Host "🚀 Starting ARQ Worker..." -ForegroundColor Green
Write-Host ""
Write-Host "Prerequisites:" -ForegroundColor Yellow
Write-Host "  1. Redis server must be running (redis-server)" -ForegroundColor Yellow
Write-Host "  2. Database must be accessible" -ForegroundColor Yellow
Write-Host "  3. Python dependencies must be installed" -ForegroundColor Yellow
Write-Host ""

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Cyan
# This checks if port 6379 (Redis) is open on localhost
$redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet
if ($redisTest -ne "PONG") {
    Write-Host "❌ Redis is not running!" -ForegroundColor Red
    Write-Host "   Please start Redis server first:" -ForegroundColor Yellow
    Write-Host "   - Windows: redis-server.exe" -ForegroundColor Yellow
    Write-Host "   - Linux/Mac: redis-server" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host "✅ Redis is running" -ForegroundColor Green
Write-Host ""

# Start the ARQ worker
Write-Host "Starting ARQ worker..." -ForegroundColor Cyan
Write-Host "Worker will process:" -ForegroundColor Gray
Write-Host "  - Embedding regeneration tasks" -ForegroundColor Gray
Write-Host "  - Reminder scheduling (every 15 minutes)" -ForegroundColor Gray
Write-Host "  - Other background jobs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the worker" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# Run the ARQ worker
try {
    arq app.worker.tasks.WorkerSettings
} catch {
    Write-Host ""
    Write-Host "❌ Failed to start ARQ worker: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure you're in the backend2 directory" -ForegroundColor Yellow
    Write-Host "  2. Activate virtual environment if using one" -ForegroundColor Yellow
    Write-Host "  3. Verify ARQ is installed: pip install arq" -ForegroundColor Yellow
    Write-Host "  4. Check Redis connection in .env file" -ForegroundColor Yellow
    exit 1
}
