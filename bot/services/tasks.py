import time
from typing import List, Tuple
from repositories.tasks import TaskRepository
from yougile.dto.tasks import TaskDto

class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self._task_repo = task_repo

    async def get_today_tasks_sorted(self) -> Tuple[List[TaskDto], List[TaskDto]]:
        """
        Получает задачи на сегодня и сортирует их.
        Возвращает кортеж: (просроченные_задачи, задачи_на_сегодня).
        """
        # Получаем данные через абстракцию репозитория (сработает кэш или API)
        tasks = await self._task_repo.get_today_tasks()
        
        overdue = []
        today = []
        
        current_time = time.time() * 1000
        
        # Разделение и сортировка
        for task in tasks:
            if task.completed or task.deleted or task.archived:
                continue
                
            # Упрощенная логика проверки дедлайна (в реальности требует работы с timezone)
            if task.timestamp and task.timestamp < current_time:
                overdue.append(task)
            else:
                today.append(task)
                
        # Сортировка: просроченные и сегодняшние сортируются по времени возрастания (timestamp)
        overdue.sort(key=lambda x: x.timestamp if x.timestamp else float('inf'))
        today.sort(key=lambda x: x.timestamp if x.timestamp else float('inf'))
        
        return overdue, today

    def format_task_short_message(self, task: TaskDto, is_overdue: bool) -> str:
        """Форматирует краткий текст для одной задачи в списке."""
        status_icon = "🔴" if is_overdue else "🟠"
        # В реальном приложении здесь будет конвертация timestamp в ЧЧ:ММ
        return f"{status_icon} <b>{task.title}</b>"