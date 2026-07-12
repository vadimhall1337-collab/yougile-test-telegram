import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline.tasks import (
    get_today_tasks_keyboard, 
    get_task_detail_keyboard, 
    TaskDetailCallback, 
)
from bot.repositories.tasks import TaskRepository 

today_router = Router()

# ==========================================
# 1. ОБРАБОТЧИК КНОПКИ "СЕГОДНЯ"
# ==========================================
@today_router.message(F.text == "📅 Сегодня")
async def show_today_tasks(message: Message, task_repo: TaskRepository):
    tasks = await task_repo.get_today_tasks()
    
    if not tasks:
        await message.answer("🎉 Отлично! У вас нет просроченных и текущих задач на сегодня.")
        return
        
    now = datetime.now().date()
    
    # ИСПРАВЛЕНО: Убрали .date() у t.deadline, так как это уже объект даты
    overdue_tasks = [t for t in tasks if t.deadline and t.deadline < now]
    today_tasks = [t for t in tasks if not t.deadline or t.deadline >= now]
    
    # 1. Если есть просроченные, отправляем их отдельным сообщением
    if overdue_tasks:
        text_overdue = "🚨 <b>Просроченные задачи:</b>\n\n"
        for i, task in enumerate(overdue_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y")
            text_overdue += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_overdue += "<i>Выберите просроченную задачу для работы:</i>"
        await message.answer(
            text_overdue, 
            reply_markup=get_today_tasks_keyboard(overdue_tasks), 
            parse_mode="HTML"
        )
        
    # 2. Отправляем задачи на сегодня
    if today_tasks:
        text_today = "📅 <b>Задачи на сегодня:</b>\n\n"
        for i, task in enumerate(today_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Без дедлайна"
            text_today += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_today += "<i>Выберите задачу на сегодня для работы:</i>"
        await message.answer(
            text_today, 
            reply_markup=get_today_tasks_keyboard(today_tasks), 
            parse_mode="HTML"
        )


# ==========================================
# 2. ОБРАБОТЧИК КЛИКА ПО КОНКРЕТНОЙ ЗАДАЧЕ
# ==========================================
@today_router.callback_query(TaskDetailCallback.filter())
async def process_task_detail(call: CallbackQuery, callback_data: TaskDetailCallback, task_repo: TaskRepository):
    task_id = callback_data.task_id
    task = await task_repo.get_by_id(task_id)
    
    deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
    
    text = (
        f"📌 <b>Карточка задачи</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Название:</b> {task.title}\n"
        f"⏳ <b>Дедлайн:</b> <code>{deadline_str}</code>\n"
    )
    
    if hasattr(task, 'description') and task.description:
        text += f"━━━━━━━━━━━━━━━━━━━━\n💬 <b>Описание:</b>\n<i>{task.description}</i>"
        
    keyboard = get_task_detail_keyboard(task)
    
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await call.answer()


# ==========================================
# 3. ОБРАБОТЧИК ВОЗВРАТА НАЗАД К СВОЕМУ СПИСКУ
# ==========================================
@today_router.callback_query(F.data == "back_to_today")
async def process_back_to_today(call: CallbackQuery, task_repo: TaskRepository):
    tasks = await task_repo.get_today_tasks()
    now = datetime.now().date()
    
    # Умное определение контекста по тексту закрываемой карточки
    is_overdue = False
    match = re.search(r"Дедлайн:\s*(\d{2}\.\d{2}\.\d{4})", call.message.text)
    if match:
        try:
            task_date = datetime.strptime(match.group(1), "%d.%m.%Y").date()
            if task_date < now:
                is_overdue = True
        except ValueError:
            pass

    # Восстанавливаем именно тот список, из которого была открыта задача
    if is_overdue:
        # ИСПРАВЛЕНО: Убрали .date()
        overdue_tasks = [t for t in tasks if t.deadline and t.deadline < now]
        if not overdue_tasks:
            await call.message.edit_text("🎉 Отлично! У вас больше нет просроченных задач.")
            await call.answer()
            return
            
        text = "🚨 <b>Просроченные задачи:</b>\n\n"
        for i, task in enumerate(overdue_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y")
            text += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
        text += "<i>Выберите просроченную задачу для работы:</i>"
        keyboard = get_today_tasks_keyboard(overdue_tasks)
    else:
        # ИСПРАВЛЕНО: Убрали .date()
        today_tasks = [t for t in tasks if not t.deadline or t.deadline >= now]
        if not today_tasks:
            await call.message.edit_text("🎉 Отлично! У вас больше нет задач на сегодня.")
            await call.answer()
            return
            
        text = "📅 <b>Задачи на сегодня:</b>\n\n"
        for i, task in enumerate(today_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Без дедлайна"
            text += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
        text += "<i>Выберите задачу на сегодня для работы:</i>"
        keyboard = get_today_tasks_keyboard(today_tasks)
        
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await call.answer()