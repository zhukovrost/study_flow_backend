from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import sqlite3

DB_FILE = "app.db"

app = FastAPI(title="Study Progress API")


class SessionCreate(BaseModel):
    user_id: int
    category: Optional[str] = "general"


class SessionEnd(BaseModel):
    session_id: int


class TaskCreate(BaseModel):
    user_id: int
    name: str


class TaskComplete(BaseModel):
    user_id: int
    task_id: int


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        category TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        completed INTEGER DEFAULT 0,
        completion_time TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()


init_db()

@app.post("/sessions/start")
def start_session(data: SessionCreate):
    conn = get_db_connection()
    c = conn.cursor()
    start_time = datetime.fromisoformat().strftime("%d.%m.%Y %H:%M:%S UTC")
    c.execute(
        "INSERT INTO sessions (user_id, start_time, category) VALUES (?, ?, ?)",
        (data.user_id, start_time, data.category)
    )
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return {"session_id": session_id, "start_time": start_time}


@app.post("/sessions/end")
def end_session(data: SessionEnd):
    conn = get_db_connection()
    c = conn.cursor()
    end_time = datetime.utcnow().isoformat()
    c.execute("UPDATE sessions SET end_time = ? WHERE id = ?", (end_time, data.session_id))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    conn.commit()
    conn.close()
    return {"session_id": data.session_id, "end_time": end_time}


@app.post("/tasks/add")
def add_task(data: TaskCreate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, name) VALUES (?, ?)", (data.user_id, data.name))
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return {"task_id": task_id, "name": data.name}


@app.post("/tasks/complete")
def complete_task(data: TaskComplete):
    conn = get_db_connection()
    c = conn.cursor()
    completion_time = datetime.utcnow().isoformat()
    c.execute(
        "UPDATE tasks SET completed = 1, completion_time = ? WHERE id = ? AND user_id = ?",
        (completion_time, data.task_id, data.user_id)
    )
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Задача не найдена")
    conn.commit()
    conn.close()
    return {"Номер задачи": data.task_id, "Закончено": completion_time}


@app.get("/stats/daily/{user_id}")
def get_daily_summary(user_id: int, day: Optional[date] = None):
    if day is None:
        day = datetime.utcnow().date()
    start = datetime.combine(day, datetime.min.time())
    end = datetime.combine(day, datetime.max.time())

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
    SELECT start_time, end_time FROM sessions
    WHERE user_id = ? AND start_time BETWEEN ? AND ?
    """, (user_id, start.isoformat(), end.isoformat()))

    total_seconds = 0
    for start_time, end_time in c.fetchall():
        if end_time:
            total_seconds += (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()

    c.execute("""
    SELECT COUNT(*) as count FROM tasks
    WHERE user_id = ? AND completed = 1 AND completion_time BETWEEN ? AND ?
    """, (user_id, start.isoformat(), end.isoformat()))
    tasks_done = c.fetchone()["count"]

    conn.close()

    return {
        "День": day.isoformat(),
        "Общее время учебы (в минутах)": round(total_seconds / 60, 2),
        "Сделанных задач": tasks_done
    }


@app.get("/stats/progress/{user_id}")
def get_progress(user_id: int):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT start_time, end_time FROM sessions WHERE user_id = ?", (user_id,))
    sessions = c.fetchall()

    total_seconds = 0
    completed_sessions = 0
    for start_time, end_time in sessions:
        if end_time:
            total_seconds += (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()
            completed_sessions += 1

    avg_session_length = total_seconds / completed_sessions / 60 if completed_sessions else 0

    c.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND completed = 1", (user_id,))
    tasks_done = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM tasks WHERE user_id = ?", (user_id,))
    total_tasks = c.fetchone()["count"]

    conn.close()

    return {
        "Всего сессий": completed_sessions,
        "Всего времени за учебой": round(total_seconds / 60, 2),
        "Среднее время сессии": round(avg_session_length, 2),
        "Выполнено задач": tasks_done,
        "Всего задач": total_tasks,
        "Процент успеваемости": (tasks_done / total_tasks * 100) if total_tasks else 0
    }
