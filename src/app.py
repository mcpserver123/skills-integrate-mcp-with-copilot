"""
High School Management System API

A simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import secrets
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)

security = HTTPBasic()

DATABASE_PATH = current_dir / "activities.db"

INITIAL_ACTIVITIES = [
    {
        "name": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    {
        "name": "Programming Class",
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    {
        "name": "Gym Class",
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    {
        "name": "Soccer Team",
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    {
        "name": "Basketball Team",
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    {
        "name": "Art Club",
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    {
        "name": "Drama Club",
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    {
        "name": "Math Club",
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    {
        "name": "Debate Team",
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
]

INITIAL_USERS = [
    {
        "username": "admin",
        "password": "adminpass",
        "role": "admin",
        "email": "admin@mergington.edu",
    },
    {
        "username": "michael",
        "password": "studentpass",
        "role": "student",
        "email": "michael@mergington.edu",
    },
    {
        "username": "emma",
        "password": "studentpass",
        "role": "student",
        "email": "emma@mergington.edu",
    },
    {
        "username": "john",
        "password": "studentpass",
        "role": "student",
        "email": "john@mergington.edu",
    },
]


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            schedule TEXT NOT NULL,
            max_participants INTEGER NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            UNIQUE(activity_id, email),
            FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        """
    )

    cursor.execute("SELECT COUNT(1) FROM activities")
    activity_count = cursor.fetchone()[0]

    if activity_count == 0:
        for activity in INITIAL_ACTIVITIES:
            cursor.execute(
                "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                (
                    activity["name"],
                    activity["description"],
                    activity["schedule"],
                    activity["max_participants"],
                ),
            )
            activity_id = cursor.lastrowid
            for participant_email in activity["participants"]:
                cursor.execute(
                    "INSERT INTO participants (activity_id, email) VALUES (?, ?)",
                    (activity_id, participant_email),
                )

    cursor.execute("SELECT COUNT(1) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        for user in INITIAL_USERS:
            cursor.execute(
                "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
                (user["username"], user["password"], user["role"], user["email"]),
            )

    conn.commit()
    conn.close()


class UserSignup(BaseModel):
    username: str
    password: str
    email: str


class ActivityCreate(BaseModel):
    name: str
    description: str
    schedule: str
    max_participants: int


class ActivityUpdate(BaseModel):
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: Optional[int] = None


def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password, role, email FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def create_user(username: str, password: str, role: str, email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, role, email) VALUES (?, ?, ?, ?)",
        (username, password, role, email),
    )
    conn.commit()
    conn.close()


def verify_password(plain_password: str, stored_password: str):
    return secrets.compare_digest(plain_password, stored_password)


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = get_user_by_username(credentials.username)
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {
        "username": user["username"],
        "role": user["role"],
        "email": user["email"],
    }


def require_admin(current_user: dict):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


def fetch_activity(activity_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, schedule, max_participants FROM activities WHERE name = ?",
        (activity_name,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_participants(activity_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email FROM participants WHERE activity_id = ? ORDER BY id",
        (activity_id,),
    )
    participants = [row["email"] for row in cursor.fetchall()]
    conn.close()
    return participants


def get_activities_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, schedule, max_participants FROM activities ORDER BY name"
    )
    activities_rows = cursor.fetchall()

    activities_data = {}
    for row in activities_rows:
        activity_id = row["id"]
        activities_data[row["name"]] = {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": get_participants(activity_id),
        }

    conn.close()
    return activities_data


@app.on_event("startup")
def startup_event():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return get_activities_data()


@app.post("/auth/signup")
def signup_user(signup: UserSignup):
    if get_user_by_username(signup.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    create_user(signup.username, signup.password, "student", signup.email)
    return {
        "message": "Student account created",
        "username": signup.username,
        "email": signup.email,
        "role": "student",
    }


@app.post("/auth/login")
def login_user(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "email": current_user["email"],
    }


@app.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@app.post("/activities")
def create_activity(activity: ActivityCreate, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    if fetch_activity(activity.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity already exists",
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
        (activity.name, activity.description, activity.schedule, activity.max_participants),
    )
    conn.commit()
    conn.close()
    return {"message": f"Created activity {activity.name}"}


@app.put("/activities/{activity_name}")
def update_activity(
    activity_name: str,
    activity_update: ActivityUpdate,
    current_user: dict = Depends(get_current_user),
):
    require_admin(current_user)
    activity = fetch_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    update_fields = []
    values = []

    if activity_update.description is not None:
        update_fields.append("description = ?")
        values.append(activity_update.description)
    if activity_update.schedule is not None:
        update_fields.append("schedule = ?")
        values.append(activity_update.schedule)
    if activity_update.max_participants is not None:
        update_fields.append("max_participants = ?")
        values.append(activity_update.max_participants)

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    values.append(activity_name)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE activities SET {', '.join(update_fields)} WHERE name = ?",
        tuple(values),
    )
    conn.commit()
    conn.close()
    return {"message": f"Updated activity {activity_name}"}


@app.delete("/activities/{activity_name}")
def delete_activity(activity_name: str, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    activity = fetch_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE name = ?", (activity_name,))
    conn.commit()
    conn.close()
    return {"message": f"Deleted activity {activity_name}"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == "student" and email != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only sign up for themselves",
        )

    activity = fetch_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    participants = get_participants(activity["id"])
    if email in participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student is already signed up")

    if len(participants) >= activity["max_participants"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activity is full")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO participants (activity_id, email) VALUES (?, ?)",
        (activity["id"], email),
    )
    conn.commit()
    conn.close()

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == "student" and email != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only unregister themselves",
        )

    activity = fetch_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM participants WHERE activity_id = ? AND email = ?",
        (activity["id"], email),
    )
    participant_row = cursor.fetchone()
    if not participant_row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not signed up for this activity",
        )

    cursor.execute("DELETE FROM participants WHERE id = ?", (participant_row["id"],))
    conn.commit()
    conn.close()

    return {"message": f"Unregistered {email} from {activity_name}"}
