from typing import Dict, Any, List
from bot.yougile.client import YouGileClient
from bot.yougile.dto.tasks import TaskDto, CreateTaskDto, UpdateTaskDto

class TasksEndpoint:
    """Обертка для работы с эндпоинтом /tasks API YouGile."""
    
    def __init__(self, client: YouGileClient):
        self._client = client

    async def get_task(self, task_id: str) -> TaskDto:
        """Получает задачу по ID."""
        response = await self._client.request("GET", f"/tasks/{task_id}")
        return TaskDto(**response)

    async def get_tasks(self, column_id: str = None, search: str = None) -> List[TaskDto]:
        """Получает список задач с возможной фильтрацией."""
        params = {}
        if column_id:
            params["columnId"] = column_id
        if search:
            params["search"] = search
            
        # Формируем query строку
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/tasks?{query_string}" if query_string else "/tasks"
        
        response = await self._client.request("GET", endpoint)
        return [TaskDto(**item) for item in response.get("content", [])]

    async def create_task(self, data: CreateTaskDto) -> TaskDto:
        """Создает новую задачу."""
        response = await self._client.request(
            "POST", "/tasks", json=data.model_dump(exclude_none=True)
        )
        return TaskDto(**response)
        
    async def update_task(self, task_id: str, data: UpdateTaskDto) -> TaskDto:
        """Обновляет существующую задачу."""
        response = await self._client.request(
            "PUT", f"/tasks/{task_id}", json=data.model_dump(exclude_none=True)
        )
        return TaskDto(**response)