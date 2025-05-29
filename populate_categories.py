from models import db, Category
from app import app

categories = [
    # Incomes
    "Salário",
    "Rendimento de Investimentos",
    "Venda de Produto",
    "Reembolso",
    "Prêmio",
    "Aluguel Recebido",
    "Dividendos",
    "Bônus",
    "Comissão",
    "Restituição de Imposto",
    "Transferência Recebida",
    "Pensão Recebida",
    "Aposentadoria",
    "13º Salário",
    "Férias Recebidas",
    "Lucro",
    "Recebimento de Empréstimo",
    "Cashback",
    "Herança",
    "Outros Recebimentos",
    # Expenses
    "Alimentação",
    "Supermercado",
    "Transporte",
    "Combustível",
    "Moradia",
    "Aluguel Pago",
    "Condomínio",
    "Energia Elétrica",
    "Água e Saneamento",
    "Internet",
    "Telefone",
    "Saúde",
    "Medicamentos",
    "Educação",
    "Mensalidade Escolar",
    "Cursos",
    "Lazer",
    "Viagem",
    "Restaurante",
    "Compras",
    "Roupas",
    "Beleza",
    "Assinaturas",
    "Streaming",
    "Seguros",
    "Cartão de Crédito",
    "Impostos",
    "Taxas Bancárias",
    "Doações",
    "Presentes",
    "Animais de Estimação",
    "Manutenção de Veículo",
    "Outros Gastos",
    "Ajuste de Saldo",
]

with app.app_context():
    for name in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()
    print("Categorias populadas com sucesso!")
