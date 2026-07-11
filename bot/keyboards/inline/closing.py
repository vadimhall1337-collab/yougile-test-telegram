from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class ConfirmCloseCallback(CallbackData, prefix="close_tree"):
    task_id: str
    confirm: bool

def get_confirm_closing_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения закрытия ветки задач."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да", 
                    callback_data=ConfirmCloseCallback(task_id=task_id, confirm=True).pack()
                ),
                InlineKeyboardButton(
                    text="Нет", 
                    callback_data=ConfirmCloseCallback(task_id=task_id, confirm=False).pack()
                )
            ]
        ]
    )