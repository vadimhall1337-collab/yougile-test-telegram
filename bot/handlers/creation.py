from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.creation import CreateTaskState
from keyboards.inline.creation import (
    get_destination_keyboard, 
    get_deadline_date_keyboard, 
    get_deadline_time_keyboard,
    CreationCallback
)
from services.task_creation import TaskCreationService
from keyboards.reply.main_menu import get_main_menu_keyboard

creation_router = Router(name="creation_router")
# DI injects task_creation_service

@creation_router.message(F.text == "➕ Новая задача")
async def start_task_creation(message: Message, state: FSMContext):
    await state.set_state(CreateTaskState.waiting_for_destination)
    await message.answer(
        "Выберите, где создать задачу:",
        reply_markup=get_destination_keyboard()
    )

@creation_router.callback_query(CreateTaskState.waiting_for_destination, CreationCallback.filter(F.step == "dest"))
async def process_destination(query: CallbackQuery, callback_data: CreationCallback, state: FSMContext):
    await state.update_data(destination=callback_data.value)
    
    if callback_data.value == "inbox":
        await state.set_state(CreateTaskState.waiting_for_title)
        await query.message.edit_text("Введите название задачи:")
    else:
        # Для других разделов потребуется дополнительный флоу (выбор конкретного дела)
        await query.message.edit_text("Выбран раздел в разработке. Перенаправление во 'Входящие'...\nВведите название задачи:")
        await state.set_state(CreateTaskState.waiting_for_title)
        
    await query.answer()

@creation_router.message(CreateTaskState.waiting_for_title, F.text)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(CreateTaskState.waiting_for_date)
    await message.answer("Выберите дедлайн (дата):", reply_markup=get_deadline_date_keyboard())

@creation_router.callback_query(CreateTaskState.waiting_for_date, CreationCallback.filter(F.step == "date"))
async def process_date(query: CallbackQuery, callback_data: CreationCallback, state: FSMContext):
    await state.update_data(date=callback_data.value)
    
    if callback_data.value == "none":
        # Пропускаем выбор времени
        await state.update_data(time="none")
        await finalize_task_creation(query, state)
    else:
        await state.set_state(CreateTaskState.waiting_for_time)
        await query.message.edit_text("Выберите дедлайн (время):", reply_markup=get_deadline_time_keyboard())
    await query.answer()

@creation_router.callback_query(CreateTaskState.waiting_for_time, CreationCallback.filter(F.step == "time"))
async def process_time(query: CallbackQuery, callback_data: CreationCallback, state: FSMContext):
    await state.update_data(time=callback_data.value)
    await finalize_task_creation(query, state)
    await query.answer()

async def finalize_task_creation(query: CallbackQuery, state: FSMContext):
    """Финальный шаг: отправка данных в сервис и ответ пользователю."""
    data = await state.get_data()
    
    # В production-коде сервис инжектируется
    # task_id = await task_creation_service.create_task_from_fsm(data)
    
    await query.message.edit_text(
        f"✅ Задача <b>{data.get('title')}</b> успешно создана во Входящих!", 
        parse_mode="HTML"
    )
    await state.clear()
    
@creation_router.callback_query(F.data == "cancel_creation")
async def cancel_creation(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.delete()
    await query.message.answer("Создание задачи отменено.", reply_markup=get_main_menu_keyboard())
    await query.answer()