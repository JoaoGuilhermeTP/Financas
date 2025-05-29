import random
from datetime import datetime, timedelta
from app import app
from models import db, Transaction, BankAccount, Category

# Settings
USER_ID = 1
NUM_TRANSACTIONS = 100

with app.app_context():
    # Get a bank account for the user
    bank_account = BankAccount.query.filter_by(user_id=USER_ID).first()
    if not bank_account:
        raise Exception(f"No bank account found for user_id={USER_ID}")

    # Get all categories
    categories = Category.query.all()
    if not categories:
        raise Exception("No categories found. Please add categories first.")

    for _ in range(NUM_TRANSACTIONS):
        description = 'teste'
        amount = random.randint(500, 50000) / 100  # Convert cents to decimal
        type_ = random.choice(["Income", "Expense"])
        date = datetime.now() - timedelta(days=random.randint(0, 365))
        user_id = USER_ID
        category = random.choice(categories)
        transaction = Transaction(
            description=description,
            amount=amount,
            type=type_,
            date=date,
            user_id=user_id,
            bank_account_id=bank_account.id,
            category_id=category.id
        )
        db.session.add(transaction)
    db.session.commit()
    print(f"{NUM_TRANSACTIONS} random transactions added for user_id={USER_ID}.")
