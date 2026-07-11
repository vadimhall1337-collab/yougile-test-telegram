from datetime import datetime
from services.notifications import NotificationService
from repositories.database.users import UserSettingsRepository

async def dispatcher_job(notification_service: NotificationService, user_repo: UserSettingsRepository):
    """
    Глобальная задача. Запускается каждую минуту.
    Проверяет настройки пользователей и рассылает сводки.
    """
    now = datetime.now()
    current_time = now.time().replace(second=0, microsecond=0)
    current_weekday = now.weekday() # 0 = Понедельник, 6 = Воскресенье
    
    # В реальном репозитории нам потребуется метод get_all_users()
    users_settings = await user_repo.get_all_users()
    
    for settings in users_settings:
        # Проверяем, рабочий ли сегодня день для пользователя
        if current_weekday not in settings.working_days:
            continue
            
        # Проверка утренней сводки
        if settings.morning_summary_time.replace(second=0, microsecond=0) == current_time:
            await notification_service.send_morning_summary(settings.telegram_id)
            
        # Проверка вечерней сводки
        if settings.evening_summary_time.replace(second=0, microsecond=0) == current_time:
            await notification_service.send_evening_summary(settings.telegram_id)