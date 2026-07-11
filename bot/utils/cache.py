from abc import ABC, abstractmethod
from typing import Any, Optional
import time
import asyncio

class CacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        pass

    @abstractmethod
    async def invalidate(self, prefix: str) -> None:
        pass

class MemoryCache(CacheService):
    def __init__(self):
        self._store = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            record = self._store.get(key)
            if not record:
                return None
            
            value, expires_at = record
            if time.time() > expires_at:
                del self._store[key]
                return None
                
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        async with self._lock:
            expires_at = time.time() + ttl_seconds
            self._store[key] = (value, expires_at)

    async def invalidate(self, prefix: str) -> None:
        async with self._lock:
            keys_to_delete = [k for k in self._store.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]