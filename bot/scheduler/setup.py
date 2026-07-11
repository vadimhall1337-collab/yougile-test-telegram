from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from scheduler.jobs import dispatcher_job

def setup_scheduler(notification_service, user_repo) -> AsyncIOScheduler:
    """Инициализирует и возвращает настроенный планировщик."""
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    # Регистрируем глобальный диспетчер сводок (запуск каждую минуту)
    scheduler.add_job(
        dispatcher_job,
        trigger=CronTrigger(minute="*"),
        kwargs={
            "notification_service": notification_service,
            "user_repo": user_repo
        },
        id="global_summary_dispatcher",
        replace_existing=True
    )
    
    return scheduler

# Пример того, как обработчик "Отложить" (Этап 5) добавит задачу:
# scheduler.add_job(
#     notification_service.send_delayed_reminder,
#     trigger="date",
#     run_date=datetime.now() + timedelta(minutes=15),
#     kwargs={"telegram_id": 123, "task_id": "abc", "task_title": "Подписать акт"}
# )