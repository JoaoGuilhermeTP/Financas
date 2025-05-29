from models import db, Bank
from app import app

# Lista dos bancos mais populares do Brasil
banks = [
    "Banco do Brasil",
    "Caixa Econômica Federal",
    "Bradesco",
    "Itaú Unibanco",
    "Santander",
    "Banco Safra",
    "Banco Inter",
    "Banco Original",
    "Nubank",
    "BTG Pactual",
    "Banco Pan",
    "Banco C6",
    "Banco BMG",
    "Banco Votorantim (BV)",
    "Banco Daycoval",
    "Banco Mercantil do Brasil"
]

with app.app_context():
    for name in banks:
        if not Bank.query.filter_by(name=name).first():
            db.session.add(Bank(name=name))
    db.session.commit()
    print("Bancos populares do Brasil adicionados com sucesso!")
