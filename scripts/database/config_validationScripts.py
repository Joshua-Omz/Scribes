import os
from app.core.config import settings

def validate_config():
    """Validate all required configuration for AssistantService"""
    
    print("=" * 60)
    print("SCRIBES ASSISTANT SERVICE - CONFIGURATION VALIDATION")
    print("=" * 60)
    
    issues = []
    
    # 1. Check HuggingFace API Key
    if not settings.huggingface_api_key:
        issues.append("❌ HUGGINGFACE_API_KEY not set")
    else:
        masked_key = settings.huggingface_api_key[:7] + "..." + settings.huggingface_api_key[-4:]
        print(f"✅ HuggingFace API Key: {masked_key}")
    
    # 2. Check API Mode
    print(f"✅ HF Use API Mode: {settings.hf_use_api}")
    
    # 3. Check Models
    print(f"✅ Embedding Model: {settings.hf_embedding_model}")
    print(f"✅ Generation Model: {settings.hf_generation_model}")
    
    # 4. Check Token Budgets
    print(f"\n📊 Token Budget Configuration:")
    print(f"   Context Window: {settings.assistant_model_context_window}")
    print(f"   Max Context: {settings.assistant_max_context_tokens}")
    print(f"   Max Output: {settings.assistant_max_output_tokens}")
    print(f"   System Tokens: {settings.assistant_system_tokens}")
    print(f"   Query Tokens: {settings.assistant_user_query_tokens}")
    
    # 5. Calculate total and validate
    total_tokens = (
        settings.assistant_system_tokens +
        settings.assistant_user_query_tokens +
        settings.assistant_max_context_tokens +
        settings.assistant_max_output_tokens
    )
    
    if total_tokens > settings.assistant_model_context_window:
        issues.append(f"❌ Token budget overflow: {total_tokens} > {settings.assistant_model_context_window}")
    else:
        buffer = settings.assistant_model_context_window - total_tokens
        print(f"   ✅ Total Budget: {total_tokens}/{settings.assistant_model_context_window} tokens")
        print(f"   ✅ Safety Buffer: {buffer} tokens ({buffer/settings.assistant_model_context_window*100:.1f}%)")
    
    # 6. Check Database
    print(f"\n🗄️  Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    
    # Final Report
    print("\n" + "=" * 60)
    if issues:
        print("❌ CONFIGURATION ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before testing.")
        return False
    else:
        print("✅ ALL CONFIGURATION CHECKS PASSED!")
        print("You can proceed with manual testing.")
        return True

if __name__ == "__main__":
    validate_config()