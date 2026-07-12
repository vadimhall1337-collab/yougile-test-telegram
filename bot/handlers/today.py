from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.inline.tasks import (
    get_today_tasks_keyboard, 
    get_task_detail_keyboard, 
    TaskDetailCallback, 
    TaskActionCallback
)
# Импортируем ваш класс репозитория (или сервиса), который обращается к YouGile
from repositories.tasks import TaskRepository 

router = Router()

# ==========================================
# 1. ОБРАБОТЧИК КНОПКИ "СЕГОДНЯ" (ВЫВОД СПИСКА)
# ==========================================
@router.message(F.text == "Сегодня")
async def show_today_tasks(message: Message, task_repository: TaskRepository):
    # Получаем задачи на сегодня
    tasks = await task_repository.get_today_tasks()
    
    if not tasks:
        await message.answer("🎉 Отлично! У вас нет просроченных и текущих задач на сегодня.")
        return
        
    text = "📅 <b>Задачи на сегодня и просроченные:</b>\n\n<i>Выберите задачу для работы:</i>"
    
    # Генерируем клавиатуру-список
    keyboard = get_today_tasks_keyboard(tasks)
    
    await message.answer(text, reply_markup=keyboard)


# ==========================================
# 2. ОБРАБОТЧИК КЛИКА ПО КОНКРЕТНОЙ ЗАДАЧЕ
# ==========================================
@router.callback_query(TaskDetailCallback.filter())
async def process_task_detail(call: CallbackQuery, callback_data: TaskDetailCallback, task_repository: TaskRepository):
    # Достаем ID задачи, на которую нажал пользователь
    task_id = callback_data.task_id
    
    # Делаем запрос к API для получения актуальной карточки задачи по ID
    task = await task_repository.get_by_id(task_id)
    
    # Формируем дату дедлайна
    deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
    
    # Формируем красивую карточку задачи
    text = (
        f"📌 <b>{task.title}</b>\n\n"
        f"⏳ <b>Дедлайн:</b> {deadline_str}\n"
    )
    # Если в YouGile добавлено описание, выводим его
    if task.description:
        text += f"\n📝 <b>Описание:</b>\n{task.description}"
        
    # Формируем клавиатуру действий для этой задачи
    keyboard = get_task_detail_keyboard(task)
    
    # Редактируем текущее сообщение, превращая список в карточку задачи
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


# ==========================================
# 3. ОБРАБОТЧИК ВОЗВРАТА НАЗАД К СПИСКУ
# ==========================================
@router.callback_query(F.data == "back_to_today")
async def process_back_to_today(call: CallbackQuery, task_repository: TaskRepository):
    # При нажатии "Назад" снова запрашиваем актуальный список задач
    tasks = await task_repository.get_today_tasks()
    
    if not tasks:
        await call.message.edit_text("🎉 Отлично! У вас больше нет просроченных и текущих задач на сегодня.")
        await call.answer()
        return
        
    text = "📅 <b>Задачи на сегодня и просроченные:</b>\n\n<i>Выберите задачу для работы:</i>"
    keyboard = get_today_tasks_keyboard(tasks)
    
    # Возвращаем интерфейс к первоначальному списку
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()