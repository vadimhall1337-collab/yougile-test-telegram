from aiogram.fsm.state import StatesGroup, State

class EditTaskState(StatesGroup):
    """Состояния для пошагового редактирования задачи"""
    waiting_for_field = State()  # Выбор поля для редактирования (title, description, deadline)
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_deadline_date = State()
    waiting_for_new_deadline_time = State()
