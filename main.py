import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'bot')))

import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config.settings import config
from bot.yougile.client import YouGileClient
from bot.utils.cache import MemoryCache
from bot.repositories.tasks import TaskRepository
from bot.repositories.database.users import UserSettingsRepository
from bot.services.tasks import TaskService
from bot.services.notifications import NotificationService
from bot.scheduler.setup import setup_scheduler
from bot.repositories.cases import CaseRepository
from bot.database.session import async_session_maker
from bot.services.task_creation import TaskCreationService
from bot.services.task_closing import TaskClosingService
from bot.services.users import UserService

from bot.handlers.start import start_router
from bot.handlers.today import today_router
from bot.handlers.work import work_router
from bot.handlers.cases import cases_router
from bot.handlers.creation import creation_router
from bot.handlers.closing import closing_router
from bot.handlers.settings import settings_router

logger = structlog.get_logger(__name__)

async def main():
    await logger.ainfo("Starting YouGile Telegram Bot...")
    
    yougile_client = YouGileClient(api_key=config.YOUGILE_TOKEN, base_url=config.YOUGILE_API_URL)
    cache_service = MemoryCache()
    
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(token=config.BOT_TOKEN)
    
    task_repo = TaskRepository(client=yougile_client, cache=cache_service)
    case_repo = CaseRepository(client=yougile_client, cache=cache_service)
    user_repo = UserSettingsRepository(session_factory=async_session_maker)
    
    task_service = TaskService(task_repo=task_repo)
    task_creation_service = TaskCreationService(task_repo=task_repo, config=config) 
    task_closing_service = TaskClosingService(task_repo=task_repo)
    user_service = UserService(user_repo=user_repo)
    notification_service = NotificationService(bot=bot, task_repo=task_repo, user_repo=user_repo)
    
    scheduler = setup_scheduler(notification_service=notification_service, user_repo=user_repo)
    scheduler.start()
    
    dp.include_routers(
        start_router, today_router, work_router, 
        cases_router, creation_router, closing_router, settings_router
    )
    
    dp.workflow_data.update(
        task_service=task_service,
        task_creation_service=task_creation_service, # Добавили
        task_closing_service=task_closing_service,   # Добавили
        user_service=user_service,                   # Добавили
        notification_service=notification_service,
        db_user_repo=user_repo,
        config=config,
        case_repo=case_repo,
        task_repo=task_repo
    )
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await logger.ainfo("Shutting down YouGile Bot...")
        scheduler.shutdown()
        await yougile_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())