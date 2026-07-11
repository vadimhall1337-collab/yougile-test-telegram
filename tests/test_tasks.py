import pytest
import time
from unittest.mock import AsyncMock

from services.tasks import TaskService
from repositories.tasks import TaskRepository
from yougile.dto.tasks import TaskDto

@pytest.fixture
def mock_task_repo():
    return AsyncMock(spec=TaskRepository)

@pytest.fixture
def task_service(mock_task_repo):
    return TaskService(task_repo=mock_task_repo)

@pytest.mark.asyncio
async def test_get_today_tasks_sorted(task_service, mock_task_repo):
    # Подготавливаем тестовые данные (одна задача просрочена, одна на будущее)
    now = time.time()
    task_overdue = TaskDto(id="1", title="Old", columnId="c1", timestamp=now - 3600)
    task_today = TaskDto(id="2", title="New", columnId="c1", timestamp=now + 3600)
    
    mock_task_repo.get_today_tasks.return_value = [task_today, task_overdue]
    
    # Вызываем тестируемый метод сервиса
    overdue, today = await task_service.get_today_tasks_sorted()
    
    # Проверяем, что бизнес-логика отработала верно
    assert len(overdue) == 1
    assert overdue[0].id == "1"
    
    assert len(today) == 1
    assert today[0].id == "2"