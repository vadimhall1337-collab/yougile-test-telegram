from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

# Фабрика коллбеков для действий с конкретной задачей
class TaskAction(CallbackData, prefix="task"):
    action: str  # Действие: 'complete', 'details', и т.д.
    task_id: str # ID задачи в YouGile

def get_task_action_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру под конкретной задачей."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Выполнить", 
                callback_data=TaskAction(action="complete", task_id=task_id).pack()
            ),
            InlineKeyboardButton(
                text="ℹ️ Подробнее", 
                callback_data=TaskAction(action="details", task_id=task_id).pack()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)