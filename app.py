#--------------------------------------------------UNDER DEVELOPMENT-------------------------------------------------
from fastapi import FastAPI , HTTPException , Header
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid, logging
from passlib.context import CryptContext
import sqlite3 
from datetime import datetime, timedelta

#connections = sqlite3.connect('expense_tracking_database')

app = FastAPI()
#DUMMY CODE TO BE REFINED
users_db = {} # DUMMY... SECURE DATABASE TO BE ADDED... stores users with their passwords
sessions: dict = {}
active_sessions = {}

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
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pass = hasher.hash(user_pass)
    users_db[username] = {"password": hashed_pass, "expenses":{},"expense_id":1 }
    return {"message": "Successfully created your account"}

@app.post("/verify_login")
def verify(login: Login):
    to_confirm = login.password
    username = login.user_name

    if username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    verify = hasher.verify(to_confirm,users_db[username]["password"])
    
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
    user_data = users_db[username]
    current_id = user_data["expense_id"]
    user_data["expense_id"] += 1


    amount = expense.amount
    category = expense.category
    date = expense.date
    description = expense.description

    user_data["expenses"][current_id] = {
        "id": current_id,
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }
    return {"message":"Expense added successfully", "expense": user_data["expenses"][current_id]}
    

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
    user_data = users_db[username]
    expenses = user_data["expenses"]
    if not expenses:
        return []
    expense_list = list(expenses.values())
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
    user_data = users_db[username]
    expenses = user_data["expenses"]
    if not expenses:
        return {"total_spent": 0, "average": 0, "category_count": 0}
    total_exp = sum(exp["amount"] for exp in expenses.values())
    total_cat = len(expenses)
    avg_exp = total_exp / total_cat
    
    return {"total_spent": total_exp, "average": avg_exp, "category_count": total_cat}

        




"""
def view_all_expenses():
    if not expenses:
        print("\nNo expenses found.\n")
        return

    print("\n===== ALL EXPENSES =====")

    for expense_id, expense in expenses.items():
        print(f"\nID: {expense_id}")
        print(f"Amount: {expense['amount']}")
        print(f"Category: {expense['category']}")
        print(f"Date: {expense['date']}")
        print(f"Description: {expense['description']}")    


def edit_expense():
    if not expenses:
        print("\nNo expenses available.\n")
        return

    expense_id = int(input("Enter Expense ID to edit: "))

    if expense_id not in expenses:
        print("Expense not found.")
        return

    expense = expenses[expense_id]

    print("\nLeave blank to keep current value.\n")

    amount = input(f"Amount ({expense['amount']}): ")
    category = input(f"Category ({expense['category']}): ")
    date = input(f"Date ({expense['date']}): ")
    description = input(f"Description ({expense['description']}): ")

    if amount:
        expense["amount"] = float(amount)

    if category:
        expense["category"] = category

    if date:
        expense["date"] = date

    if description:
        expense["description"] = description

    print("\nExpense updated successfully.\n")


def delete_expense():
    if not expenses:
        print("\nNo expenses available.\n")
        return

    expense_id = int(input("Enter Expense ID to delete: "))

    if expense_id not in expenses:
        print("Expense not found.")
        return

    confirm = input("Are you sure? (Y/N): ").upper()

    if confirm == "Y":
        del expenses[expense_id]
        print("Expense deleted successfully.")
    else:
        print("Deletion cancelled.")


def view_stats():
    if not expenses:
        print("\nNo expenses available.\n")
        return

    total_spent = 0
    category_totals = {}

    for expense in expenses.values():
        amount = expense["amount"]
        category = expense["category"]

        total_spent += amount

        if category not in category_totals:
            category_totals[category] = 0

        category_totals[category] += amount

    print("\n===== STATISTICS =====")
    print(f"Total Expenses: {len(expenses)}")
    print(f"Total Amount Spent: {total_spent}")

    print("\nCategory Breakdown:")

    for category, amount in category_totals.items():
        print(f"{category}: {amount}")


def main_menu():
    while True:
        print("\n===== EXPENSE TRACKER =====")
        print("1. Add Expense")
        print("2. Edit Expense")
        print("3. Delete Expense")
        print("4. View All Expenses")
        print("5. Statistics")
        print("6. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            add_expense()

        elif choice == "2":
            edit_expense()

        elif choice == "3":
            delete_expense()

        elif choice == "4":
            view_all_expenses()

        elif choice == "5":
            view_stats()

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Try again.")


main_menu()
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    

