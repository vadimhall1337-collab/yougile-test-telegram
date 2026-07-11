from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import structlog

logger = structlog.get_logger(__name__)

class NavigationService:
    """Сервис инкапсулирует логику работы со стеком экранов в Redis/FSM."""
    
    async def push_screen(self, state: FSMContext, screen_identifier: str) -> None:
        """Добавляет новый экран в конец стека."""
        data = await state.get_data()
        stack = data.get("navigation_stack", [])
        
        # Защита от дублирования при повторном нажатии одной и той же кнопки
        if not stack or stack[-1] != screen_identifier:
            stack.append(screen_identifier)
            await state.update_data(navigation_stack=stack)
            await logger.adebug("Pushed to stack", current_stack=stack)

    async def pop_screen(self, state: FSMContext) -> str:
        """
        Извлекает текущий экран и возвращает идентификатор предыдущего.
        Если стек пуст или мы на верхнем уровне, возвращает маркер 'main_menu'.
        """
        data = await state.get_data()
        stack = data.get("navigation_stack", [])
        
        if len(stack) > 1:
            stack.pop() # Удаляем текущий экран
            previous_screen = stack[-1] # Смотрим, что было до него
            await state.update_data(navigation_stack=stack)
            await logger.adebug("Popped from stack", new_stack=stack, previous=previous_screen)
            return previous_screen
            
        # Если история закончилась, принудительно очищаем ее и возвращаем в корень
        await state.update_data(navigation_stack=["main_menu"])
        return "main_menu"
        
    async def clear_stack(self, state: FSMContext) -> None:
        """Сброс навигации (например, при вызове /start или кнопки 'Главное меню')."""
        await state.update_data(navigation_stack=["main_menu"])