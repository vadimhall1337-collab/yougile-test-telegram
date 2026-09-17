from typing import List, Dict
from repositories.tasks import TaskRepository
from yougile.dto.tasks import TaskDto
import structlog

logger = structlog.get_logger(__name__)

class TaskPostponeService:
    """Сервис для управления откладыванием задач (перемещением между колонками)."""
    
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo
        self._default_board_id = "c59af5e0-84c6-4e67-8b23-681dd0ddf580"
    
    async def get_board_columns(self, board_id: str = None) -> List[Dict]:
        """
        Получает список колонок для доски.
        Возвращает только активные (не удалённые) колонки.
        """
        target_board = board_id or self._default_board_id
        
        payload = {
            "boardId": target_board,
            "limit": 1000
        }
        
        raw_columns = await self._task_repo._client.request("GET", "/columns", json=payload)
        columns = [col for col in raw_columns.get("content", []) if not col.get("deleted")]
        
        return columns
    
    async def get_available_columns_for_task(self, task: TaskDto) -> List[Dict]:
        """
        Получает список доступных колонок для перемещения задачи.
        Исключает текущую колонку задачи.
        """
        all_columns = await self.get_board_columns(task.boardId)
        
        # Фильтруем текущую колонку
        available = [col for col in all_columns if col["id"] != task.columnId]
        
        return available
    
    async def move_task_to_column(self, task_id: str, new_column_id: str) -> TaskDto:
        """
        Перемещает задачу в указанную колонку.
        Возвращает обновлённый объект задачи.
        """
        # Перемещаем задачу через репозиторий
        updated_task = await self._task_repo.move(task_id, new_column_id)
        
        await logger.ainfo(
            "Task postponed to column", 
            task_id=task_id, 
            new_column_id=new_column_id,
            task_title=updated_task.title
        )
        
        return updated_task
    
    async def get_task_with_details(self, task_id: str) -> TaskDto:
        """Получает полную информацию о задаче."""
        return await self._task_repo.get_by_id(task_id)
