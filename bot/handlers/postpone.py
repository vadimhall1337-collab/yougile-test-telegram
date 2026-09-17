from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.inline.tasks import TaskActionCallback
from bot.services.task_postpone import TaskPostponeService

postpone_router = Router(name="postpone_router")

@postpone_router.callback_query(TaskActionCallback.filter(F.action == "postpone"))
async def process_task_postpone(query: CallbackQuery, callback_data: TaskActionCallback, task_postpone_service: TaskPostponeService):
    """
    Обработка нажатия кнопки '🕒 Отложить'.
    Показывает пользователю варианты колонок для перемещения задачи.
    """
    task_id = callback_data.task_id
    
    # Получаем задачу через сервис
    try:
        task = await task_postpone_service.get_task_with_details(task_id)
    except Exception as e:
        await query.answer(f"❌ Задача не найдена: {str(e)}", show_alert=True)
        return
    
    # Получаем доступные колонки для перемещения
    columns = await task_postpone_service.get_available_columns_for_task(task)
    
    if not columns:
        await query.answer("❌ Нет доступных колонок для перемещения.", show_alert=True)
        return
    
    # Формируем текст сообщения
    text = (
        f"🕒 <b>Перемещение задачи</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{task.title}</b>\n\n"
        f"Выберите колонку, в которую хотите переместить задачу:"
    )
    
    # Создаём клавиатуру с колонками
    builder = InlineKeyboardBuilder()
    
    for col in columns:
        col_name = col["title"][:30] + "..." if len(col["title"]) > 30 else col["title"]
        builder.button(
            text=f"📁 {col_name}",
            callback_data=f"postpone_move:{task_id}:{col['id']}"
        )
    
    # Кнопка отмены
    builder.button(
        text="❌ Отмена",
        callback_data=f"postpone_cancel:{task_id}"
    )
    
    builder.adjust(1)
    
    await query.message.edit_text(
        text=text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await query.answer()


@postpone_router.callback_query(F.data.startswith("postpone_move:"))
async def process_postpone_move(query: CallbackQuery, task_postpone_service: TaskPostponeService):
    """
    Обработка выбора колонки для перемещения задачи.
    """
    # Парсим callback_data: postpone_move:{task_id}:{column_id}
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("❌ Ошибка формата данных.", show_alert=True)
        return
    
    task_id = parts[1]
    new_column_id = parts[2]
    
    try:
        # Перемещаем задачу в выбранную колонку через сервис
        updated_task = await task_postpone_service.move_task_to_column(task_id, new_column_id)
        
        await query.message.edit_text(
            text=f"✅ <i>Задача «{updated_task.title}» перемещена в другую колонку.</i>",
            parse_mode="HTML"
        )
        await query.answer("Задача перемещена!", show_alert=False)
        
    except Exception as e:
        await query.answer(f"❌ Ошибка при перемещении: {str(e)}", show_alert=True)


@postpone_router.callback_query(F.data.startswith("postpone_cancel:"))
async def process_postpone_cancel(query: CallbackQuery, task_postpone_service: TaskPostponeService):
    """
    Обработка отмены перемещения задачи.
    Возвращает карточку задачи.
    """
    # Парсим callback_data: postpone_cancel:{task_id}
    parts = query.data.split(":")
    if len(parts) != 2:
        await query.answer("❌ Ошибка формата данных.", show_alert=True)
        return
    
    task_id = parts[1]
    
    try:
        from bot.keyboards.inline.tasks import get_task_detail_keyboard
        
        task = await task_postpone_service.get_task_with_details(task_id)
        
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
        
        await query.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await query.answer("Отменено.")
        
    except Exception as e:
        await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
