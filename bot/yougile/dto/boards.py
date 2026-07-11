from pydantic import BaseModel

class CaseDto(BaseModel):
    id: str
    title: str