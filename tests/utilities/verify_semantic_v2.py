"""
Quick verification test for Semantic Search V2 implementation.
Run this to verify the refactored system works correctly.
"""

import asyncio
from app.services.embedding_service import get_embedding_service, EmbeddingGenerationError


async def test_embedding_service():
    """Test the enhanced embedding service with retry logic."""
    print("\n=== Testing Embedding Service ===")
    
    service = get_embedding_service()
    
    # Test 1: Generate embedding with all fields
    print("\n1. Testing embedding generation with all fields...")
    text = service.combine_text_for_embedding(
        content="This is a test sermon about faith and grace",
        title="Test Sermon",
        preacher="John Doe",
        scripture_refs="John 3:16, Romans 5:8",
        tags=["faith", "grace", "salvation"]
    )
    print(f"   Combined text: {text[:100]}...")
    
    try:
        embedding = service.generate(text)
        print(f"   ✅ Generated embedding: {len(embedding)} dimensions")
        assert len(embedding) == 1536, "Embedding should be 1536 dimensions"
        assert not all(v == 0 for v in embedding), "Embedding should not be all zeros"
    except EmbeddingGenerationError as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Test model info
    print("\n2. Testing model info...")
    info = service.get_model_info()
    print(f"   Model: {info['model_name']}")
    print(f"   Native dimension: {info['embedding_dimension']}")
    print(f"   Target dimension: {info['target_dimension']}")
    print(f"   Padding used: {info['padding_used']}")
    
    # Test 3: Test empty text handling
    print("\n3. Testing empty text handling...")
    try:
        service.generate("")
        print("   ❌ Should have raised EmbeddingGenerationError")
        return False
    except EmbeddingGenerationError:
        print("   ✅ Correctly raises error for empty text")
    
    print("\n✅ All embedding service tests passed!")
    return True


def test_event_registration():
    """Test that event listeners are properly structured."""
    print("\n=== Testing Event Listeners ===")
    
    from app.models.events import register_note_events
    
    print("\n1. Testing event registration...")
    try:
        register_note_events()
        print("   ✅ Event listeners registered successfully")
    except Exception as e:
        print(f"   ❌ Failed to register events: {e}")
        return False
    
    print("\n✅ Event listener tests passed!")
    return True


def test_migration_file():
    """Test that migration file is properly formatted."""
    print("\n=== Testing Migration File ===")
    
    print("\n1. Checking migration file exists...")
    import os
    migration_path = "c:\\flutter proj\\Scribes\\backend2\\alembic\\versions\\2025-11-09_70c020ced272_add_hnsw_index_for_embeddings.py"
    
    if os.path.exists(migration_path):
        print("   ✅ Migration file exists")
        
        # Check content
        with open(migration_path, 'r') as f:
            content = f.read()
            
        print("\n2. Checking migration content...")
        checks = [
            ("CREATE INDEX", "Contains CREATE INDEX command"),
            ("idx_notes_embedding_hnsw", "Has correct index name"),
            ("USING hnsw", "Uses HNSW index type"),
            ("vector_cosine_ops", "Uses cosine distance operator"),
            ("DROP INDEX", "Has downgrade function")
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
                all_passed = False
        
        if all_passed:
            print("\n✅ Migration file tests passed!")
            return True
        else:
            return False
    else:
        print("   ❌ Migration file not found")
        return False


def test_dependencies():
    """Test that all required dependencies are installed."""
    print("\n=== Testing Dependencies ===")
    
    dependencies = {
        "tenacity": "8.2.3",
        "sentence_transformers": "5.1.2",
        "pgvector": "0.2.5",
        "fastapi": "0.109.0",
        "sqlalchemy": "2.0.25"
    }
    
    all_installed = True
    for package, expected_version in dependencies.items():
        try:
            if package == "sentence_transformers":
                import sentence_transformers
                version = sentence_transformers.__version__
            elif package == "tenacity":
                import tenacity
                version = tenacity.__version__
            elif package == "pgvector":
                import pgvector
                version = pgvector.__version__
            elif package == "fastapi":
                import fastapi
                version = fastapi.__version__
            elif package == "sqlalchemy":
                import sqlalchemy
                version = sqlalchemy.__version__
            
            if version >= expected_version:
                print(f"   ✅ {package}: {version} (>= {expected_version})")
            else:
                print(f"   ⚠️  {package}: {version} (expected >= {expected_version})")
                all_installed = False
        except ImportError:
            print(f"   ❌ {package}: Not installed")
            all_installed = False
    
    if all_installed:
        print("\n✅ All dependencies installed!")
    else:
        print("\n⚠️  Some dependencies missing or outdated")
    
    return all_installed


def test_file_structure():
    """Test that all new files exist."""
    print("\n=== Testing File Structure ===")
    
    files = [
        ("app/models/events.py", "Event listeners"),
        ("app/api/semantic_routes_v2.py", "Semantic routes V2"),
        ("docs/guides/SEMANTIC_SEARCH_V2_IMPLEMENTATION.md", "Implementation guide"),
        ("docs/guides/DEPLOYMENT_CHECKLIST_V2.md", "Deployment checklist"),
        ("docs/guides/IMPLEMENTATION_SUMMARY.md", "Implementation summary")
    ]
    
    import os
    all_exist = True
    base_path = "c:\\flutter proj\\Scribes\\backend2\\"
    
    for file_path, description in files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"   ✅ {description}: {size:,} bytes")
        else:
            print(f"   ❌ Missing: {description}")
            all_exist = False
    
    if all_exist:
        print("\n✅ All files exist!")
    else:
        print("\n❌ Some files missing")
    
    return all_exist


def main():
    """Run all verification tests."""
    print("="*60)
    print("SEMANTIC SEARCH V2 - VERIFICATION TESTS")
    print("="*60)
    
    results = {
        "Dependencies": test_dependencies(),
        "File Structure": test_file_structure(),
        "Migration File": test_migration_file(),
        "Event Listeners": test_event_registration(),
        "Embedding Service": asyncio.run(test_embedding_service())
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ABOVE")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
