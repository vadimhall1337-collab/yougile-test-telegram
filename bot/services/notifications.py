import time
from datetime import datetime
from aiogram import Bot
from repositories.tasks import TaskRepository
from repositories.database.users import UserSettingsRepository
import structlog

logger = structlog.get_logger(__name__)

class NotificationService:
    def __init__(self, bot: Bot, task_repo: TaskRepository, user_repo: UserSettingsRepository):
        self._bot = bot
        self._task_repo = task_repo
        self._user_repo = user_repo

    async def send_morning_summary(self, telegram_id: int):
        """Формирует и отправляет утреннюю сводку."""
        try:
            # Получаем все задачи на сегодня (включая просроченные)
            tasks = await self._task_repo.get_today_tasks()
            
            overdue = []
            today = []
            current_time = time.time()
            
            for task in tasks:
                if task.completed or task.deleted or task.archived:
                    continue
                if task.timestamp and task.timestamp < current_time:
                    overdue.append(task)
                else:
                    today.append(task)

            text = (
                f"🌅 <b>Доброе утро. Сегодня:</b>\n\n"
                f"🔴 Просрочено — {len(overdue)}\n"
                f"🟠 Сегодня — {len(today)}\n\n"
            )
            
            # В реальном приложении здесь будет генерация списка с названиями задач
            if overdue or today:
                text += "<i>Откройте раздел «Сегодня» в меню для работы с задачами.</i>"
            else:
                text += "У вас нет активных задач на сегодня. Отличного дня!"
                
            await self._bot.send_message(telegram_id, text, parse_mode="HTML")
            await logger.ainfo("Morning summary sent", user_id=telegram_id)
            
        except Exception as e:
            await logger.aerror("Failed to send morning summary", user_id=telegram_id, error=str(e))

    async def send_evening_summary(self, telegram_id: int):
        """Формирует и отправляет вечернюю сводку."""
        try:
            # Логика подсчета выполненных за день задач (потребует фильтрации по дате завершения)
            # В качестве заглушки архитектуры покажем структуру
            completed_count = 0 
            remaining_count = 0
            
            text = (
                f"🌙 <b>Итоги дня:</b>\n\n"
                f"✅ Сегодня выполнено: {completed_count}\n"
                f"⏳ Осталось: {remaining_count}\n\n"
                f"<i>Хорошего вечера!</i>"
            )
            await self._bot.send_message(telegram_id, text, parse_mode="HTML")
            await logger.ainfo("Evening summary sent", user_id=telegram_id)
        except Exception as e:
            await logger.aerror("Failed to send evening summary", user_id=telegram_id, error=str(e))

    async def send_delayed_reminder(self, telegram_id: int, task_id: str, task_title: str):
        """Отправляет отложенное уведомление (напоминание)."""
        text = f"⏰ <b>Напоминание о задаче:</b>\n\n☐ {task_title}"
        
        # В реальном коде мы прикрепим Inline-кнопку для перехода к задаче
        await self._bot.send_message(telegram_id, text, parse_mode="HTML")