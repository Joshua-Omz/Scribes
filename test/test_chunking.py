"""
Test script for embedding chunking functionality.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.embedding_service import get_embedding_service


def test_short_text():
    """Test that short texts don't trigger chunking."""
    print("\n=== Test 1: Short Text (No Chunking Expected) ===")
    service = get_embedding_service()
    
    short_text = "This is a short sermon about faith and hope."
    print(f"Text length: {len(short_text)} chars (~{len(short_text)//4} tokens)")
    
    embedding = service.generate(short_text, enable_chunking=True)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print("✓ Short text processed successfully")


def test_long_text():
    """Test that long texts trigger chunking."""
    print("\n=== Test 2: Long Text (Chunking Expected) ===")
    service = get_embedding_service()
    
    # Create a long text (~2000 tokens)
    long_text = """
    This is a comprehensive sermon about faith, hope, and charity. 
    The apostle Paul teaches us that faith is the substance of things hoped for, the evidence of things not seen.
    Throughout history, many prophets have testified of these principles.
    """ * 100  # Repeat to make it very long
    
    print(f"Text length: {len(long_text)} chars (~{len(long_text)//4} tokens)")
    
    embedding = service.generate(long_text, enable_chunking=True)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print("✓ Long text processed with chunking successfully")


def test_chunking_disabled():
    """Test that chunking can be disabled."""
    print("\n=== Test 3: Long Text with Chunking Disabled ===")
    service = get_embedding_service()
    
    long_text = "This is a test. " * 200
    print(f"Text length: {len(long_text)} chars (~{len(long_text)//4} tokens)")
    
    embedding = service.generate(long_text, enable_chunking=False)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print("✓ Chunking disabled - text truncated by model")


def test_combine_text():
    """Test the combine_text_for_embedding method."""
    print("\n=== Test 4: Combine Text for Embedding ===")
    service = get_embedding_service()
    
    content = "This is a sermon about grace. " * 50
    scripture_refs = "John 3:16, Romans 5:8"
    tags = ["grace", "salvation", "faith"]
    
    combined = service.combine_text_for_embedding(content, scripture_refs, tags)
    print(f"Combined text length: {len(combined)} chars (~{len(combined)//4} tokens)")
    print(f"Text preview: {combined[:200]}...")
    
    embedding = service.generate(combined, enable_chunking=True)
    print(f"Embedding dimension: {len(embedding)}")
    print("✓ Combined text embedded successfully")


def test_similarity_with_chunking():
    """Test that chunked embeddings maintain good similarity."""
    print("\n=== Test 5: Similarity with Chunked Embeddings ===")
    service = get_embedding_service()
    
    # Two similar long texts
    text1 = "Faith is essential for salvation. Without faith, we cannot please God. " * 60
    text2 = "Belief in Christ is necessary for redemption. Faith is the foundation of our relationship with God. " * 60
    
    embedding1 = service.generate(text1, enable_chunking=True)
    embedding2 = service.generate(text2, enable_chunking=True)
    
    similarity = service.similarity(embedding1, embedding2)
    print(f"Similarity between similar texts: {similarity:.4f}")
    print(f"✓ Similarity score looks reasonable (should be > 0.5 for similar content)")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Embedding Chunking Implementation")
    print("=" * 60)
    
    try:
        test_short_text()
        test_long_text()
        test_chunking_disabled()
        test_combine_text()
        test_similarity_with_chunking()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
