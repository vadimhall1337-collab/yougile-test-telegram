from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

# Правильные абсолютные импорты от корня (bot.*)
from bot.keyboards.inline.tasks import (
    get_today_tasks_keyboard, 
    get_task_detail_keyboard, 
    TaskDetailCallback, 
    TaskActionCallback
)
from bot.repositories.tasks import TaskRepository 

today_router = Router()

# ==========================================
# 1. ОБРАБОТЧИК КНОПКИ "СЕГОДНЯ" (ВЫВОД СПИСКА)
# ==========================================
@today_router.message(F.text == "Сегодня")
async def show_today_tasks(message: Message, task_repository: TaskRepository):
    # Получаем задачи на сегодня (твоя рабочая логика)
    tasks = await task_repository.get_today_tasks()
    
    if not tasks:
        await message.answer("🎉 Отлично! У вас нет просроченных и текущих задач на сегодня.")
        return
        
    text = "📅 <b>Задачи на сегодня и просроченные:</b>\n\n<i>Выберите задачу для работы:</i>"
    
    # Генерируем клавиатуру, где каждая задача - это отдельная кнопка
    keyboard = get_today_tasks_keyboard(tasks)
    
    await message.answer(text, reply_markup=keyboard)


# ==========================================
# 2. ОБРАБОТЧИК КЛИКА ПО КОНКРЕТНОЙ ЗАДАЧЕ
# ==========================================
@today_router.callback_query(TaskDetailCallback.filter())
async def process_task_detail(call: CallbackQuery, callback_data: TaskDetailCallback, task_repository: TaskRepository):
    # Достаем ID задачи из нажатой кнопки
    task_id = callback_data.task_id
    
    # Запрашиваем из YouGile актуальную информацию о конкретной задаче
    task = await task_repository.get_by_id(task_id)
    
    # Формируем дату дедлайна
    deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
    
    # Собираем красивый текст карточки
    text = (
        f"📌 <b>{task.title}</b>\n\n"
        f"⏳ <b>Дедлайн:</b> {deadline_str}\n"
    )
    
    # Если у задачи есть описание, добавляем его в сообщение
    if hasattr(task, 'description') and task.description:
        text += f"\n📝 <b>Описание:</b>\n{task.description}"
        
    # Формируем клавиатуру действий для этой задачи (Выполнить, Отложить)
    keyboard = get_task_detail_keyboard(task)
    
    # Заменяем старое сообщение на карточку задачи
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ==========================================
# 3. ОБРАБОТЧИК ВОЗВРАТА НАЗАД К СПИСКУ
# ==========================================
@today_router.callback_query(F.data == "back_to_today")
async def process_back_to_today(call: CallbackQuery, task_repository: TaskRepository):
    # При нажатии "Назад" снова запрашиваем список задач
    tasks = await task_repository.get_today_tasks()
    
    if not tasks:
        await call.message.edit_text("🎉 Отлично! У вас больше нет просроченных и текущих задач на сегодня.")
        await call.answer()
        return
        
    text = "📅 <b>Задачи на сегодня и просроченные:</b>\n\n<i>Выберите задачу для работы:</i>"
    keyboard = get_today_tasks_keyboard(tasks)
    
    # Возвращаем интерфейс обратно к списку задач
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()