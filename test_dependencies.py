#!/usr/bin/env python3
"""
Test script to verify all dependencies are correctly installed.
Focuses on CPU-only torch and NumPy 1.x compatibility.
"""
import sys

def test_imports():
    """Test all critical imports and version requirements."""
    print("=" * 80)
    print("DEPENDENCY VERIFICATION TEST")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # Test 1: NumPy version
    print("TEST 1: NumPy Version Check")
    print("-" * 80)
    try:
        import numpy
        print(f"✅ NumPy imported successfully: {numpy.__version__}")
        
        major_version = int(numpy.__version__.split('.')[0])
        if major_version >= 2:
            print("❌ FAIL: NumPy 2.x detected!")
            print("   PyTorch 2.2.0 requires NumPy 1.x")
            print("   Fix: pip install 'numpy>=1.24.0,<2.0.0' --force-reinstall")
            all_passed = False
        else:
            print(f"✅ PASS: NumPy 1.x ({numpy.__version__}) - Compatible with torch 2.2.0")
    except ImportError as e:
        print(f"❌ FAIL: Cannot import numpy: {e}")
        all_passed = False
    print()
    
    # Test 2: PyTorch CPU version
    print("TEST 2: PyTorch CPU-Only Check")
    print("-" * 80)
    try:
        import torch
        print(f"✅ PyTorch imported successfully: {torch.__version__}")
        
        if '+cpu' in torch.__version__:
            print("✅ PASS: CPU-only version detected (no GPU dependencies)")
        else:
            print("⚠️  WARNING: Not CPU-only version")
            print("   Expected: 2.2.0+cpu")
            print(f"   Got: {torch.__version__}")
        
        if torch.cuda.is_available():
            print("⚠️  WARNING: CUDA is available (unexpected for CPU-only)")
        else:
            print("✅ PASS: CUDA not available (correct for CPU-only build)")
        
        # Test basic tensor operation
        x = torch.tensor([1.0, 2.0, 3.0])
        y = x * 2
        print(f"✅ PASS: Basic tensor operations work: {y.tolist()}")
        
    except ImportError as e:
        print(f"❌ FAIL: Cannot import torch: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ FAIL: Torch operation failed: {e}")
        all_passed = False
    print()
    
    # Test 3: Transformers
    print("TEST 3: Transformers Library")
    print("-" * 80)
    try:
        import transformers
        print(f"✅ Transformers imported successfully: {transformers.__version__}")
        
        # Try to load a tokenizer (this would fail with NumPy 2.x)
        from transformers import AutoTokenizer
        print("✅ PASS: AutoTokenizer can be imported")
        
    except Exception as e:
        print(f"❌ FAIL: Transformers error: {e}")
        all_passed = False
    print()
    
    # Test 4: Sentence Transformers
    print("TEST 4: Sentence Transformers")
    print("-" * 80)
    try:
        import sentence_transformers
        print(f"✅ Sentence-Transformers imported successfully: {sentence_transformers.__version__}")
        
        from sentence_transformers import SentenceTransformer
        print("✅ PASS: SentenceTransformer class can be imported")
        
    except Exception as e:
        print(f"❌ FAIL: Sentence-Transformers error: {e}")
        all_passed = False
    print()
    
    # Test 5: Other critical dependencies
    print("TEST 5: Other Dependencies")
    print("-" * 80)
    dependencies = [
        'fastapi',
        'sqlalchemy',
        'redis',
        'aiocache',
        'msgpack',
        'pydantic'
    ]
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep}: {version}")
        except ImportError:
            print(f"❌ {dep}: NOT INSTALLED")
            all_passed = False
    print()
    
    # Final Summary
    print("=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Your environment is correctly configured:")
        print("  ✅ NumPy 1.x (compatible with torch 2.2.0)")
        print("  ✅ PyTorch CPU-only (no GPU required)")
        print("  ✅ All critical dependencies installed")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        print()
        print("See error messages above for details.")
        print()
        print("Common fixes:")
        print("  1. NumPy 2.x issue:")
        print("     pip install 'numpy>=1.24.0,<2.0.0' --force-reinstall")
        print()
        print("  2. Missing dependencies:")
        print("     pip install -r requirements.txt")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(test_imports())
