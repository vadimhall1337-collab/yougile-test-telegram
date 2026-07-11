from aiogram.fsm.state import StatesGroup, State

class CreateTaskState(StatesGroup):
    """Состояния для пошагового создания новой задачи (Этап 8)"""
    waiting_for_destination = State()
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()

class EditSettingsState(StatesGroup):
    """Состояния для изменения настроек уведомлений в меню (Этап 10)"""
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()
    waiting_for_reminder_mins = State()