import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from repositories.tasks import TaskRepository
from yougile.dto.tasks import CreateTaskDto

class TaskCreationService:
    def __init__(self, task_repo: TaskRepository, config: Any):
        self._task_repo = task_repo
        self._config = config  # Конфигурация приложения (содержит ID колонок и исполнителя)

    def _calculate_timestamp(self, date_val: str, time_val: str) -> Optional[int]:
        """Конвертирует выбранные дату и время в timestamp."""
        if date_val == "none":
            return None
            
        now = datetime.now()
        target_date = now
        
        if date_val == "tomorrow":
            target_date = now + timedelta(days=1)
            
        # Устанавливаем время (по умолчанию конец рабочего дня, если время не выбрано, 
        # но в YouGile дедлайн без времени обычно ставится на 23:59)
        hour, minute = 23, 59
        if time_val != "none" and ":" in time_val:
            hour, minute = map(int, time_val.split(":"))
            
        final_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return int(final_datetime.timestamp() * 1000) # YouGile может требовать миллисекунды

    async def create_task_from_fsm(self, state_data: Dict[str, Any]) -> str:
        """Собирает DTO и вызывает репозиторий для создания задачи."""
        
        # Получаем ID колонки из конфига (например, для Входящих)
        destination = state_data.get("destination")
        if destination == "inbox":
            column_id = self._config.YOUGILE_INBOX_COLUMN_ID
        else:
            # Заглушка: если выбрано что-то другое, потребуется дополнительный шаг выбора колонки
            column_id = self._config.YOUGILE_INBOX_COLUMN_ID 
            
        timestamp = self._calculate_timestamp(state_data.get("date"), state_data.get("time"))
        
        dto = CreateTaskDto(
            title=state_data.get("title"),
            columnId=column_id,
            # Описание и исполнитель могут быть добавлены в DTO
        )
        
        # Передаем в репозиторий (который сам инвалидирует кэш)
        created_task = await self._task_repo.create(dto)
        return created_task.id