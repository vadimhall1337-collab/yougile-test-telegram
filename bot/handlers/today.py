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
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.inline.tasks import TaskActionCallback

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

# Обработчик выбора подзадач.
@today_router.callback_query(TaskActionCallback.filter(F.action == "subtasks"))
async def process_task_subtasks(call: CallbackQuery, callback_data: TaskActionCallback, task_repo: TaskRepository):
    task_id = callback_data.task_id
    task = await task_repo.get_by_id(task_id)
    
    if not task.subtasks:
        await call.answer("У этой задачи нет подзадач.", show_alert=True)
        return
        
    await call.answer("Загружаю список подзадач...")
    
    # Шапка сообщения
    text = (
        f"📋 <b>Подзадачи для:</b>\n«{task.title}»\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    builder = InlineKeyboardBuilder()
    
    # В одном цикле собираем и полный текстовый список, и инлайн-кнопки
    for idx, sub_id in enumerate(task.subtasks, start=1):
        try:
            sub_task = await task_repo.get_by_id(sub_id)
            status_icon = "✅" if sub_task.completed else "📌"
            
            # 1. Добавляем в текст сообщения ПОЛНОЕ (неурезанное) название подзадачи
            text += f"{idx}. {status_icon} <b>{sub_task.title}</b>\n"
            
            # 2. Обрезаем название исключительно для инлайн-кнопки
            sub_title = sub_task.title if len(sub_task.title) <= 25 else sub_task.title[:22] + "..."
            button_text = f"{idx}. {status_icon} {sub_title}"
            
            builder.button(
                text=button_text,
                callback_data=TaskDetailCallback(task_id=sub_task.id)
            )
        except Exception:
            text += f"{idx}. ❌ Ошибка загрузки подзадачи (ID: {sub_id})\n"
            builder.button(
                text=f"{idx}. ❌ Ошибка загрузки",
                callback_data="invalid_subtask_click"
            )
            
    # Подвал сообщения под текстовым списком задач
    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите подзадачу из списка ниже, чтобы открыть её карточку:</i>"
    )
    
    # Кнопка возврата к родительской задаче
    builder.button(
        text="🔙 Назад к родительской задаче", 
        callback_data=TaskDetailCallback(task_id=task_id)
    )
    
    # Выстраиваем кнопки в один вертикальный ряд
    builder.adjust(1)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    
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