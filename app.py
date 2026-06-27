
from fastapi import FastAPI , HTTPException , Header
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid, logging
from passlib.context import CryptContext
import sqlite3 
from datetime import datetime, timedelta
import json
import asyncio
from contextlib import asynccontextmanager

active_sessions = {}

def adapter(dict_obj):
    return json.dumps(dict_obj)

def converter(dict_obj2):
    return json.loads(dict_obj2)

sqlite3.register_adapter(dict,adapter)
sqlite3.register_converter("json",converter)

connections = sqlite3.connect('expense_tracking_database',detect_types=sqlite3.PARSE_DECLTYPES,check_same_thread=False)
cursor = connections.cursor()

create_table = """CREATE TABLE IF NOT EXISTS
users(username text PRIMARY KEY,password TEXT,expenses JSON,expense_id INTEGER)
"""

cursor.execute(create_table)

async def clean_sessions(session_dict):
    while True:
        await asyncio.sleep(3600)
        for token in list(session_dict.keys()):
            time_created = session_dict[token]["expires_at"]
            now = datetime.now()
            if time_created < now:
                del session_dict[token]

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(clean_sessions(active_sessions))
    yield

    task.cancel()

app = FastAPI(lifespan= lifespan)


sessions: dict = {}



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Login(BaseModel):
    user_name: str
    password:str

class UserExpense(BaseModel):
    amount: float
    category: str
    date: str
    description: str

class Signup(BaseModel):
    username: str
    password: str



hasher = CryptContext(schemes=["bcrypt"])







#----------------VERIFYING THE USER------------------

@app.post("/signup")
def adding(add: Signup):
    username = add.username
    user_pass = add.password
    cursor.execute("SELECT username FROM users WHERE username = ?",(username,))
    result = cursor.fetchone()
    if result:
        raise HTTPException(status_code=400, detail="Username already exists")
    else:
        hashed_pass = hasher.hash(user_pass)
        cursor.execute("INSERT INTO users (username,password,expenses,expense_id) VALUES (?,?,?,?)",(username,hashed_pass,{},1))
        connections.commit()

        return {"message": "Successfully created your account"}

@app.post("/verify_login")
def verify(login: Login):
    to_confirm = login.password
    username = login.user_name
    cursor.execute("SELECT username FROM users WHERE username = ?",(username,))
    result_ = cursor.fetchone()
    if not result_:
        raise HTTPException(status_code=404, detail="User not found")
    result = result_[0]

    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    cursor.execute("select password from users where username = ?",(username,))
    password_= cursor.fetchone()
    if not password_:
        raise HTTPException(status_code=404, detail="User not found")
    password = password_[0]

    verify = hasher.verify(to_confirm,password)
    
    if verify:
        token = str(uuid.uuid4())
        active_sessions[token] = {"username": login.user_name, "expires_at":datetime.now() + timedelta(hours=24)}
        return {"token":token,"message":"Sucessfully login"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
#-------------------------------------------------UNDER DEVELOPMENT


@app.post("/expenses")
async def add_expense(expense: UserExpense, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = token_parts[1]
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    session_data = active_sessions[token]
    if datetime.now() > session_data["expires_at"]:
        del active_sessions[token]  
        raise HTTPException(status_code=401, detail="Token has expired")
    
    username = session_data["username"]
    cursor.execute("select expenses from users where username = ?",(username,))
    expenses_ = cursor.fetchone()
    if not expenses_:
        raise HTTPException(status_code=404, detail="User not found")
    expenses = expenses_[0]

    cursor.execute("select expense_id from users where username = ?",(username,))
    current_id_ = cursor.fetchone()
    if not current_id_:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_id = current_id_[0]

    next_id = current_id + 1
    cursor.execute("update users set expense_id = ? where username = ?",(next_id,username))
    connections.commit()

    if expenses is not None:
        expense_to_work = expenses
    else:
        expense_to_work = {"expenses":{}}

    if "expenses" not in expense_to_work:
        expense_to_work["expenses"] = {}
        
    amount = expense.amount
    category = expense.category
    date = expense.date
    description = expense.description

    expense_to_work["expenses"][str(current_id)] = {
        "id": current_id,
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }

    cursor.execute("update users set expenses = ? where username = ?",(expense_to_work,username))
    connections.commit()

    return {"message":"Expense added successfully", "expense": expense_to_work["expenses"][str(current_id)]}
    

@app.get("/expenses")
async def return_expense(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = token_parts[1]
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    session_data = active_sessions[token]
    username = session_data["username"]
    cursor.execute("select expenses from users where username = ?",(username,))
    expenses_ =  cursor.fetchone()
    if not expenses_:
        raise HTTPException(status_code=404, detail="User not found")
    expenses = expenses_[0]

    inner_expenses = expenses.get("expenses", {})

    if not inner_expenses:
        return {"expenses":[]}
    expense_list = list(inner_expenses.values())
    return {"expenses":expense_list}

@app.get("/expenses/stats")
async def stats(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = token_parts[1]
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    session_data = active_sessions[token]
    username = session_data["username"]
    cursor.execute("select expenses from users where username = ?",(username,))
    expenses_ = cursor.fetchone()
    if not expenses_:
        raise HTTPException(status_code=404, detail="User not found")
    expenses = expenses_[0]

    inner_expenses = expenses.get("expenses", {})

    if not inner_expenses:
        return {"total_spent": 0, "average": 0, "category_count": 0}
    total_exp = sum(exp["amount"] for exp in inner_expenses.values())
    total_cat = len(inner_expenses)
    avg_exp = total_exp / total_cat
    
    return {"total_spent": total_exp, "average": avg_exp, "category_count": total_cat}

@app.delete("/expenses/{expense_id}")
async def delete_exp(expense_id: int, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = token_parts[1]
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    session_data = active_sessions[token]
    username = session_data["username"]

    cursor.execute("select expenses from users where username = ?",(username,))
    expenses_ = cursor.fetchone()
    if not expenses_:
        raise HTTPException(status_code=404, detail="User not found")
    expenses = expenses_[0]

    if str(expense_id) not in expenses.get("expenses",{}) :   
        raise HTTPException(status_code=404, detail="Expense not found")
    
    del expenses["expenses"][str(expense_id)]                 
    cursor.execute("UPDATE users SET expenses = ? WHERE username = ?", (expenses, username))  
    connections.commit()                                   
    return {"message":"expense deleted successfully"}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    

