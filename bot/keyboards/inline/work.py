from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import Optional

class NavigationCallback(CallbackData, prefix="nav"):
    """Единая фабрика для навигации по всему дереву YouGile."""
    target: str          # Куда идем: 'cases', 'checks', 'regional', 'board', 'column', 'task'
    id: Optional[str] = None # ID сущности (кейса, доски, задачи), если есть
    action: str = "view" # Действие: view (просмотр), back (назад), main (в корень)

def get_work_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура корневого раздела 'Работа'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🏠 Дела", 
                callback_data=NavigationCallback(target="cases").pack()
            )],
            [InlineKeyboardButton(
                text="✅ Материалы", 
                callback_data=NavigationCallback(target="checks").pack()
            )],
            [InlineKeyboardButton(
                text="🌍 Поручения", 
                callback_data=NavigationCallback(target="regional").pack()
            )],
            # Стандартный блок навигации, который будет добавляться ко всем клавиатурам
            [
                InlineKeyboardButton(
                    text="⬅ Назад", 
                    callback_data=NavigationCallback(target="back", action="back").pack()
                ),
                InlineKeyboardButton(
                    text="🏠 Главное меню", 
                    callback_data=NavigationCallback(target="main", action="main").pack()
                )
            ]
        ]
    )