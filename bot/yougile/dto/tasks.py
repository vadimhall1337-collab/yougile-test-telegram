from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, date

class TaskDto(BaseModel):
    id: str
    title: str
    columnId: Optional[str] = None
    boardId: Optional[str] = None
    deleted: bool = False
    completed: bool = False
    archived: bool = False
    timestamp: Optional[int] = None 
    deadline: Optional[date] = None 
    
    parent_id: Optional[str] = None
    idTaskProject: Optional[str] = None
    description: Optional[str] = None      # Описание для детального просмотра
    subtasks: Optional[List[str]] = Field(default_factory=list)   # Массив ID подзадач

    @model_validator(mode='before')
    @classmethod
    def pre_process_yougile_data(cls, data: any) -> any:
        if isinstance(data, dict):
            # 1. Исправляем ошибку валидации булевых полей (null -> False)
            for field in ["deleted", "completed", "archived"]:
                if data.get(field) is None:
                    data[field] = False
            
            # 2. Исправляем ошибку валидации дедлайна (конвертируем объект/таймстамп в date)
            deadline_val = data.get("deadline")
            if isinstance(deadline_val, dict):
                ts = deadline_val.get("deadline")
                data["deadline"] = datetime.fromtimestamp(ts / 1000).date() if ts else None
            elif isinstance(deadline_val, (int, float)):
                data["deadline"] = datetime.fromtimestamp(deadline_val / 1000).date()
                
        return data

class CreateTaskDto(BaseModel):
    title: str
    columnId: str
    description: Optional[str] = None

class UpdateTaskDto(BaseModel):
    title: Optional[str] = None
    columnId: Optional[str] = None
    completed: Optional[bool] = None
    archived: Optional[bool] = None