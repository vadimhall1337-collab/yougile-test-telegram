# Реализация кнопки "🕒 Отложить" для Telegram-бота YouGile

## Обзор

Реализован полный цикл функционала для откладывания задач (перемещения между колонками) в интеграции Telegram-бота с YouGile API v2.

## Архитектура решения

### 1. Сервисный слой (`bot/services/task_postpone.py`)

**Класс:** `TaskPostponeService`

**Методы:**
- `get_board_columns(board_id)` - получение списка колонок доски
- `get_available_columns_for_task(task)` - получение доступных колонок для перемещения (исключая текущую)
- `move_task_to_column(task_id, new_column_id)` - перемещение задачи в новую колонку
- `get_task_with_details(task_id)` - получение полной информации о задаче

**Принципы:**
- Инкапсуляция бизнес-логики
- Логирование всех операций через structlog
- Работа через репозиторий для кэширования

### 2. Обработчики (`bot/handlers/postpone.py`)

**Router:** `postpone_router`

**Обработчики:**

1. **`process_task_postpone`** - начальный обработчик кнопки "🕒 Отложить"
   - Получает задачу по ID
   - Запрашивает доступные колонки
   - Показывает пользователю меню выбора колонки
   - Callback: `task_action:{task_id}:postpone`

2. **`process_postpone_move`** - обработка выбора колонки
   - Парсит callback данные: `postpone_move:{task_id}:{column_id}`
   - Вызывает сервис для перемещения задачи
   - Показывает подтверждение успеха
   - Callback pattern: `postpone_move:*`

3. **`process_postpone_cancel`** - отмена операции
   - Возвращает карточку задачи
   - Callback pattern: `postpone_cancel:*`

### 3. Интеграция в основное приложение (`main.py`)

**Изменения:**
```python
# Импорт сервиса
from bot.services.task_postpone import TaskPostponeService

# Импорт роутера
from bot.handlers.postpone import postpone_router

# Инициализация сервиса
task_postpone_service = TaskPostponeService(task_repo=task_repo)

# Регистрация в workflow_data (Dependency Injection)
dp.workflow_data.update(
    task_postpone_service=task_postpone_service,
    # ...
)

# Подключение роутера
dp.include_routers(
    # ...
    postpone_router
)
```

## Поток данных

```
User → [🕒 Отложить] 
       ↓
process_task_postpone (handler)
       ↓
TaskPostponeService.get_available_columns_for_task()
       ↓
[Меню с колонками]
       ↓
User → [Выбор колонки]
       ↓
process_postpone_move (handler)
       ↓
TaskPostponeService.move_task_to_column()
       ↓
TaskRepository.move() → YouGile API PUT /tasks/{id}
       ↓
[Подтверждение ✅]
```

## YouGile API v2 Endpoints

### GET /columns
Получение списка колонок доски:
```json
{
  "boardId": "c59af5e0-84c6-4e67-8b23-681dd0ddf580",
  "limit": 1000
}
```

### PUT /tasks/{task_id}
Перемещение задачи:
```json
{
  "columnId": "new-column-id"
}
```

## Клавиатуры

Используется существующая клавиатура из `bot/keyboards/inline/tasks.py`:

```python
def get_task_detail_keyboard(task: TaskDto) -> InlineKeyboardMarkup:
    builder.button(
        text="🕒 Отложить",
        callback_data=TaskActionCallback(task_id=task.id, action="postpone")
    )
```

Динамическая клавиатура для выбора колонок создаётся в хендлере.

## Кэширование

Сервис использует кэширование через `TaskRepository`:
- Список колонок кэшируется на уровне репозитория
- Данные задачи кэшируются по ключу `tasks:detail:{task_id}`
- При перемещении задачи кэш автоматически инвалидируется

## Логирование

Все операции логируются через structlog:
```python
await logger.ainfo(
    "Task postponed to column", 
    task_id=task_id, 
    new_column_id=new_column_id,
    task_title=updated_task.title
)
```

## Обработка ошибок

1. **Задача не найдена** - показывается alert с ошибкой
2. **Нет доступных колонок** - уведомление пользователя
3. **Ошибка при перемещении** - detail error message в alert
4. **Некорректный callback** - проверка формата данных

## Расширение функционала

### Возможные улучшения:

1. **Быстрые действия**
   - "Отложить на завтра" (автоматический выбор колонки)
   - "Отложить на неделю"
   - "В архив"

2. **Комментарии**
   - Добавить комментарий при перемещении
   - Уведомление ответственным лицам

3. **Массовые операции**
   - Перемещение нескольких задач сразу
   - Пакетное изменение статуса

4. **Умные подсказки**
   - Рекомендации колонок на основе истории
   - Предсказание следующей колонки по workflow

## Тестирование

### Ручное тестирование:
1. Открыть задачу через "📅 Сегодня"
2. Нажать "🕒 Отложить"
3. Выбрать целевую колонку
4. Проверить обновление в YouGile
5. Проверить кнопку "❌ Отмена"

### Автоматические тесты (планируется):
```python
async def test_postpone_task():
    task = await task_repo.get_by_id("test-id")
    result = await postpone_service.move_task_to_column(
        task.id, 
        "target-column-id"
    )
    assert result.columnId == "target-column-id"
```

## Безопасность

- Проверка прав доступа через YouGile API
- Валидация всех входных данных
- Защита от injection через callback data
- Rate limiting на уровне клиента YouGile (50 запросов/мин)

## Производительность

- Асинхронные вызовы API
- Кэширование списков колонок
- Параллельная загрузка данных задачи и колонок
- Минимизация количества запросов к API

## Зависимости

```
aiogram >= 3.x
pydantic >= 2.x
structlog
httpx (для YouGile client)
```

## Совместимость

- ✅ YouGile API v2
- ✅ Telegram Bot API 7.0+
- ✅ Python 3.10+
- ✅ Async/Await паттерны
