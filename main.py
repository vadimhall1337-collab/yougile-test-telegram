import sys
import os
# Указываем интерпретатору искать модули внутри папки bot/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'bot')))

import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import config
from yougile.client import YouGileClient
from utils.cache import MemoryCache
from repositories.tasks import TaskRepository
from repositories.database.users import UserSettingsRepository
from services.tasks import TaskService
from services.notifications import NotificationService
from scheduler.setup import setup_scheduler
from repositories.cases import CaseRepository
from database.session import async_session_maker

# Импорт роутеров, созданных на предыдущих этапах
from handlers.start import start_router
from handlers.today import today_router
from handlers.work import work_router
from handlers.cases import cases_router
from handlers.creation import creation_router
from handlers.closing import closing_router
from handlers.settings import settings_router

logger = structlog.get_logger(__name__)

async def main():
    await logger.ainfo("Starting YouGile Telegram Bot...")
    
    # 1. Инициализация клиентов, хранилищ и кэша
    yougile_client = YouGileClient(api_key=config.YOUGILE_TOKEN, base_url=config.YOUGILE_API_URL)
    cache_service = MemoryCache()
    
    # Инициализация Диспетчера aiogram с MemoryStorage для хранения состояний
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(token=config.BOT_TOKEN)
    
    # 2. Инициализация слоя репозиториев (с передачей реальных фабрик сессий и клиентов)
    task_repo = TaskRepository(client=yougile_client, cache=cache_service)
    case_repo = CaseRepository(client=yougile_client, cache=cache_service)
    user_repo = UserSettingsRepository(session_factory=async_session_maker)
    
    # 3. Инициализация бизнес-логики (Service Layer)
    task_service = TaskService(task_repo=task_repo)
    
    # Инициализация сервиса уведомлений для планировщика
    notification_service = NotificationService(bot=bot, task_repo=task_repo, user_repo=user_repo)
    
    # 4. Запуск фонового планировщика задач APScheduler
    scheduler = setup_scheduler(notification_service=notification_service, user_repo=user_repo)
    scheduler.start()
    
    # 5. Регистрация роутеров в диспетчере
    dp.include_routers(
        start_router, today_router, work_router, 
        cases_router, creation_router, closing_router, settings_router
    )
    
    # 6. Внедрение зависимостей (DI) — прокидываем сервисы и репозитории во все хэндлеры
    dp.workflow_data.update(
        task_service=task_service,
        notification_service=notification_service,
        db_user_repo=user_repo,
        config=config,
        case_repo=case_repo,
        task_repo=task_repo
    )
    
    try:
        # Сбрасываем старые зависшие сообщения в Telegram-боте перед стартом
        await bot.delete_webhook(drop_pending_updates=True)
        # Запуск прослушивания обновлений
        await dp.start_polling(bot)
    finally:
        await logger.ainfo("Shutting down YouGile Bot...")
        scheduler.shutdown()
        await yougile_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())