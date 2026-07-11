from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Сборка клавиатуры главного меню."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📂 Работа")],
            [KeyboardButton(text="➕ Новая задача"), KeyboardButton(text="🔎 Поиск")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        is_persistent=True,  # Клавиатура всегда видна пользователю
        input_field_placeholder="Выберите раздел..."
    )
    return keyboard