from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class TaskDto(BaseModel):
    id: str
    title: str
    columnId: str
    boardId: Optional[str] = None
    deleted: bool = False
    completed: bool = False
    archived: bool = False
    timestamp: int
    
    # Для дерева подзадач
    subtasks: Optional[List[str]] = Field(default_factory=list)
    parent_id: Optional[str] = None

class CreateTaskDto(BaseModel):
    title: str
    columnId: str
    description: Optional[str] = None

class UpdateTaskDto(BaseModel):
    title: Optional[str] = None
    columnId: Optional[str] = None
    completed: Optional[bool] = None
    archived: Optional[bool] = None