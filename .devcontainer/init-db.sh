#!/bin/bash
set -e

# This script runs during PostgreSQL initialization

echo "Initializing Scribes database..."

# Enable pgvector extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE scribes_db TO postgres;
EOSQL

echo "Database initialization complete!"
