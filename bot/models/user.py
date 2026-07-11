from sqlalchemy import BigInteger, Integer, Time, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import time

class Base(DeclarativeBase):
    pass

class UserSettings(Base):
    __tablename__ = "user_settings"

    # ID пользователя в Telegram
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True) 
    
    # Настройки по умолчанию
    morning_summary_time: Mapped[time] = mapped_column(Time, default=time(8, 30))
    evening_summary_time: Mapped[time] = mapped_column(Time, default=time(18, 0))
    default_reminder_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Рабочие дни. Используем JSON вместо ARRAY для совместимости с SQLite
    working_days: Mapped[list[int]] = mapped_column(JSON, default=[0, 1, 2, 3, 4])