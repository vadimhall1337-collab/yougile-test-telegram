from typing import List
from repositories.base import BaseRepository
from yougile.client import YouGileClient
from utils.cache import CacheService
from yougile.dto.boards import CaseDto

class CaseRepository(BaseRepository):
    def __init__(self, client: YouGileClient, cache: CacheService):
        super().__init__(client, cache)
        self._CACHE_PREFIX_CASES = "cases:active"

    async def get_active_cases(self) -> List[CaseDto]:
        """Получает список активных колонок (дел) из YouGile."""
        cache_key = self._CACHE_PREFIX_CASES
        
        async def fetcher():
            raw_data = await self._client.request("GET", "/columns")
            cases = []
            for item in raw_data.get("content", []):
                # Отсеиваем удаленные колонки, если такой флаг есть
                if not item.get("deleted", False):
                    cases.append(CaseDto(id=item["id"], title=item["title"]))
            return cases
            
        # Кэшируем на 10 минут (600 секунд), чтобы не дергать API каждый раз
        return await self._fetch_with_cache(cache_key, fetcher, ttl=600)