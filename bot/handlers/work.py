from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline.work import get_work_menu_keyboard, NavigationCallback
from bot.keyboards.reply.main_menu import get_main_menu_keyboard
from bot.services.navigation import NavigationService

work_router = Router(name="work_router")
nav_service = NavigationService() # В production — через Dependency Injection

@work_router.message(F.text == "📂 Работа")
async def process_work_menu(message: Message, state: FSMContext):
    """Вход в раздел 'Работа' из главного меню."""
    
    # Фиксируем переход в FSM
    await nav_service.push_screen(state, "work_root")
    
    text = "📂 <b>Раздел Работа</b>\n\nВыберите интересующую вас категорию:"
    
    await message.answer(
        text=text, 
        reply_markup=get_work_menu_keyboard(),
        parse_mode="HTML"
    )

@work_router.callback_query(NavigationCallback.filter(F.action == "main"))
async def process_main_menu_callback(query: CallbackQuery, state: FSMContext):
    """Глобальный обработчик кнопки '🏠 Главное меню'."""
    await nav_service.clear_stack(state)
    
    await query.message.delete()
    # Отправляем новое сообщение, чтобы обновить Reply Keyboard, если нужно
    await query.message.answer(
        "Вы вернулись в Главное меню.",
        reply_markup=get_main_menu_keyboard()
    )
    await query.answer()

@work_router.callback_query(NavigationCallback.filter(F.action == "back"))
async def process_back_callback(query: CallbackQuery, state: FSMContext):
    """
    Глобальный обработчик кнопки '⬅ Назад'.
    Здесь будет реализован паттерн Strategy или роутинг по строковым идентификаторам,
    чтобы бот знал, какой интерфейс отрендерить в зависимости от previous_screen.
    """
    previous_screen = await nav_service.pop_screen(state)
    
    if previous_screen == "main_menu":
        await query.message.delete()
        await query.message.answer("Вы вернулись в Главное меню.", reply_markup=get_main_menu_keyboard())
    elif previous_screen == "work_root":
        await query.message.edit_text(
            text="📂 <b>Раздел Работа</b>\n\nВыберите интересующую вас категорию:",
            reply_markup=get_work_menu_keyboard(),
            parse_mode="HTML"
        )
    # Далее здесь будут добавляться условия для возврата к спискам дел, конкретным задачам и т.д.
    # В идеале эту маршрутизацию мы инкапсулируем в отдельный ScreenRendererService.
    
    await query.answer()