from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Схема для входа
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схема для регистрации 
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(..., min_length=2, max_length=50)

# Схема ответа с токенами
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Схема для обновления токена
class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ---------- Задачи (GET /tasks) ----------

class TaskOut(BaseModel):
    task_id: int
    category_id: Optional[int] = None
    category_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_done: bool = False
    completed_at: Optional[datetime] = None


# ---------- События (GET /events) ----------

class EventOut(BaseModel):
    event_id: int
    title: str
    description: Optional[str] = None
    event_date: datetime


class EventsResponse(BaseModel):
    count: int            # количество событий (верхняя часть экрана)
    events: list[EventOut]
