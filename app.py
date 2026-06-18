#--------------------------------------------------UNDER DEVELOPMENT-------------------------------------------------
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid, logging
from passlib.context import CryptContext

app = FastAPI()
#DUMMY CODE TO BE REFINED
password = [] # DUMMY... SECURE DATABASE TO BE ADDED 
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

class Expense(BaseModel):
    amount: float
    category: str
    date: str
    description: str

class Signup(BaseModel):
    username: str
    password: str



hasher = CryptContext(schemes=["bcrypt"])

@app.post("/signup")
def adding(add: Signup):
    username = add.username
    user_pass = add.password
    hashed_pass = hasher.hash(user_pass)
    password.append(hashed_pass)

@app.post("/login")
def hash_password(login: Login):
    user_pass = Login.password
    hashed_pass = hasher.hash(user_pass)
    return {"sucessfully hashed: ":hashed_pass}

@app.post("/verify_login")
def verify(login: Login):
    to_confirm = login.password
    verify = hasher.verify(to_confirm,password[-1])
    if verify:
        token = str(uuid.uuid4())
        active_sessions[token] = login.user_name
        return {"token":token,"message":"Sucessfully login"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
#-------------------------------------------------UNDER DEVELOPMENT

"""
@app.post("/add_expense")
async def add_expense(expense: Expense):
    expenses = {}
    session_id = str(uuid.uuid4())
    expense_id_counter = 1

    amount = expense.amount
    category = expense.category
    date = expense.date
    description = expense.description

    expenses[expense_id_counter] = {
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }

    print(f"\nExpense added with ID {expense_id_counter}\n")
    expense_id_counter += 1
    sessions[session_id] = {"expense_id":expense_id_counter,"expenses":expenses}


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