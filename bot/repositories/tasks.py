from typing import List, Optional
from repositories.base import BaseRepository
from yougile.dto.tasks import TaskDto, CreateTaskDto, UpdateTaskDto
from yougile.client import YouGileClient
from utils.cache import CacheService
from datetime import datetime

class TaskRepository(BaseRepository):
    def __init__(self, client: YouGileClient, cache: CacheService):
        super().__init__(client, cache)
        # Префиксы кэша для инвалидации
        self._CACHE_PREFIX_TODAY = "tasks:today"
        self._CACHE_PREFIX_CASE = "tasks:case:"
        self._CACHE_PREFIX_DETAIL = "tasks:detail:"
        self._CACHE_PREFIX_SEARCH = "tasks:search:"

    def _get_invalidation_prefixes(self, task_id: Optional[str] = None, case_id: Optional[str] = None) -> List[str]:
        """Формирует список префиксов, которые нужно сбросить при мутации задачи."""
        prefixes = [self._CACHE_PREFIX_TODAY, self._CACHE_PREFIX_SEARCH]
        if task_id:
            prefixes.append(f"{self._CACHE_PREFIX_DETAIL}{task_id}")
        if case_id:
            prefixes.append(f"{self._CACHE_PREFIX_CASE}{case_id}")
        return prefixes

    async def get_by_id(self, task_id: str) -> TaskDto:
        cache_key = f"{self._CACHE_PREFIX_DETAIL}{task_id}"
        
        async def fetcher():
            raw_data = await self._client.request("GET", f"/tasks/{task_id}")
            return TaskDto(**raw_data)
            
        return await self._fetch_with_cache(cache_key, fetcher)

    async def get_case_tree(self, case_id: str) -> List[TaskDto]:
        cache_key = f"{self._CACHE_PREFIX_CASE}{case_id}"
        
        async def fetcher():
            # Запрашиваем задачи конкретной доски/колонки
            raw_data = await self._client.request("GET", f"/tasks?columnId={case_id}")
            return [TaskDto(**item) for item in raw_data.get("content", [])]
            
        return await self._fetch_with_cache(cache_key, fetcher)

    async def get_today_tasks(self) -> List[TaskDto]:
        """
        Получает список всех задач на сегодня для конкретной доски
        через предварительное получение списка её колонок.
        """
        TARGET_BOARD_ID = "c59af5e0-84c6-4e67-8b23-681dd0ddf580"
        
        # 1. Получаем список колонок для нашей доски (с кэшированием, например, на 12 или 24 часа)
        cache_key_columns = f"board:columns:{TARGET_BOARD_ID}"
        
        async def fetch_columns():
            # Запрашиваем колонки доски (лимит 1000, чтобы точно забрать все)
            raw_columns = await self._client.request("GET", f"/columns?boardId={TARGET_BOARD_ID}&limit=1000")
            # Возвращаем список ID активных колонок
            return [col["id"] for col in raw_columns.get("content", []) if not col.get("deleted")]

        # Используем встроенный метод работы с кэшем (TTL = 12 часов = 43200 секунд)
        column_ids = await self._fetch_with_cache(cache_key_columns, fetch_columns, ttl=43200)
        
        if not column_ids:
            return []

        # 2. Формируем строку ID колонок через запятую для YouGile API
        columns_param = ","(column_ids)
        
        # Используем рекомендованный эндпоинт /task-list
        response = await self._client.request("GET", f"/task-list?limit=1000&columnId={columns_param}")
        tasks_raw = response.get("content", [])
        
        today = datetime.now().date()
        result = []
        
        # 3. Фильтруем полученные задачи по дедлайну
        for task in tasks_raw:
            deadline_obj = task.get("deadline")
            if not deadline_obj:
                continue
                
            timestamp = deadline_obj.get("deadline")
            if not timestamp:
                continue
                
            deadline_date = datetime.fromtimestamp(timestamp / 1000).date()
            
            # Если дедлайн сегодня или просрочен
            if deadline_date <= today:
                result.append(TaskDto(
                    id=task["id"],
                    title=task["title"],
                    timestamp=timestamp,
                    deadline=deadline_date
                ))
                
        return result

    async def create(self, dto: CreateTaskDto) -> TaskDto:
        async def action():
            raw_data = await self._client.request("POST", "/tasks", json=dto.model_dump(exclude_none=True))
            return TaskDto(**raw_data)
            
        prefixes = self._get_invalidation_prefixes(case_id=dto.columnId)
        return await self._execute_and_invalidate(action, prefixes)

    async def update(self, task_id: str, dto: UpdateTaskDto) -> TaskDto:
        async def action():
            raw_data = await self._client.request("PUT", f"/tasks/{task_id}", json=dto.model_dump(exclude_none=True))
            return TaskDto(**raw_data)
            
        prefixes = self._get_invalidation_prefixes(task_id=task_id, case_id=dto.columnId)
        return await self._execute_and_invalidate(action, prefixes)

    async def complete(self, task_id: str) -> TaskDto:
        # Для завершения меняем статус completed на True
        dto = UpdateTaskDto(completed=True)
        return await self.update(task_id, dto)

    async def move(self, task_id: str, new_column_id: str) -> TaskDto:
        # Для перемещения меняем columnId
        dto = UpdateTaskDto(columnId=new_column_id)
        return await self.update(task_id, dto)

    async def search(self, query: str) -> List[TaskDto]:
        # Кэшируем результаты поиска с небольшим TTL
        cache_key = f"{self._CACHE_PREFIX_SEARCH}{query}"
        
        async def fetcher():
            raw_data = await self._client.request("GET", f"/tasks?search={query}")
            return [TaskDto(**item) for item in raw_data.get("content", [])]
            
        return await self._fetch_with_cache(cache_key, fetcher, ttl=60)