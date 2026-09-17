from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from yougile.dto.tasks import TaskDto

# Фабрики коллбэков для удобной передачи ID задачи между нажатиями
class TaskDetailCallback(CallbackData, prefix="task_detail"):
    task_id: str

class TaskActionCallback(CallbackData, prefix="task_action"):
    task_id: str
    action: str  # Возможные значения: "complete", "postpone", "subtasks", "edit", "quick_complete", "quick_postpone"

class EditFieldCallback(CallbackData, prefix="edit_field"):
    task_id: str
    field: str  # "title", "description", "deadline"

TaskAction = TaskActionCallback    

def get_today_tasks_keyboard(tasks: List[TaskDto], with_quick_actions: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком задач.
    
    Args:
        tasks: Список задач для отображения
        with_quick_actions: Если True, добавляет inline-кнопки быстрого действия (✅ и 🕒) к каждой задаче
    """
    builder = InlineKeyboardBuilder()
    
    for idx, task in enumerate(tasks, start=1):
        # Обрезаем слишком длинные названия, чтобы они красиво смотрелись на кнопке
        title = task.title if len(task.title) <= 30 else task.title[:27] + "..."
        
        if with_quick_actions:
            # Создаём строку с названием и быстрыми кнопками
            builder.button(
                text=f"{idx}. {title}",
                callback_data=TaskDetailCallback(task_id=task.id)
            )
            # Быстрые кнопки: Выполнить | Отложить
            builder.button(
                text="✅",
                callback_data=TaskActionCallback(task_id=task.id, action="quick_complete")
            )
            builder.button(
                text="🕒",
                callback_data=TaskActionCallback(task_id=task.id, action="quick_postpone")
            )
            # Расположение: 1 кнопка названия + 2 маленькие кнопки действий
            builder.adjust(1)  # Каждая задача в отдельном ряду
        else:
            # Простой режим без быстрых кнопок
            builder.button(
                text=f"{idx}. {title}",
                callback_data=TaskDetailCallback(task_id=task.id)
            )
            builder.adjust(1)
    
    return builder.as_markup()

def get_task_detail_keyboard(task: TaskDto) -> InlineKeyboardMarkup:
    """Клавиатура для конкретной задачи (выполнить, отложить, редактировать, подзадачи)."""
    builder = InlineKeyboardBuilder()
    
    # Первый ряд: Выполнить | Отложить
    builder.button(
        text="✅ Выполнить",
        callback_data=TaskActionCallback(task_id=task.id, action="complete")
    )
    builder.button(
        text="🕒 Отложить",
        callback_data=TaskActionCallback(task_id=task.id, action="postpone")
    )
    
    # Второй ряд: Редактировать | Подзадачи (если есть)
    builder.button(
        text="✏️ Редактировать",
        callback_data=TaskActionCallback(task_id=task.id, action="edit")
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
    
    # Кнопки действий ставим по 2 в ряд
    builder.adjust(2, 2, 1) 
    return builder.as_markup()

def get_edit_menu_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора поля редактирования задачи."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="📝 Название",
        callback_data=EditFieldCallback(task_id=task_id, field="title")
    )
    builder.button(
        text="📄 Описание",
        callback_data=EditFieldCallback(task_id=task_id, field="description")
    )
    builder.button(
        text="📅 Дедлайн",
        callback_data=EditFieldCallback(task_id=task_id, field="deadline")
    )
    
    builder.button(
        text="❌ Отмена",
        callback_data=TaskActionCallback(task_id=task_id, action="cancel_edit")
    )
    
    builder.adjust(2, 1)
    return builder.as_markup()

def get_cancel_edit_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой отмены."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=TaskActionCallback(task_id=task_id, action="cancel_edit")
    )
    return builder.as_markup()