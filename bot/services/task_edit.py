from typing import Optional
from datetime import date, datetime
from repositories.tasks import TaskRepository
from yougile.dto.tasks import TaskDto, UpdateTaskDto
import structlog

logger = structlog.get_logger(__name__)

class TaskEditService:
    """Сервис для редактирования задач."""
    
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo
    
    async def get_task(self, task_id: str) -> TaskDto:
        """Получает полную информацию о задаче."""
        return await self._task_repo.get_by_id(task_id)
    
    async def update_title(self, task_id: str, new_title: str) -> TaskDto:
        """Обновляет название задачи."""
        dto = UpdateTaskDto(title=new_title)
        updated_task = await self._task_repo.update(task_id, dto)
        
        await logger.ainfo(
            "Task title updated",
            task_id=task_id,
            new_title=new_title
        )
        
        return updated_task
    
    async def update_description(self, task_id: str, new_description: Optional[str]) -> TaskDto:
        """Обновляет описание задачи."""
        dto = UpdateTaskDto(description=new_description if new_description else None)
        updated_task = await self._task_repo.update(task_id, dto)
        
        await logger.ainfo(
            "Task description updated",
            task_id=task_id,
            has_description=new_description is not None
        )
        
        return updated_task
    
    async def update_deadline(self, task_id: str, new_deadline: date) -> TaskDto:
        """Обновляет дедлайн задачи."""
        dto = UpdateTaskDto(deadline=new_deadline)
        updated_task = await self._task_repo.update(task_id, dto)
        
        await logger.ainfo(
            "Task deadline updated",
            task_id=task_id,
            new_deadline=new_deadline.isoformat()
        )
        
        return updated_task
