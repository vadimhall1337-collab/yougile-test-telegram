from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import structlog

from bot.keyboards.inline.tasks import TaskAction, get_task_action_keyboard
from bot.services.tasks import TaskService

logger = structlog.get_logger(__name__)
today_router = Router(name="today_router")

# Ловим любые варианты кнопки "Сегодня" или команду /today
@today_router.message(F.text.contains("Сегодня") | (F.text == "/today"))
async def process_today_menu(message: Message, state: FSMContext, task_service: TaskService):
    """Обработчик раздела 'Сегодня'."""
    
    # 1. Логируем старт в консоль
    await logger.ainfo(f"Пользователь {message.from_user.id} запросил задачи на сегодня.")
    
    # 2. Очищаем состояние навигации (чтобы не застрять в настройках)
    await state.clear()
    
    # 3. Отправляем сообщение-заглушку, пока API YouGile "думает"
    wait_msg = await message.answer("⏳ <i>Подключаюсь к YouGile и ищу задачи...</i>", parse_mode="HTML")
    
    try:
        # Получаем задачи через сервис
        overdue_tasks, today_tasks = await task_service.get_today_tasks_sorted()
        
        # Формируем текст
        text = "🗓 <b>План на сегодня</b>\n\n"
        
        if not overdue_tasks and not today_tasks:
            text += "<i>Нет активных задач на сегодня. Отличная работа!</i>"
            await wait_msg.edit_text(text, parse_mode="HTML")
            return

        # Добавляем просроченные задачи
        if overdue_tasks:
            text += "🔴 <b>Просрочено:</b>\n"
            for task in overdue_tasks:
                text += f"▪️ {task.title}\n"
            text += "\n"
            
        # Добавляем сегодняшние задачи
        if today_tasks:
            text += "🟠 <b>На сегодня:</b>\n"
            for task in today_tasks:
                text += f"▫️ {task.title}\n"
                
        # Определяем задачу для inline-кнопок
        first_task = (overdue_tasks + today_tasks)[0]
        
        # Обновляем наше сообщение-заглушку на готовый результат
        await wait_msg.edit_text(
            text, 
            reply_markup=get_task_action_keyboard(first_task.id),
            parse_mode="HTML"
        )
        await logger.ainfo("Задачи успешно загружены и выведены.")
        
    except Exception as e:
        await logger.aerror(f"Ошибка при запросе задач: {e}")
        await wait_msg.edit_text("❌ Произошла ошибка при загрузке задач из YouGile. Посмотрите логи в консоли.")