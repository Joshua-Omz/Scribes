"""Simple test to verify cache is working."""
import asyncio
from app.core.cache import get_cache_manager


async def main():
    print("Testing cache...")
    
    # Get cache manager
    cache_manager = await get_cache_manager()
    
    if not cache_manager.is_available:
        print("❌ Cache not available")
        return
    
    print("✅ Cache available")
    
    # Test aiocache wrapper
    try:
        await cache_manager.cache.set("test:simple", {"data": "hello"}, ttl=60)
        result = await cache_manager.cache.get("test:simple")
        print(f"✅ aiocache test: {result}")
    except Exception as e:
        print(f"❌ aiocache error: {e}")
    
    # Test raw client
    try:
        await cache_manager.client.set("test:raw", "hello", ex=60)
        result = await cache_manager.client.get("test:raw")
        print(f"✅ raw client test: {result}")
    except Exception as e:
        print(f"❌ raw client error: {e}")
    
    await cache_manager.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
