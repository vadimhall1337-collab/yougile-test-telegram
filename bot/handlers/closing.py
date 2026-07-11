from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.inline.tasks import TaskAction
from keyboards.inline.closing import ConfirmCloseCallback, get_confirm_closing_keyboard
from services.task_closing import TaskClosingService

closing_router = Router(name="closing_router")
# В production внедряется через Dependency Injection
# task_closing_service = TaskClosingService(...) 

@closing_router.callback_query(TaskAction.filter(F.action == "complete"))
async def process_task_complete(query: CallbackQuery, callback_data: TaskAction, task_closing_service: TaskClosingService):
    """Первичная обработка нажатия '✅ Выполнить'."""
    task_id = callback_data.task_id
    
    # Проверяем наличие незавершенных подзадач через бизнес-слой
    has_uncompleted = await task_closing_service.check_uncompleted_subtasks(task_id)
    
    if has_uncompleted:
        # Показываем предупреждение и запрашиваем подтверждение
        warning_text = (
            "⚠️ <b>Внутри закрываемой задачи остались незавершенные подзадачи.</b>\n\n"
            "Отметить выполненной всю задачу вместе со всеми вложенными подзадачами?"
        )
        await query.message.edit_text(
            text=warning_text,
            reply_markup=get_confirm_closing_keyboard(task_id),
            parse_mode="HTML"
        )
    else:
        # Если подзадач нет, сразу закрываем
        await task_closing_service.complete_task_tree(task_id)
        await query.message.edit_text("✅ <i>Задача успешно выполнена.</i>", parse_mode="HTML")
        
    await query.answer()

@closing_router.callback_query(ConfirmCloseCallback.filter())
async def process_close_confirmation(query: CallbackQuery, callback_data: ConfirmCloseCallback, task_closing_service: TaskClosingService):
    """Обработка кнопок 'Да'/'Нет' при каскадном закрытии."""
    
    if callback_data.confirm:
        # Пользователь нажал 'Да'
        await query.answer("Закрытие ветки задач...", show_alert=False)
        await task_closing_service.complete_task_tree(callback_data.task_id)
        await query.message.edit_text("✅ <i>Задача и все её подзадачи успешно выполнены.</i>", parse_mode="HTML")
    else:
        # Пользователь нажал 'Нет' - отменяем действие
        # Возвращаем пользователя на шаг назад (можно использовать NavigationService из Этапа 6)
        await query.message.edit_text("❌ <i>Закрытие отменено.</i>", parse_mode="HTML")
        
    await query.answer()