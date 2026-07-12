from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    YOUGILE_TOKEN: str
    YOUGILE_API_URL: str = "https://ru.yougile.com/api-v2"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    TIMEZONE: str = "Europe/Moscow"
    YOUGILE_INBOX_COLUMN_ID: str # ID колонки для новых задач
    YOUGILE_CHECKS_COLUMN_ID: str   # Материалы
    YOUGILE_REGIONAL_COLUMN_ID: str # Поручения
    YOUGILE_TODAY_COLUMN_ID: str # сегодняшние задачи
    ID_COMPANY: str = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()