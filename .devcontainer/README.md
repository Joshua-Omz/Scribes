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

# Monitor Redis commands
redis-cli monitor

# Flush all data (careful!)
redis-cli FLUSHALL
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
3. Rebuild the container if needed

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
