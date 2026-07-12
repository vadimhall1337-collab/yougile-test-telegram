import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline.tasks import (
    get_today_tasks_keyboard, 
    get_task_detail_keyboard, 
    TaskDetailCallback, 
)
from bot.repositories.tasks import TaskRepository
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.inline.tasks import TaskActionCallback
from bot.services.navigation import NavigationService

today_router = Router()
nav_service = NavigationService()

# ==========================================
# 1. ОБРАБОТЧИК КНОПКИ "СЕГОДНЯ"
# ==========================================
@today_router.message(F.text == "📅 Сегодня")
async def show_today_tasks(message: Message, task_repo: TaskRepository, state: FSMContext):
    tasks = await task_repo.get_today_tasks()
    
    if not tasks:
        await message.answer("🎉 Отлично! У вас нет просроченных и текущих задач на сегодня.")
        return
        
    now = datetime.now().date()
    
    overdue_tasks = [t for t in tasks if t.deadline and t.deadline < now]
    today_tasks = [t for t in tasks if not t.deadline or t.deadline >= now]
    
    sent_msg_ids = []
    
    # 1. Если есть просроченные, отправляем их отдельным сообщением
    if overdue_tasks:
        text_overdue = "🚨 <b>Просроченные задачи:</b>\n\n"
        for i, task in enumerate(overdue_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y")
            text_overdue += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_overdue += "<i>Выберите просроченную задачу для работы:</i>"
        msg_overdue = await message.answer(
            text_overdue, 
            reply_markup=get_today_tasks_keyboard(overdue_tasks), 
            parse_mode="HTML"
        )
        sent_msg_ids.append(msg_overdue.message_id)
        
    # 2. Отправляем задачи на сегодня
    if today_tasks:
        text_today = "📅 <b>Задачи на сегодня:</b>\n\n"
        for i, task in enumerate(today_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Без дедлайна"
            text_today += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_today += "<i>Выберите задачу на сегодня для работы:</i>"
        msg_today = await message.answer(
            text_today, 
            reply_markup=get_today_tasks_keyboard(today_tasks), 
            parse_mode="HTML"
        )
        sent_msg_ids.append(msg_today.message_id)

    # Сохраняем ID всех созданных сообщений в стейт FSM
    await state.update_data(today_list_msg_ids=sent_msg_ids)
    await nav_service.clear_stack(state)


# ==========================================
# 2. ОБРАБОТЧИК КЛИКА ПО КОНКРЕТНОЙ ЗАДАЧЕ
# ==========================================
@today_router.callback_query(TaskDetailCallback.filter())
async def process_task_detail(call: CallbackQuery, callback_data: TaskDetailCallback, task_repo: TaskRepository, state: FSMContext):
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
    
    # Извлекаем сохраненные ID сообщений списков
    data = await state.get_data()
    msg_ids = data.get("today_list_msg_ids")
    
    if msg_ids:
        # Если мы кликнули по задаче из главного меню списков, удаляем ОБА сообщения
        for msg_id in msg_ids:
            try:
                await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_id)
            except Exception:
                pass
                
        # Стираем список ID из стейта, так как сообщений больше нет
        await state.update_data(today_list_msg_ids=None)
        
        # Отправляем карточку задачи НОВЫМ сообщением
        await call.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Если мы перешли сюда вглубь (из подзадач), просто обновляем текущую карточку (edit)
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    await call.answer()


# ==========================================
# 3. ОБРАБОТЧИК ПОДЗАДАЧ
# ==========================================
@today_router.callback_query(TaskActionCallback.filter(F.action == "subtasks"))
async def process_task_subtasks(call: CallbackQuery, callback_data: TaskActionCallback, task_repo: TaskRepository):
    task_id = callback_data.task_id
    task = await task_repo.get_by_id(task_id)
    
    if not task.subtasks:
        await call.answer("У этой задачи нет подзадач.", show_alert=True)
        return
        
    await call.answer("Загружаю список подзадач...")
    
    text = (
        f"📋 <b>Подзадачи для:</b>\n«{task.title}»\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    builder = InlineKeyboardBuilder()
    
    for idx, sub_id in enumerate(task.subtasks, start=1):
        try:
            sub_task = await task_repo.get_by_id(sub_id)
            status_icon = "✅" if sub_task.completed else "📌"
            
            text += f"{idx}. {status_icon} <b>{sub_task.title}</b>\n"
            
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
            
    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Выберите подзадачу из списка ниже, чтобы открыть её карточку:</i>"
    )
    
    builder.button(
        text="🔙 Назад к родительской задаче", 
        callback_data=TaskDetailCallback(task_id=task_id)
    )
    
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


# ==========================================
# 4. ОБРАБОТЧИК ВОЗВРАТА НАЗАД К СВОЕМУ СПИСКУ
# ==========================================
@today_router.callback_query(F.data == "back_to_today")
async def process_back_to_today(call: CallbackQuery, task_repo: TaskRepository, state: FSMContext):
    # 1. Удаляем текущую карточку задачи (или подзадачи) полностью
    try:
        await call.message.delete()
    except Exception:
        pass

    # 2. Получаем актуальный список задач
    tasks = await task_repo.get_today_tasks()
    
    if not tasks:
        await call.message.answer("🎉 Отлично! У вас нет просроченных и текущих задач на сегодня.")
        await call.answer()
        return
        
    now = datetime.now().date()
    overdue_tasks = [t for t in tasks if t.deadline and t.deadline < now]
    today_tasks = [t for t in tasks if not t.deadline or t.deadline >= now]
    
    sent_msg_ids = []
    
    # 3. Заново отправляем просроченные задачи новым сообщением
    if overdue_tasks:
        text_overdue = "🚨 <b>Просроченные задачи:</b>\n\n"
        for i, task in enumerate(overdue_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y")
            text_overdue += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_overdue += "<i>Выберите просроченную задачу для работы:</i>"
        msg_overdue = await call.message.answer(
            text_overdue, 
            reply_markup=get_today_tasks_keyboard(overdue_tasks), 
            parse_mode="HTML"
        )
        sent_msg_ids.append(msg_overdue.message_id)
        
    # 4. Заново отправляем задачи на сегодня вторым сообщением
    if today_tasks:
        text_today = "📅 <b>Задачи на сегодня:</b>\n\n"
        for i, task in enumerate(today_tasks, 1):
            deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Без дедлайна"
            text_today += f"{i}. 📌 <b>{task.title}</b>\n   ⏳ Дедлайн: <code>{deadline_str}</code>\n\n"
            
        text_today += "<i>Выберите задачу на сегодня для работы:</i>"
        msg_today = await call.message.answer(
            text_today, 
            reply_markup=get_today_tasks_keyboard(today_tasks), 
            parse_mode="HTML"
        )
        sent_msg_ids.append(msg_today.message_id)
        
    # 5. Снова сохраняем новые ID сообщений в стейт, чтобы они удалились при следующем клике
    await state.update_data(today_list_msg_ids=sent_msg_ids)
    await nav_service.clear_stack(state)
    
    await call.answer()