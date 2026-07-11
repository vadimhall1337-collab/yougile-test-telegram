from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class CreationCallback(CallbackData, prefix="create"):
    step: str
    value: str

def get_destination_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Входящие", callback_data=CreationCallback(step="dest", value="inbox").pack())],
            [InlineKeyboardButton(text="🏠 Дела", callback_data=CreationCallback(step="dest", value="case").pack())],
            [InlineKeyboardButton(text="✅ Материалы", callback_data=CreationCallback(step="dest", value="check").pack())],
            [InlineKeyboardButton(text="🌍 Поручения", callback_data=CreationCallback(step="dest", value="regional").pack())],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
        ]
    )

def get_deadline_date_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сегодня", callback_data=CreationCallback(step="date", value="today").pack()),
                InlineKeyboardButton(text="Завтра", callback_data=CreationCallback(step="date", value="tomorrow").pack())
            ],
            [
                InlineKeyboardButton(text="📅 Выбрать дату", callback_data=CreationCallback(step="date", value="custom").pack()),
                InlineKeyboardButton(text="Без срока", callback_data=CreationCallback(step="date", value="none").pack())
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
        ]
    )

def get_deadline_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="09:00", callback_data=CreationCallback(step="time", value="09:00").pack()),
                InlineKeyboardButton(text="12:00", callback_data=CreationCallback(step="time", value="12:00").pack()),
                InlineKeyboardButton(text="18:00", callback_data=CreationCallback(step="time", value="18:00").pack())
            ],
            [
                InlineKeyboardButton(text="⏰ Выбрать", callback_data=CreationCallback(step="time", value="custom").pack()),
                InlineKeyboardButton(text="Без времени", callback_data=CreationCallback(step="time", value="none").pack())
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")]
        ]
    )