from aiogram.fsm.context import FSMContext
import structlog

logger = structlog.get_logger(__name__)

class UserService:
    """Сервис для управления сессиями и профилями пользователей."""
    
    async def process_start_command(self, user_id: int, username: str, state: FSMContext) -> str:
        """
        Бизнес-логика обработки команды /start.
        """
        # Очищаем состояние и стек навигации при возврате в главное меню,
        # чтобы предотвратить зависание пользователя в глубоких меню.
        await state.clear()
        
        await logger.ainfo("User started the bot", user_id=user_id, username=username)
        
        return f"Приветствую, {username}! Выберите нужный раздел в меню ниже."