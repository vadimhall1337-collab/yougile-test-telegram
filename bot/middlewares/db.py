from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для прокидывания сессии базы данных в каждый запрос Telegram.
    """
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Открываем сессию перед обработкой события
        async with self.session_pool() as session:
            # Передаем сессию в словарь data, чтобы она была доступна в handlers
            data["db_session"] = session
            # Передаем управление дальше по цепочке
            return await handler(event, data)