from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot.keyboards.inline.settings import get_settings_keyboard, SettingsCallback
from bot.repositories.database.users import UserSettingsRepository
from bot.states.creation import EditSettingsState

settings_router = Router(name="settings_router")

async def _send_or_edit_settings(message_or_query, db_user_repo: UserSettingsRepository, user_id: int):
    """Вспомогательная функция для генерации актуального меню настроек из БД."""
    settings = await db_user_repo.get_or_create(user_id)
    text = (
        "⚙️ <b>Настройки профиля</b>\n\n"
        "Здесь вы можете управлять параметрами уведомлений.\n"
        "Выберите параметр для изменения:"
    )
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(text=text, reply_markup=get_settings_keyboard(settings), parse_mode="HTML")
    else:
        await message_or_query.answer(text=text, reply_markup=get_settings_keyboard(settings), parse_mode="HTML")

@settings_router.message(F.text == "⚙️ Настройки")
async def process_settings_menu(message: Message, state: FSMContext, db_user_repo: UserSettingsRepository):
    await state.clear()
    await _send_or_edit_settings(message, db_user_repo, message.from_user.id)

@settings_router.callback_query(SettingsCallback.filter(F.action == "edit_morning"))
async def change_morning_click(query: CallbackQuery, state: FSMContext):
    await state.set_state(EditSettingsState.waiting_for_morning_time)
    await query.message.edit_text("⏳ Введите новое время для <b>утренней сводки</b> в формате <code>ЧЧ:ММ</code> (например, 09:00):", parse_mode="HTML")
    await query.answer()

@settings_router.callback_query(SettingsCallback.filter(F.action == "edit_evening"))
async def change_evening_click(query: CallbackQuery, state: FSMContext):
    await state.set_state(EditSettingsState.waiting_for_evening_time)
    await query.message.edit_text("⏳ Введите новое время для <b>вечерней сводки</b> в формате <code>ЧЧ:ММ</code> (например, 18:30):", parse_mode="HTML")
    await query.answer()

@settings_router.message(EditSettingsState.waiting_for_morning_time, F.text)
async def save_morning_time(message: Message, state: FSMContext, db_user_repo: UserSettingsRepository):
    try:
        valid_time = datetime.strptime(message.text.strip(), "%H:%M").time()
        await db_user_repo.update_settings(message.from_user.id, {"morning_summary_time": valid_time})
        
        await message.answer(f"✅ Время утренней сводки успешно изменено на <b>{message.text}</b>!", parse_mode="HTML")
        await state.clear()
        # Сразу выводим обновленное меню с новыми значениями на кнопках
        await _send_or_edit_settings(message, db_user_repo, message.from_user.id)
    except ValueError:
        await message.answer("❌ Неверный формат времени! Пожалуйста, введите время в формате <code>ЧЧ:ММ</code> (например, 08:30):", parse_mode="HTML")

@settings_router.message(EditSettingsState.waiting_for_evening_time, F.text)
async def save_evening_time(message: Message, state: FSMContext, db_user_repo: UserSettingsRepository):
    try:
        valid_time = datetime.strptime(message.text.strip(), "%H:%M").time()
        await db_user_repo.update_settings(message.from_user.id, {"evening_summary_time": valid_time})
        
        await message.answer(f"✅ Время вечерней сводки успешно изменено на <b>{message.text}</b>!", parse_mode="HTML")
        await state.clear()
        # Сразу выводим обновленное меню с новыми значениями на кнопках
        await _send_or_edit_settings(message, db_user_repo, message.from_user.id)
    except ValueError:
        await message.answer("❌ Неверный формат времени! Пожалуйста, введите время в формате <code>ЧЧ:ММ</code> (например, 18:00):", parse_mode="HTML")