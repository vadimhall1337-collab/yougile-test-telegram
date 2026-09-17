import re
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline.tasks import (
    TaskActionCallback,
    EditFieldCallback,
    get_edit_menu_keyboard,
    get_task_detail_keyboard,
    get_cancel_edit_keyboard,
)
from bot.services.task_edit import TaskEditService
from bot.states.edit import EditTaskState

edit_router = Router(name="edit_router")

# ==========================================
# 1. ВХОД В РЕЖИМ РЕДАКТИРОВАНИЯ
# ==========================================
@edit_router.callback_query(TaskActionCallback.filter(F.action == "edit"))
async def process_edit_start(query: CallbackQuery, callback_data: TaskActionCallback, task_edit_service: TaskEditService):
    """Начало редактирования задачи - показ меню выбора поля."""
    task_id = callback_data.task_id
    
    try:
        task = await task_edit_service.get_task(task_id)
    except Exception as e:
        await query.answer(f"❌ Задача не найдена: {str(e)}", show_alert=True)
        return
    
    text = (
        f"✏️ <b>Редактирование задачи</b>\\n"
        f"━━━━━━━━━━━━━━━━━━━━\\n"
        f"📌 <b>{task.title}</b>\\n\\n"
        f"Выберите поле для редактирования:"
    )
    
    keyboard = get_edit_menu_keyboard(task_id)
    
    await query.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await query.answer()


# ==========================================
# 2. ВЫБОР ПОЛЯ ДЛЯ РЕДАКТИРОВАНИЯ
# ==========================================
@edit_router.callback_query(EditFieldCallback.filter())
async def process_field_selection(query: CallbackQuery, callback_data: EditFieldCallback, task_edit_service: TaskEditService, state: FSMContext):
    """Обработка выбора поля для редактирования."""
    task_id = callback_data.task_id
    field = callback_data.field
    
    try:
        task = await task_edit_service.get_task(task_id)
    except Exception as e:
        await query.answer(f"❌ Задача не найдена: {str(e)}", show_alert=True)
        return
    
    # Сохраняем контекст в FSM
    await state.update_data(edit_task_id=task_id, edit_field=field, original_title=task.title)
    
    if field == "title":
        text = (
            f"📝 <b>Изменение названия</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"Текущее название: <i>{task.title}</i>\\n\\n"
            f"Отправьте новое название задачи:\\n"
            f"(или нажмите 'Отмена' для отмены)"
        )
        
        await state.set_state(EditTaskState.waiting_for_new_title)
        await query.message.edit_text(
            text=text,
            reply_markup=get_cancel_edit_keyboard(task_id),
            parse_mode="HTML"
        )
        
    elif field == "description":
        current_desc = task.description if task.description else "Не указано"
        text = (
            f"📄 <b>Изменение описания</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"Текущее описание: <i>{current_desc}</i>\\n\\n"
            f"Отправьте новое описание задачи:\\n"
            f"(или нажмите 'Отмена', или отправьте '-' для удаления описания)"
        )
        
        await state.set_state(EditTaskState.waiting_for_new_description)
        await query.message.edit_text(
            text=text,
            reply_markup=get_cancel_edit_keyboard(task_id),
            parse_mode="HTML"
        )
        
    elif field == "deadline":
        current_deadline = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
        text = (
            f"📅 <b>Изменение дедлайна</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"Текущий дедлайн: <i>{current_deadline}</i>\\n\\n"
            f"Отправьте новую дату в формате ДД.ММ.ГГГГ:\\n"
            f"<i>(например: 25.12.2024)</i>\\n\\n"
            f"Или нажмите 'Отмена' для отмены"
        )
        
        await state.set_state(EditTaskState.waiting_for_new_deadline_date)
        await query.message.edit_text(
            text=text,
            reply_markup=get_cancel_edit_keyboard(task_id),
            parse_mode="HTML"
        )
    
    await query.answer()


# ==========================================
# 3. ОБРАБОТКА НОВОГО НАЗВАНИЯ
# ==========================================
@edit_router.message(EditTaskState.waiting_for_new_title)
async def process_new_title(message: Message, state: FSMContext, task_edit_service: TaskEditService):
    """Обработка нового названия задачи."""
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    new_title = message.text.strip()
    
    if not new_title:
        await message.answer("❌ Название не может быть пустым.")
        return
    
    try:
        await task_edit_service.update_title(task_id, new_title)
        
        # Возвращаем карточку задачи
        task = await task_edit_service.get_task(task_id)
        deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
        
        text = (
            f"✅ <b>Название обновлено!</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"📌 <b>{task.title}</b>\\n"
            f"⏳ <b>Дедлайн:</b> <code>{deadline_str}</code>"
        )
        
        await message.answer(
            text=text,
            reply_markup=get_task_detail_keyboard(task),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении: {str(e)}")
    
    finally:
        await state.clear()


# ==========================================
# 4. ОБРАБОТКА НОВОГО ОПИСАНИЯ
# ==========================================
@edit_router.message(EditTaskState.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext, task_edit_service: TaskEditService):
    """Обработка нового описания задачи."""
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    new_description = message.text.strip()
    
    # Если пользователь отправил "-", удаляем описание
    if new_description == "-":
        new_description = None
    
    try:
        await task_edit_service.update_description(task_id, new_description)
        
        # Возвращаем карточку задачи
        task = await task_edit_service.get_task(task_id)
        deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
        
        desc_text = task.description if task.description else "Описание отсутствует"
        
        text = (
            f"✅ <b>Описание обновлено!</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"📌 <b>{task.title}</b>\\n"
            f"⏳ <b>Дедлайн:</b> <code>{deadline_str}</code>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"💬 <b>Описание:</b>\\n<i>{desc_text}</i>"
        )
        
        await message.answer(
            text=text,
            reply_markup=get_task_detail_keyboard(task),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении: {str(e)}")
    
    finally:
        await state.clear()


# ==========================================
# 5. ОБРАБОТКА НОВОГО ДЕДЛАЙНА
# ==========================================
@edit_router.message(EditTaskState.waiting_for_new_deadline_date)
async def process_new_deadline(message: Message, state: FSMContext, task_edit_service: TaskEditService):
    """Обработка новой даты дедлайна."""
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    date_text = message.text.strip()
    
    # Парсим дату в формате ДД.ММ.ГГГГ
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not re.match(date_pattern, date_text):
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например: 25.12.2024)"
        )
        return
    
    try:
        new_deadline = datetime.strptime(date_text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверная дата. Проверьте корректность введенных данных.")
        return
    
    try:
        await task_edit_service.update_deadline(task_id, new_deadline)
        
        # Возвращаем карточку задачи
        task = await task_edit_service.get_task(task_id)
        deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
        
        text = (
            f"✅ <b>Дедлайн обновлен!</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"📌 <b>{task.title}</b>\\n"
            f"⏳ <b>Новый дедлайн:</b> <code>{deadline_str}</code>"
        )
        
        await message.answer(
            text=text,
            reply_markup=get_task_detail_keyboard(task),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении: {str(e)}")
    
    finally:
        await state.clear()


# ==========================================
# 6. ОТМЕНА РЕДАКТИРОВАНИЯ
# ==========================================
@edit_router.callback_query(TaskActionCallback.filter(F.action == "cancel_edit"))
async def process_cancel_edit(query: CallbackQuery, callback_data: TaskActionCallback, task_edit_service: TaskEditService, state: FSMContext):
    """Отмена редактирования и возврат к карточке задачи."""
    task_id = callback_data.task_id
    
    try:
        task = await task_edit_service.get_task(task_id)
        
        deadline_str = task.deadline.strftime("%d.%m.%Y") if task.deadline else "Не установлен"
        
        text = (
            f"📌 <b>Карточка задачи</b>\\n"
            f"━━━━━━━━━━━━━━━━━━━━\\n"
            f"📝 <b>Название:</b> {task.title}\\n"
            f"⏳ <b>Дедлайн:</b> <code>{deadline_str}</code>\\n"
        )
        
        if hasattr(task, 'description') and task.description:
            text += f"━━━━━━━━━━━━━━━━━━━━\\n💬 <b>Описание:</b>\\n<i>{task.description}</i>"
        
        keyboard = get_task_detail_keyboard(task)
        
        await query.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await query.answer("Редактирование отменено.")
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    
    finally:
        await state.clear()
