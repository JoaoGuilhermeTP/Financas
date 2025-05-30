from models import db, Bank
from app import app

# Lista dos bancos mais populares do Brasil (ordenada alfabeticamente e sem duplicatas)
banks = sorted(set([
    "ABC Brasil",
    "Agibank",
    "Alfa",
    "Amazônia",
    "Banese",
    "Banestes",
    "Banpará",
    "Banrisul",
    "BMG",
    "BNDES",
    "Bonsucesso",
    "Bradesco",
    "BRB",
    "BS2",
    "BTG Pactual",
    "BV (Votorantim)",
    "C6 Bank",
    "Caixa Econômica Federal",
    "Cetelem",
    "Cooperativo do Brasil (Sicoob)",
    "Cooperativo Sicredi",
    "Crefisa",
    "Cresol",
    "Daycoval",
    "Digio",
    "Fibra",
    "Inter",
    "Itaú BBA",
    "Itaú Unibanco",
    "Mercantil do Brasil",
    "Modal",
    "Neon",
    "Next",
    "Nubank",
    "Original",
    "PagBank (PagSeguro)",
    "Pan",
    "Paraná",
    "PicPay",
    "Pine",
    "Rendimento",
    "Safra",
    "Santander Brasil",
    "Sofisa",
    "Topázio",
    "Toyota do Brasil",
    "Votorantim (BV)",
    "XP Investimentos",
]))

with app.app_context():
    for name in banks:
        if not Bank.query.filter_by(name=name).first():
            db.session.add(Bank(name=name))
    db.session.add(Bank(name="Outros"))  # Adiciona a opção "Outros" para bancos não listados
    db.session.commit()
    print("Bancos populares do Brasil adicionados com sucesso!")
