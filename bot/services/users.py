from aiogram.fsm.context import FSMContext
import structlog
from bot.repositories.database.users import UserSettingsRepository

logger = structlog.get_logger(__name__)

class UserService:
    """Сервис для управления сессиями и профилями пользователей."""
    
    def __init__(self, user_repo: UserSettingsRepository = None):
        self.user_repo = user_repo
    
    async def process_start_command(self, user_id: int, username: str, state: FSMContext) -> str:
        """
        Бизнес-логика обработки команды /start.
        """
        await state.clear()
        
        if self.user_repo:
            await self.user_repo.get_or_create(user_id)
        
        await logger.ainfo("User started the bot", user_id=user_id, username=username)
        
        return f"Приветствую, {username}! Выберите нужный раздел в меню ниже."