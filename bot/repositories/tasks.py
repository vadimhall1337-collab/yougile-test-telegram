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
        """Получает список всех задач с лимитом 1000 для последующей фильтрации."""
        # Делаем запрос точно так же, как в твоем рабочем скрипте
        response = await self._client.request("GET", "/tasks?limit=1000")
        tasks_raw = response.get("content", [])
        
        today = datetime.now().date()
        result = []
        
        for task in tasks_raw:
            deadline_obj = task.get("deadline")
            if not deadline_obj:
                continue
                
            timestamp = deadline_obj.get("deadline")
            if not timestamp:
                continue
                
            deadline_date = datetime.fromtimestamp(timestamp / 1000).date()
            
            # Передаем в Service Layer все задачи, у которых дедлайн сегодня ИЛИ уже просрочен
            # (Просроченные задачи тоже критически важно выводить в плане на день)
            if deadline_date <= today:
                # Маппим сырой словарь в типизированный объект TaskDto
                result.append(TaskDto(
                    id=task["id"],
                    title=task["title"],
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