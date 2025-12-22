# Dev Container Setup for Scribes Backend

This dev container provides a complete development environment for the Scribes backend project.

## What's Included

### Services
- **Python 3.11** - Main application runtime
- **PostgreSQL 16 with pgvector** - Database with vector extension for embeddings
- **Redis 7** - Cache and background job queue

### VS Code Extensions
- Python language support (Pylance)
- Black formatter
- isort for import organization
- Flake8 linting
- Docker tools
- GitLens
- GitHub Copilot (if you have access)

### Pre-installed Tools
- Git & GitHub CLI
- PostgreSQL client tools
- IPython & ipdb for debugging
- pre-commit hooks

## Getting Started

### Prerequisites
- Docker Desktop installed and running
- VS Code with "Dev Containers" extension installed

### Opening the Project

1. Open VS Code
2. Open the `backend2` folder
3. When prompted, click "Reopen in Container" (or use Command Palette: `Dev Containers: Reopen in Container`)
4. Wait for the container to build (first time will take a few minutes)

### After Container Starts

1. **Verify database connection:**
   ```bash
   psql postgresql://postgres:postgres@localhost:5432/scribes_db -c "\dx"
   ```
   You should see the `vector` extension listed.

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Create test data (optional):**
   ```bash
   python create_test_data.py
   ```

4. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Database Management

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost:5432/scribes_db

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Redis Management

```bash
# Connect to Redis CLI
redis-cli

# Monitor Redis commands in real-time
redis-cli monitor

# Check Redis connection
redis-cli ping  # Should return "PONG"

# View rate limiting keys
redis-cli KEYS "ratelimit:*"

# Check specific user's rate limit
redis-cli ZCARD ratelimit:user:1:minute

# Check user's daily cost
redis-cli GET ratelimit:cost:user:1:daily

# Clear all rate limiting data (dev only!)
redis-cli KEYS "ratelimit:*" | xargs redis-cli DEL

# Flush all data (careful!)
redis-cli FLUSHALL
```

### Production Features Testing

#### Rate Limiting

```bash
# Check rate limiter health
curl http://localhost:8000/api/v1/assistant/health

# Get your rate limit stats (requires auth token)
curl http://localhost:8000/api/v1/assistant/stats \
     -H "Authorization: Bearer YOUR_TOKEN"

# Test rate limiting by sending 11 requests rapidly
# (Limit is 10/minute, so 11th should return 429)
for i in {1..11}; do
    curl -X POST http://localhost:8000/api/v1/assistant/query \
         -H "Authorization: Bearer YOUR_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"query":"test"}' &
done
wait
```

#### Response Caching (Coming Soon)

```bash
# Once caching is implemented:
# First request: uncached (~3-5s)
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is grace?"}'

# Second request: cached (<1s)
time curl -X POST http://localhost:8000/api/v1/assistant/query \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"What is grace?"}'
```

#### Metrics (Coming Soon)

```bash
# Once Prometheus metrics are implemented:
curl http://localhost:8000/metrics
```

### Background Workers

```bash
# Start ARQ worker
arq app.worker.arq_config.WorkerSettings
```

## Environment Variables

Default environment variables are set in `.env.devcontainer`. To customize:

1. Copy `.env.devcontainer` to `../.env` (in the project root)
2. Update values as needed
3. Add your HuggingFace API key to `HUGGINGFACE_API_KEY`
4. Rebuild the container if needed

### Production Features Configuration

The dev container includes all production features:

✅ **Rate Limiting** - Enabled by default
- `RATE_LIMITING_ENABLED=true`
- Per-user limits: 10/min, 100/hour, 500/day
- Cost limits: $5/day per user, $100/day global
- See `docs/RATE_LIMITING_IMPLEMENTATION.md` for details

⏳ **Response Caching** - Coming soon (Phase 2)
- Will reduce API costs by 60-80%
- Target: <1s cached response time

⏳ **Observability Metrics** - Coming soon (Phase 3)
- Prometheus metrics endpoint
- Grafana dashboards
- Real-time monitoring

⏳ **Circuit Breakers** - Coming soon (Phase 4)
- HuggingFace API fault tolerance
- Automatic recovery

**Documentation:**
- Quick Start: `docs/PRODUCTION_FEATURES_QUICK_START.md`
- Full Progress: `docs/PRODUCTION_INFRASTRUCTURE_PROGRESS.md`

## Tips

### Code Formatting
Code is automatically formatted on save using Black and isort.

### Debugging
- Set breakpoints in VS Code
- Use the Debug panel to start the FastAPI debugger
- Or use `ipdb` by adding `import ipdb; ipdb.set_trace()` in your code

### Database GUI
You can connect to the PostgreSQL database using any database client:
- Host: localhost
- Port: 5432
- User: postgres
- Password: postgres
- Database: scribes_db

Recommended tools:
- DBeaver
- pgAdmin
- TablePlus

## Troubleshooting

### Container won't start
```bash
# Rebuild container
Dev Containers: Rebuild Container

# Check Docker logs
docker-compose -f .devcontainer/docker-compose.yml logs
```

### Database connection issues
```bash
# Check if PostgreSQL is running
docker-compose -f .devcontainer/docker-compose.yml ps

# Restart services
docker-compose -f .devcontainer/docker-compose.yml restart
```

### Port already in use
Stop any local services running on ports 8000, 5432, or 6379, then rebuild the container.

## Updating Dependencies

When `requirements.txt` changes:

```bash
# Inside the container
pip install -r requirements.txt
```

Or rebuild the container to ensure a clean state.

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
