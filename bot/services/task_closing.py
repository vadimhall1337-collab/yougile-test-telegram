import asyncio
from typing import List
from repositories.tasks import TaskRepository
import structlog

logger = structlog.get_logger(__name__)

class TaskClosingService:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    async def check_uncompleted_subtasks(self, task_id: str) -> bool:
        """
        Проверяет, есть ли у задачи незавершенные подзадачи.
        Возвращает True, если есть хотя бы одна открытая подзадача.
        """
        task = await self._task_repo.get_by_id(task_id)
        
        if not task.subtasks:
            return False
            
        # В реальном API возможно потребуется запрашивать статусы подзадач пакетно
        # Здесь мы проверяем каждую подзадачу (сработает кэш репозитория, если они уже загружены)
        for subtask_id in task.subtasks:
            subtask = await self._task_repo.get_by_id(subtask_id)
            if not subtask.completed and not subtask.deleted and not subtask.archived:
                return True
                
        return False

    async def complete_task_tree(self, task_id: str) -> None:
        """
        Рекурсивно закрывает задачу и все ее подзадачи.
        """
        task = await self._task_repo.get_by_id(task_id)
        
        # Сначала закрываем вложенные элементы
        if task.subtasks:
            # Используем asyncio.gather для параллельного закрытия подзадач
            tasks_to_close = [self.complete_task_tree(sub_id) for sub_id in task.subtasks]
            await asyncio.gather(*tasks_to_close)
            
        # Затем закрываем саму задачу
        if not task.completed:
            await self._task_repo.complete(task_id)
            await logger.ainfo("Task completed", task_id=task_id)