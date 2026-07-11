from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import UserSettings
from typing import List, Optional, Dict, Any

class UserSettingsRepository:
    """Репозиторий для работы с локальной базой данных пользователей."""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_or_create(self, telegram_id: int) -> UserSettings:
        """Получает настройки пользователя или создает дефолтные."""
        async with self._session_factory() as session:
            stmt = select(UserSettings).where(UserSettings.telegram_id == telegram_id)
            result = await session.execute(stmt)
            settings = result.scalar_one_or_none()
            
            if not settings:
                settings = UserSettings(telegram_id=telegram_id)
                session.add(settings)
                await session.commit()
                await session.refresh(settings)
                
            return settings

    async def update_settings(self, telegram_id: int, updates: Dict[str, Any]) -> UserSettings:
        """Обновляет указанные поля в настройках пользователя."""
        async with self._session_factory() as session:
            settings = await self.get_or_create(telegram_id)
            
            for key, value in updates.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                    
            await session.commit()
            return settings
        
    async def get_all_users(self) -> List[UserSettings]:
        """Возвращает список всех пользователей из базы данных."""
        async with self._session_factory() as session:
            # Используем select для получения всех записей
            stmt = select(UserSettings)
            result = await session.execute(stmt)
            # Возвращаем список объектов UserSettings
            return list(result.scalars().all())