expenses = {}
expense_id_counter = 1


def add_expense():
    global expense_id_counter

    amount = float(input("Enter amount: "))
    category = input("Enter category: ")
    date = input("Enter date (YYYY-MM-DD): ")
    description = input("Enter description: ")

    expenses[expense_id_counter] = {
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }

    print(f"\nExpense added with ID {expense_id_counter}\n")
    expense_id_counter += 1


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