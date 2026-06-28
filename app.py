from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uuid, logging
from passlib.context import CryptContext
import sqlite3
from datetime import datetime, timedelta
import json
import asyncio
from contextlib import asynccontextmanager

# ---------------- SESSION STORAGE ----------------
active_sessions = {}

# ---------------- SQLITE JSON SUPPORT ----------------
def adapter(obj):
    return json.dumps(obj)

def converter(obj):
    return json.loads(obj)

sqlite3.register_adapter(dict, adapter)
sqlite3.register_converter("json", converter)

connections = sqlite3.connect(
    "expense_tracking_database",
    detect_types=sqlite3.PARSE_DECLTYPES,
    check_same_thread=False
)

cursor = connections.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    expenses JSON,
    expense_id INTEGER
)
""")

connections.commit()

# ---------------- SESSION CLEANER ----------------
async def clean_sessions():
    while True:
        await asyncio.sleep(3600)
        for token in list(active_sessions.keys()):
            if active_sessions[token]["expires_at"] < datetime.now():
                del active_sessions[token]

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(clean_sessions())
    yield
    task.cancel()

# ---------------- APP ----------------
app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {"status": "running"}

# ---------------- CORS FIXED ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- MODELS ----------------
class Login(BaseModel):
    user_name: str
    password: str

class Signup(BaseModel):
    username: str
    password: str

class UserExpense(BaseModel):
    amount: float
    category: str
    date: str
    description: str

# ---------------- AUTH ----------------
hasher = CryptContext(schemes=["bcrypt"])

# ---------------- SIGNUP ----------------
@app.post("/signup")
def signup(data: Signup):
    cursor.execute("SELECT username FROM users WHERE username = ?", (data.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hasher.hash(data.password)

    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        (data.username, hashed, {}, 1)
    )
    connections.commit()

    return {"message": "Account created"}

# ---------------- LOGIN ----------------
@app.post("/verify_login")
def login(data: Login):
    cursor.execute("SELECT password FROM users WHERE username = ?", (data.user_name,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    if not hasher.verify(data.password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = str(uuid.uuid4())

    active_sessions[token] = {
        "username": data.user_name,
        "expires_at": datetime.now() + timedelta(hours=24)
    }

    return {"token": token}

# ---------------- AUTH HELPER ----------------
def get_user(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid format")

    token = parts[1]

    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid token")

    session = active_sessions[token]

    if session["expires_at"] < datetime.now():
        del active_sessions[token]
        raise HTTPException(status_code=401, detail="Token expired")

    return session["username"]

# ---------------- ADD EXPENSE ----------------
@app.post("/expenses")
def add_expense(expense: UserExpense, authorization: Optional[str] = Header(None)):
    username = get_user(authorization)

    cursor.execute("SELECT expenses, expense_id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    expenses = row[0] or {"expenses": {}}
    next_id = row[1]

    if "expenses" not in expenses:
        expenses["expenses"] = {}

    expenses["expenses"][str(next_id)] = {
        "id": next_id,
        "amount": expense.amount,
        "category": expense.category.strip().title(),
        "date": expense.date,
        "description": expense.description
    }

    cursor.execute(
        "UPDATE users SET expenses = ?, expense_id = ? WHERE username = ?",
        (expenses, next_id + 1, username)
    )

    connections.commit()

    return {"message": "Expense added"}

# ---------------- GET EXPENSES ----------------
@app.get("/expenses")
def get_expenses(authorization: Optional[str] = Header(None)):
    username = get_user(authorization)

    cursor.execute("SELECT expenses FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    expenses = row[0] or {"expenses": {}}

    return {"expenses": list(expenses.get("expenses", {}).values())}

# ---------------- STATS ----------------
@app.get("/expenses/stats")
def stats(authorization: Optional[str] = Header(None)):
    username = get_user(authorization)

    cursor.execute("SELECT expenses FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    expenses = row[0] or {"expenses": {}}
    items = list(expenses.get("expenses", {}).values())

    if not items:
        return {"total_spent": 0, "average": 0, "category_count": 0}

    total = sum(x["amount"] for x in items)

    return {
        "total_spent": total,
        "average": total / len(items),
        "category_count": len(set(x["category"].lower() for x in items))
    }

# ---------------- DELETE ----------------
@app.delete("/expenses/{expense_id}")
def delete(expense_id: int, authorization: Optional[str] = Header(None)):
    username = get_user(authorization)

    cursor.execute("SELECT expenses FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    expenses = row[0] or {"expenses": {}}

    if str(expense_id) not in expenses.get("expenses", {}):
        raise HTTPException(status_code=404, detail="Expense not found")

    del expenses["expenses"][str(expense_id)]

    cursor.execute(
        "UPDATE users SET expenses = ? WHERE username = ?",
        (expenses, username)
    )

    connections.commit()

    return {"message": "Deleted successfully"}