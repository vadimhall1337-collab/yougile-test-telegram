from typing import TypeVar, Callable, Awaitable, Any, List, Optional
from utils.cache import CacheService
from yougile.client import YouGileClient

T = TypeVar('T')

class BaseRepository:
    def __init__(self, client: YouGileClient, cache: CacheService):
        self._client = client
        self._cache = cache

    async def _fetch_with_cache(self, cache_key: str, fetch_func: Callable[[], Awaitable[T]], ttl: int = 300) -> T:
        """
        Паттерн получения данных: проверяем кэш, если пусто — идем в API и сохраняем результат.
        """
        cached_data = await self._cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        data = await fetch_func()
        await self._cache.set(cache_key, data, ttl_seconds=ttl)
        return data

    async def _invalidate(self, prefixes: List[str]) -> None:
        """
        Очистка кэша по списку префиксов.
        """
        for prefix in prefixes:
            await self._cache.invalidate(prefix)
            
    async def _execute_and_invalidate(
        self, 
        action_func: Callable[[], Awaitable[T]], 
        invalidation_prefixes: List[str]
    ) -> T:
        """
        Паттерн изменения данных: выполняем действие в API, затем инвалидируем связанные кэши.
        """
        result = await action_func()
        await self._invalidate(invalidation_prefixes)
        return result