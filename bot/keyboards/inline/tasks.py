from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from typing import List
from yougile.dto.tasks import TaskDto

# Фабрики коллбэков для удобной передачи ID задачи между нажатиями
class TaskDetailCallback(CallbackData, prefix="task_detail"):
    task_id: str

class TaskActionCallback(CallbackData, prefix="task_action"):
    task_id: str
    action: str  # Возможные значения: "complete", "postpone", "subtasks"

def get_today_tasks_keyboard(tasks: List[TaskDto]) -> InlineKeyboardMarkup:
    """Клавиатура со списком задач (каждая задача - отдельная кнопка)."""
    builder = InlineKeyboardBuilder()
    
    for idx, task in enumerate(tasks, start=1):
        # Обрезаем слишком длинные названия, чтобы они красиво смотрелись на кнопке
        title = task.title if len(task.title) <= 30 else task.title[:27] + "..."
        builder.button(
            text=f"{idx}. {title}",
            callback_data=TaskDetailCallback(task_id=task.id)
        )
    
    # Кнопки будут располагаться по одной в ряд (вертикальный список)
    builder.adjust(1)
    return builder.as_markup()

def get_task_detail_keyboard(task: TaskDto) -> InlineKeyboardMarkup:
    """Клавиатура для конкретной задачи (выполнить, отложить, подзадачи)."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ Выполнить",
        callback_data=TaskActionCallback(task_id=task.id, action="complete")
    )
    builder.button(
        text="🕒 Отложить",
        callback_data=TaskActionCallback(task_id=task.id, action="postpone")
    )
    
    # Проверяем, есть ли подзадачи (массив существует и не пуст)
    if task.subtasks and len(task.subtasks) > 0:
        builder.button(
            text="📋 Подзадачи",
            callback_data=TaskActionCallback(task_id=task.id, action="subtasks")
        )
        
    builder.button(
        text="🔙 Назад к списку",
        callback_data="back_to_today"
    )
    
    # Кнопки действий ставим по 2 в ряд, остальные (подзадачи, назад) - по 1 в ряд
    builder.adjust(2, 1) 
    return builder.as_markup()