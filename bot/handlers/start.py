from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.reply.main_menu import get_main_menu_keyboard
from services.users import UserService

start_router = Router(name="start_router")
# В production-коде сервис будет внедряться через Dependency Injection
user_service = UserService() 

@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Эндпоинт для команды /start."""
    # Передаем выполнение в сервисный слой
    reply_text = await user_service.process_start_command(
        user_id=message.from_user.id,
        username=message.from_user.full_name,
        state=state
    )
    
    # Рендерим UI (отправляем ответ и клавиатуру)
    await message.answer(
        text=reply_text,
        reply_markup=get_main_menu_keyboard()
    )

@start_router.message(Command("help"))
async def cmd_help(message: Message):
    """Эндпоинт для команды /help."""
    help_text = (
        "Это Telegram-клиент для YouGile.\n"
        "Используйте кнопки меню для навигации. Доступные команды:\n"
        "/start — Главное меню\n"
        "/help — Справка"
    )
    await message.answer(text=help_text)