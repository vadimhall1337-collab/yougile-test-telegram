from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from models.user import UserSettings

class SettingsCallback(CallbackData, prefix="settings"):
    action: str # edit_morning, edit_evening, edit_reminder, edit_days, about

def get_settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    """Формирует клавиатуру настроек с текущими значениями."""
    morning_str = settings.morning_summary_time.strftime("%H:%M")
    evening_str = settings.evening_summary_time.strftime("%H:%M")
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"⏰ Утренняя сводка ({morning_str})", 
                callback_data=SettingsCallback(action="edit_morning").pack()
            )],
            [InlineKeyboardButton(
                text=f"🌙 Вечерняя сводка ({evening_str})", 
                callback_data=SettingsCallback(action="edit_evening").pack()
            )],
            [InlineKeyboardButton(
                text=f"🔔 Напоминание по умолч. ({settings.default_reminder_minutes} мин)", 
                callback_data=SettingsCallback(action="edit_reminder").pack()
            )],
            [InlineKeyboardButton(
                text="📆 Рабочие дни", 
                callback_data=SettingsCallback(action="edit_days").pack()
            )],
            [InlineKeyboardButton(
                text="ℹ️ О программе", 
                callback_data=SettingsCallback(action="about").pack()
            )]
        ]
    )