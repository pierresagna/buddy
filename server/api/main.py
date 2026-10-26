import os

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from jose import jwt, JWTError

from models.models import (
    EventsResponse,
    TaskOut,
    Token,
    TokenRefreshRequest,
    UserLogin,
)
from tools.auth import get_current_user_id
from tools.password import verify_password
from tools.tokens import (
    create_access_token,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
)

app = FastAPI(title="Buddy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER", "buddy_user"),
    password=os.getenv("POSTGRES_PASSWORD", "change_me"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "buddy"),
)

engine = create_engine(database_url, pool_pre_ping=True)


@app.get("/")
def read_root():
    return {"service": "Buddy API", "status": "running"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"api": "ok", "database": "connected"}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={"api": "ok", "database": "unavailable"},
        )


@app.post("/login", response_model=Token)
def login(user_data: UserLogin):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT user_id, email, password_hash "
                    "FROM users WHERE email = :email"
                ),
                {"email": user_data.email},
            ).fetchone()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Ошибка подключения к базе данных",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    user_id, email, hashed_password = result

    if not verify_password(user_data.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    return {
        "access_token": create_access_token(user_id=user_id),
        "refresh_token": create_refresh_token(user_id=user_id),
        "token_type": "bearer",
    }


@app.post("/refresh", response_model=Token)
def refresh_tokens(data: TokenRefreshRequest):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный refresh токен",
    )

    try:
        payload = jwt.decode(
            data.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "refresh":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return {
        "access_token": create_access_token(user_id=int(user_id)),
        "refresh_token": create_refresh_token(user_id=int(user_id)),
        "token_type": "bearer",
    }


def db_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Ошибка подключения к базе данных",
    )


# =========================================================
# Главный экран: GET /tasks
# =========================================================

TASKS_SELECT = (
    "SELECT t.task_id, t.category_id, c.title AS category_title, t.title, "
    "t.description, t.sort_order, "
    "COALESCE(ut.is_done, false) AS is_done, ut.completed_at "
    "FROM tasks t "
    "LEFT JOIN categories c ON c.category_id = t.category_id "
    "LEFT JOIN user_tasks ut ON ut.task_id = t.task_id AND ut.user_id = :uid "
)


@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(
    category_id: int | None = Query(None, description="Фильтр по категории"),
    user_id: int = Depends(get_current_user_id),
):
    """Чек-лист адаптации текущего пользователя (с отметкой, что уже выполнено)."""
    sql = TASKS_SELECT
    params: dict = {"uid": user_id}
    if category_id is not None:
        sql += "WHERE t.category_id = :cid "
        params["cid"] = category_id
    sql += "ORDER BY t.sort_order NULLS LAST, t.task_id"

    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
    except SQLAlchemyError:
        raise db_unavailable()

    return [dict(r) for r in rows]


# =========================================================
# Календарь событий: GET /events
# =========================================================

@app.get("/events", response_model=EventsResponse)
def get_events(
    date_from: datetime | None = Query(
        None, description="Начало периода (по умолчанию — сейчас). Пример: 2026-11-01"
    ),
    date_to: datetime | None = Query(
        None, description="Конец периода, не включительно. Пример: 2026-12-01"
    ),
    user_id: int = Depends(get_current_user_id),
):
    """Количество событий + список событий (название, дата, описание), по дате."""
    sql = "SELECT event_id, title, description, event_date FROM events WHERE event_date >= :date_from "
    params: dict = {"date_from": date_from or datetime.now()}
    if date_to is not None:
        sql += "AND event_date < :date_to "
        params["date_to"] = date_to
    sql += "ORDER BY event_date, event_id"

    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
    except SQLAlchemyError:
        raise db_unavailable()

    events = [dict(r) for r in rows]
    return {"count": len(events), "events": events}
