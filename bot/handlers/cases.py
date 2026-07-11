from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline.work import NavigationCallback
from bot.keyboards.inline.cases import get_cases_list_keyboard, get_case_tree_keyboard
from bot.services.navigation import NavigationService
from bot.services.tree import TaskTreeService
from bot.repositories.tasks import TaskRepository
from bot.repositories.cases import CaseRepository
from bot.config.settings import config

cases_router = Router(name="cases_router")

# Локальные сервисы, не требующие внешних зависимостей (БД/API)
nav_service = NavigationService()
tree_service = TaskTreeService()

@cases_router.callback_query(NavigationCallback.filter(F.target == "cases"))
async def process_cases_list(query: CallbackQuery, state: FSMContext, case_repo: CaseRepository):
    """Отображение списка активных кейсов (без служебных колонок)."""
    await nav_service.push_screen(state, "cases_list")
    
    # Получаем активные кейсы через репозиторий
    cases = await case_repo.get_active_cases()
    
    await query.message.edit_text(
        text="🏠 <b>Список активных кейсов</b>\n\nВыберите нужный кейс:",
        reply_markup=get_cases_list_keyboard(cases),
        parse_mode="HTML"
    )
    await query.answer()

@cases_router.callback_query(NavigationCallback.filter(F.target == "case_tree"))
async def process_case_tree(query: CallbackQuery, callback_data: NavigationCallback, state: FSMContext, task_repo: TaskRepository):
    """Отображение дерева задач внутри конкретного выбранного кейса."""
    case_id = callback_data.id
    
    # Фиксируем переход в FSM, сохраняя ID кейса для корректного возврата
    await nav_service.push_screen(state, f"case_tree_{case_id}")
    
    # Получаем все задачи кейса
    tasks = await task_repo.get_case_tree(case_id)
    
    if not tasks:
        await query.answer("В этом кейсе пока нет задач.", show_alert=True)
        return
        
    # Строим иерархию с визуальными отступами
    visual_tree = tree_service.build_visual_tree(tasks)
    
    await query.message.edit_text(
        text="📂 <b>Дерево задач</b>\n\nВыберите задачу для просмотра:",
        reply_markup=get_case_tree_keyboard(visual_tree, case_id),
        parse_mode="HTML"
    )
    await query.answer()

@cases_router.callback_query(NavigationCallback.filter(F.target == "checks"))
async def process_checks_direct(query: CallbackQuery, state: FSMContext, task_repo: TaskRepository):
    """Прямой переход в колонку 'Материалы' (Проверки)."""
    column_id = config.YOUGILE_CHECKS_COLUMN_ID
    
    await nav_service.push_screen(state, "checks_root")
    
    tasks = await task_repo.get_case_tree(column_id)
    if not tasks:
        await query.answer("В колонке проверок пока нет задач.", show_alert=True)
        return
        
    visual_tree = tree_service.build_visual_tree(tasks)
    await query.message.edit_text(
        text="✅ <b>Проверки (Материалы)</b>\n\nВыберите задачу:",
        reply_markup=get_case_tree_keyboard(visual_tree, column_id),
        parse_mode="HTML"
    )
    await query.answer()

@cases_router.callback_query(NavigationCallback.filter(F.target == "regional"))
async def process_regional_direct(query: CallbackQuery, state: FSMContext, task_repo: TaskRepository):
    """Прямой переход в колонку 'Поручения' (Региональные поручения)."""
    column_id = config.YOUGILE_REGIONAL_COLUMN_ID
    
    await nav_service.push_screen(state, "regional_root")
    
    tasks = await task_repo.get_case_tree(column_id)
    if not tasks:
        await query.answer("Поручений пока нет.", show_alert=True)
        return
        
    visual_tree = tree_service.build_visual_tree(tasks)
    await query.message.edit_text(
        text="🌍 <b>Региональные поручения</b>\n\nВыберите поручение:",
        reply_markup=get_case_tree_keyboard(visual_tree, column_id),
        parse_mode="HTML"
    )
    await query.answer()