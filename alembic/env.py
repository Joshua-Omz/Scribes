"""
Alembic environment configuration for async migrations.
Handles database connection and migration context setup.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the project root directory to Python path
# This allows imports like 'from app.core.config import settings'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the Base and settings
from app.core.config import settings
from app.core.database import Base
# Import all models here to ensure they're registered with Base.metadata
from app.models.base import BaseModel  # noqa: F401
from app.models.user_model import User  # noqa: F401
from app.models.user_profile_model import UserProfile  # noqa: F401
from app.models.note_model import Note  # noqa: F401
from app.models.reminder_model import Reminder  # noqa: F401
from app.models.circle_model import Circle, CircleNote  # noqa: F401
from app.models.cross_ref_model import CrossRef  # noqa: F401
from app.models.annotation_model import Annotation  # noqa: F401
from app.models.export_job_model import ExportJob  # noqa: F401
from app.models.notification_model import Notification  # noqa: F401
from app.models.password_reset_model import PasswordResetToken  # noqa: F401
from app.models.refresh_model import RefreshToken  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with the provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.
    
    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
