from pydantic import BaseModel, Field
from typing import Optional, Dict, List
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
    
    subtasks: Optional[List[str]] = Field(default_factory=list)
    parent_id: Optional[str] = None
    idTaskProject: Optional[str] = None
    description: Optional[str] = None      # Описание для детального просмотра
    subtasks: Optional[List[str]] = None   # Массив ID подзадач

class CreateTaskDto(BaseModel):
    title: str
    columnId: str
    description: Optional[str] = None

class UpdateTaskDto(BaseModel):
    title: Optional[str] = None
    columnId: Optional[str] = None
    completed: Optional[bool] = None
    archived: Optional[bool] = None