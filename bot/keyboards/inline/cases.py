from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from keyboards.inline.work import NavigationCallback

def get_case_tree_keyboard(visual_tree: List[Dict[str, Any]], case_id: str) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру дерева задач для конкретного дела.
    """
    inline_keyboard = []
    
    for item in visual_tree:
        task = item["task"]
        display_text = item["display_text"]
        
        # Кнопка для открытия узла (переход в карточку задачи)
        inline_keyboard.append([
            InlineKeyboardButton(
                text=display_text,
                callback_data=NavigationCallback(target="task", id=task.id).pack()
            )
        ])
        
    # Обязательные кнопки навигации
    inline_keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад", 
            callback_data=NavigationCallback(target="back", action="back").pack()
        ),
        InlineKeyboardButton(
            text="🏠 Главное меню", 
            callback_data=NavigationCallback(target="main", action="main").pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_cases_list_keyboard(cases: List[Any]) -> InlineKeyboardMarkup:
    """Клавиатура со списком активных дел (колонок/досок)."""
    inline_keyboard = []
    
    for case in cases:
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {case.title}",
                callback_data=NavigationCallback(target="case_tree", id=case.id).pack()
            )
        ])
        
    inline_keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=NavigationCallback(target="back", action="back").pack()
        ),
        InlineKeyboardButton(
            text="🏠 Главное меню", callback_data=NavigationCallback(target="main", action="main").pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)