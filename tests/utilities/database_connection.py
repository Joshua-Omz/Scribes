"""
Database Connection Testing Script for Scribes Backend

This script tests your PostgreSQL connection and verifies:
1. Database connectivity
2. Database existence
3. Table creation
4. Basic CRUD operations
5. Migration status

Usage:
    python test_db_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base
from app.models.user_model import User
from app.core.security import get_password_hash


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}{Colors.END}\n")


async def test_basic_connection():
    """Test 1: Basic database connection"""
    print_header("Test 1: Basic Database Connection")
    
    try:
        # Create engine with pool settings
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print_success(f"Connected to PostgreSQL")
            print_info(f"Version: {version}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


async def test_database_exists():
    """Test 2: Verify database exists"""
    print_header("Test 2: Database Existence Check")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT current_database();"))
            db_name = result.scalar()
            print_success(f"Database exists: {db_name}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"Database check failed: {str(e)}")
        return False


async def test_table_creation():
    """Test 3: Create tables using SQLAlchemy"""
    print_header("Test 3: Table Creation Test")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False
        )
        
        # Drop and recreate tables
        async with engine.begin() as conn:
            print_info("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print_success("Tables dropped")
            
            print_info("Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)
            print_success("Tables created")
            
            # List created tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            print_info(f"Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table[0]}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"Table creation failed: {str(e)}")
        return False


async def test_crud_operations():
    """Test 4: Basic CRUD operations"""
    print_header("Test 4: CRUD Operations Test")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False
        )
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # CREATE
            print_info("Creating test user...")
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("Test1234!"),
                full_name="Test User",
                role="user",
                is_active=True,
                is_verified=False
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            print_success(f"User created with ID: {test_user.id}")
            
            # READ
            print_info("Reading user from database...")
            result = await session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": "test@example.com"}
            )
            user_row = result.fetchone()
            if user_row:
                print_success(f"User found: {user_row.username}")
            
            # UPDATE
            print_info("Updating user...")
            test_user.full_name = "Updated Test User"
            await session.commit()
            print_success("User updated")
            
            # DELETE
            print_info("Deleting user...")
            await session.delete(test_user)
            await session.commit()
            print_success("User deleted")
            
            # Verify deletion
            result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE email = :email"),
                {"email": "test@example.com"}
            )
            count = result.scalar()
            if count == 0:
                print_success("Deletion verified")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"CRUD operations failed: {str(e)}")
        return False


async def test_alembic_migrations():
    """Test 5: Check Alembic migration status"""
    print_header("Test 5: Migration Status Check")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False
        )
        
        async with engine.begin() as conn:
            # Check if alembic_version table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                );
            """))
            exists = result.scalar()
            
            if exists:
                # Get current version
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version;")
                )
                version = result.scalar()
                if version:
                    print_success(f"Alembic is initialized")
                    print_info(f"Current migration: {version}")
                else:
                    print_warning("Alembic table exists but no migrations applied")
            else:
                print_warning("Alembic not initialized")
                print_info("Run: alembic upgrade head")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"Migration check failed: {str(e)}")
        return False


async def test_connection_pool():
    """Test 6: Connection pool behavior"""
    print_header("Test 6: Connection Pool Test")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        
        print_info("Opening 10 concurrent connections...")
        
        async def test_query(session_num: int):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1;"))
                return session_num
        
        # Create 10 concurrent connections
        tasks = [test_query(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        print_success(f"All {len(results)} connections succeeded")
        print_info(f"Pool size: {engine.pool.size()}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print_error(f"Connection pool test failed: {str(e)}")
        return False


async def print_database_info():
    """Print detailed database information"""
    print_header("Database Configuration")
    
    print(f"{Colors.BOLD}Environment Settings:{Colors.END}")
    print(f"  Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
    print(f"  Project Name: {settings.PROJECT_NAME}")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug Mode: {settings.DEBUG}")
    
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False
        )
        
        async with engine.begin() as conn:
            # Get database info
            result = await conn.execute(text("""
                SELECT 
                    current_database() as db_name,
                    current_user as db_user,
                    inet_server_addr() as server_addr,
                    inet_server_port() as server_port,
                    version() as version;
            """))
            info = result.fetchone()
            
            print(f"\n{Colors.BOLD}Database Information:{Colors.END}")
            print(f"  Database: {info.db_name}")
            print(f"  User: {info.db_user}")
            print(f"  Server: {info.server_addr}:{info.server_port}")
            
            # Get table count
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """))
            table_count = result.scalar()
            print(f"  Tables: {table_count}")
            
            # Get database size
            result = await conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """))
            db_size = result.scalar()
            print(f"  Size: {db_size}")
        
        await engine.dispose()
        
    except Exception as e:
        print_error(f"Could not fetch database info: {str(e)}")


async def main():
    """Run all database tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║          Scribes Backend - Database Test Suite            ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    # Print database configuration
    await print_database_info()
    
    # Run all tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Database Exists", test_database_exists),
        ("Table Creation", test_table_creation),
        ("CRUD Operations", test_crud_operations),
        ("Migration Status", test_alembic_migrations),
        ("Connection Pool", test_connection_pool),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.END}" if result else f"{Colors.RED}FAILED{Colors.END}"
        print(f"  {test_name:<25} {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed! Your database is ready.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Check the errors above.{Colors.END}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)