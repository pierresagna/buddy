-- =========================================================
-- Buddy: схема базы данных (PostgreSQL)
-- Создаёт все таблицы и связи по ER-диаграмме
-- =========================================================

-- ---------- Перечисляемые типы (ENUM) ----------
-- ВНИМАНИЕ: значения не указаны на диаграмме, это предложения.
-- Замените их на значения, принятые в вашей команде.
CREATE TYPE user_role      AS ENUM ('student', 'mentor', 'admin');
CREATE TYPE user_status    AS ENUM ('active', 'blocked', 'deleted');
CREATE TYPE pair_status    AS ENUM ('active', 'completed', 'cancelled');
CREATE TYPE message_type   AS ENUM ('text', 'image', 'file', 'system');
CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived');

-- ---------- Справочники ----------
CREATE TABLE faculties (
    id   serial PRIMARY KEY,
    name text
);

CREATE TABLE languages (
    id   serial PRIMARY KEY,
    name text UNIQUE
);

CREATE TABLE categories (
    category_id serial PRIMARY KEY,
    title       text,
    description text,
    sort_order  integer
);

-- ---------- Пользователи ----------
CREATE TABLE users (
    user_id           integer PRIMARY KEY,
    email             text UNIQUE,
    password_hash     text,
    full_name         text,
    avatar_url        text,
    role              user_role,
    status            user_status,
    is_email_verified boolean,
    created_at        timestamp without time zone,
    last_login_at     timestamp without time zone
);

CREATE TABLE student_profiles (
    user_id    integer PRIMARY KEY REFERENCES users (user_id),
    country    text,
    faculty_id integer REFERENCES faculties (id),
    study_year integer
);

CREATE TABLE mentor_profiles (
    user_id    integer PRIMARY KEY REFERENCES users (user_id),
    country    text,
    faculty_id integer REFERENCES faculties (id),
    study_year integer
);

CREATE TABLE user_languages (
    user_id     integer REFERENCES users (user_id),
    language_id integer REFERENCES languages (id),
    PRIMARY KEY (user_id, language_id)
);

-- ---------- Пары, чаты, сообщения ----------
CREATE TABLE mentor_pairs (
    pair_id    serial PRIMARY KEY,
    student_id integer REFERENCES users (user_id),
    mentor_id  integer REFERENCES users (user_id),
    status     pair_status,
    created_at timestamp without time zone,
    ended_at   timestamp without time zone,
    created_by integer REFERENCES users (user_id)
);

CREATE TABLE chats (
    chat_id         serial PRIMARY KEY,
    pair_id         integer REFERENCES mentor_pairs (pair_id),
    created_at      timestamp without time zone,
    is_active       boolean,
    last_message_at timestamp without time zone
);

CREATE TABLE messages (
    message_id      integer PRIMARY KEY,
    chat_id         integer REFERENCES chats (chat_id),
    sender_id       integer REFERENCES users (user_id),
    message_content text,
    type            message_type,
    is_edited       boolean,
    created_at      timestamp without time zone,
    edited_at       timestamp without time zone,
    deleted_at      timestamp without time zone
);

CREATE TABLE message_reads (
    message_id integer REFERENCES messages (message_id),
    user_id    integer REFERENCES users (user_id),
    read_at    timestamp without time zone,
    PRIMARY KEY (message_id, user_id)
);

-- ---------- База знаний ----------
CREATE TABLE articles (
    article_id      serial PRIMARY KEY,
    category_id     integer REFERENCES categories (category_id),
    title           text,
    article_content text,
    slug            text UNIQUE,
    status          article_status,
    is_pinned       boolean,
    updated_at      timestamp without time zone
);

CREATE TABLE favorite_articles (
    user_id    integer REFERENCES users (user_id),
    article_id integer REFERENCES articles (article_id),
    created_at timestamp without time zone,
    PRIMARY KEY (user_id, article_id)
);

-- ---------- Логи ----------
CREATE TABLE logs (
    log_id      serial PRIMARY KEY,
    user_id     integer REFERENCES users (user_id),
    action_type text,
    entity_type text,
    entity_id   integer,
    created_at  timestamp without time zone
);

-- ---------- Задачи адаптации (главный экран: GET /tasks) ----------
-- Чек-лист шагов для иностранного студента: регистрация, страховка и т.д.
CREATE TABLE tasks (
    task_id     serial PRIMARY KEY,
    category_id integer REFERENCES categories (category_id),
    title       text NOT NULL,
    description text,
    sort_order  integer
);

-- Выполнение задач конкретным пользователем
CREATE TABLE user_tasks (
    user_id      integer REFERENCES users (user_id) ON DELETE CASCADE,
    task_id      integer REFERENCES tasks (task_id) ON DELETE CASCADE,
    is_done      boolean NOT NULL DEFAULT false,
    completed_at timestamp without time zone,
    PRIMARY KEY (user_id, task_id)
);
