from models import db, Bank
from app import app

main_banks = [
    "Banco do Brasil",
    "Bradesco",
    "Itaú Unibanco",
    "Santander",
    "Caixa Econômica Federal",
    "Nubank",
    "Banco Inter",
    "BTG Pactual",
    "C6 Bank",
    "Banco Pan"
]

with app.app_context():
    for bank_name in main_banks:
        if not Bank.query.filter_by(name=bank_name).first():
            bank = Bank(name=bank_name)
            db.session.add(bank)
    db.session.commit()
    print("Main Brazilian banks added to the database.")
