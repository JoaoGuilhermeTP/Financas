from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from datetime import datetime
import pytz
from models import *
from collections import defaultdict
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db.init_app(app)




@app.route('/')
def home():
    return render_template('index.html')  # Página inicial




@app.route('/register', methods=['GET', 'POST'])
def register():

    # Obtem dados do formulário de registro
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Verifica se as senhas coincidem
        if password != confirm_password:
            return render_template('register.html', error='As senhas não coincidem.')

        # Verifica se o e-mail ou nome de usuário já existe
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template('register.html', error='Usuário ou e-mail já cadastrado.')
        
        # Cria a senha hasheada
        hasshed_password = generate_password_hash(password)

        # Cria um novo usuário e adiciona ao banco de dados
        new_user = User(username=username, email=email, password=hasshed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')  




@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()  # Limpa a sessão antes de iniciar o login
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Verifica se o usuário existe
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='E-mail ou senha inválidos.')
    return render_template('login.html')  # Página de login




@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    total_balance = sum([float(a.balance) for a in accounts]) if accounts else 0.0

    # Projected balances for the next 12 months (including 'Previsto')
    today = datetime.today()
    months = [(today + relativedelta(months=i)).replace(day=1) for i in range(12)]
    projections = defaultdict(list)
    for account in accounts:
        txs = [t for t in account.transactions]
        for i, month_start in enumerate(months):
            month_end = (month_start + relativedelta(months=1))
            tx_sum = sum(float(t.amount) for t in txs if t.date < month_end)
            projections[account.id].append(tx_sum)
    projection_labels = [m.strftime('%b/%Y') for m in months]
    projection_data = [
        {
            'account_name': account.account_name,
            'balances': projections[account.id]
        }
        for account in accounts
    ]

    # Recent Transactions (last 5)
    recent_transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.date.desc()).limit(5).all()

    # Top Categories Pie Chart (current month)
    start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = (start_month + relativedelta(months=1))
    cat_agg = db.session.query(Category.name, db.func.sum(Transaction.amount)) \
        .join(Transaction, Transaction.category_id == Category.id) \
        .filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount < 0) \
        .group_by(Category.name).all()
    category_labels = [c[0] for c in cat_agg]
    category_values = [float(abs(c[1])) for c in cat_agg]

    # Monthly Summary Cards (current month)
    income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount > 0).scalar() or 0.0
    expenses = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount < 0).scalar() or 0.0
    net = float(income) + float(expenses)

    # Upcoming Scheduled Transactions (Previsto, future date)
    upcoming_transactions = Transaction.query.filter_by(user_id=session['user_id'], status='Previsto').filter(Transaction.date > today).order_by(Transaction.date).limit(5).all()

    # Account Distribution Pie Chart
    account_labels = [a.account_name for a in accounts]
    account_distribution = [float(a.balance) for a in accounts]

    return render_template('dashboard.html', accounts=accounts, total_balance=total_balance,
        projection_labels=projection_labels, projection_data=projection_data,
        recent_transactions=recent_transactions,
        category_labels=category_labels, category_values=category_values,
        income=income, expenses=expenses, net=net,
        upcoming_transactions=upcoming_transactions,
        account_labels=account_labels, account_distribution=account_distribution)




@app.route('/transacoes')
def transacoes():
    if not session['user_id']:
        return redirect(url_for('login'))

    # Get the current date and time in Brasilia timezone
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(brasilia_tz)

    # Map month numbers to Portuguese names
    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    # Get the selected month from the request arguments
    selected_month = request.args.get('month')
    if selected_month:
        try:
            # Parse the selected month into a datetime object
            start_date = datetime.strptime(selected_month, '%Y-%m')
            end_date = datetime(start_date.year, start_date.month + 1, 1) if start_date.month < 12 else datetime(start_date.year + 1, 1, 1)
        except ValueError:
            start_date = None
            end_date = None
    else:
        # Default to the current month in Brasilia timezone
        start_date = datetime(now.year, now.month, 1, tzinfo=brasilia_tz)
        end_date = datetime(now.year, now.month + 1, 1, tzinfo=brasilia_tz) if now.month < 12 else datetime(now.year + 1, 1, 1, tzinfo=brasilia_tz)

    month_name = month_names[start_date.month - 1]
    year = start_date.year
    
    transactions = Transaction.query.filter(
        Transaction.user_id == session['user_id'],
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).order_by(Transaction.date.desc()).all()

    bank_accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template('transacoes/transacoes.html', transactions=transactions, bank_accounts=bank_accounts, categories=categories, month_name=month_name, year=year)
    
   



@app.route('/transacoes/nova_transacao', methods=['GET'])
def nova_transacao():
    return render_template('transacoes/nova_transacao.html')



@app.route('/transacoes/nova/conta', methods=['GET', 'POST'])
def nova_transacao_conta():
    user_id = session.get('user_id')
    contas = BankAccount.query.filter_by(user_id=user_id).all()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = request.form['valor']
        data = request.form['data']
        conta_id = request.form['conta_id']
        category_id = request.form['category_id']
        status = request.form['status']
        if not conta_id:
            return render_template('transacoes/nova_transacao_conta.html', contas=contas, categories=categories, error='Selecione uma conta.')
        if not category_id:
            return render_template('transacoes/nova_transacao_conta.html', contas=contas, categories=categories, error='Selecione uma categoria.')
        bank_account = BankAccount.query.filter_by(id=conta_id, user_id=user_id).first()
        if not bank_account:
            return render_template('transacoes/nova_transacao_conta.html', contas=contas, categories=categories, error='Conta não encontrada.')
        valor_float = float(valor)
        transaction = Transaction(
            description=descricao,
            amount=valor_float,
            date=datetime.strptime(data, '%Y-%m-%d'),
            user_id=user_id,
            bank_account_id=bank_account.id,
            category_id=category_id,
            status=status
        )
        db.session.add(transaction)
        db.session.commit()
        if transaction.status == 'Confirmado':
            recalculate_account_balance(bank_account)
        return redirect(url_for('transacoes'))
    return render_template('transacoes/nova_transacao_conta.html', contas=contas, categories=categories)

@app.route('/transacoes/nova/cartao', methods=['GET', 'POST'])
def nova_transacao_cartao():
    user_id = session.get('user_id')
    cartoes = CreditCard.query.filter_by(user_id=user_id).all()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = request.form['valor']
        data = request.form['data']
        cartao_id = request.form['cartao_id']
        category_id = request.form['category_id']
        if not cartao_id:
            return render_template('transacoes/nova_transacao_cartao.html', cartoes=cartoes, categories=categories, error='Selecione um cartão.')
        if not category_id:
            return render_template('transacoes/nova_transacao_cartao.html', cartoes=cartoes, categories=categories, error='Selecione uma categoria.')
        credit_card = CreditCard.query.filter_by(id=cartao_id, user_id=user_id).first()
        if not credit_card:
            return render_template('transacoes/nova_transacao_cartao.html', cartoes=cartoes, categories=categories, error='Cartão não encontrado.')
        transaction = Transaction(
            description=descricao,
            amount=valor,  # valor já está em Reais, não dividir por 100
            date=datetime.strptime(data, '%Y-%m-%d'),
            user_id=user_id,
            credit_card_id=credit_card.id,
            category_id=category_id
        )
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('transacoes'))
    return render_template('transacoes/nova_transacao_cartao.html', cartoes=cartoes, categories=categories)



@app.route('/relatorios')
def relatorios():
    if not session['user_id']:
        return redirect(url_for('login'))
    return render_template('relatorios.html')  # Página de relatórios




@app.route('/configuracoes')
def configuracoes():
    if not session['user_id']:
        return redirect(url_for('login'))
    banks = Bank.query.all() 
    return render_template('configuracoes/configuracoes.html', banks=banks)  # Página de configurações




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))  # Redireciona para a página inicial após logout




@app.route('/sobre')
def sobre():
    return render_template('sobre.html')  # Página "Sobre"




@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')  # Página "Ajuda"




@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        # Lógica para enviar mensagem de contato (não implementada aqui)
        return render_template('contato.html', success='Mensagem enviada com sucesso!')
    return render_template('contato.html')  # Página "Contato"




@app.route('/configuracoes/contas', methods=['GET', 'POST'])
def configuracoes_contas():
    if not session['user_id']:
        return redirect(url_for('login'))
    banks = Bank.query.all() 
    bank_accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    return render_template('configuracoes/contas/configurar_contas.html', banks=banks, bank_accounts=bank_accounts)



@app.route('/configuracoes/contas/adicionar', methods=['GET', 'POST'])
def adicionar_conta():
    if not session['user_id']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        account_name = request.form['account_name']
        bank_id = request.form['bank_id']
        balance = request.form['balance_cents']

        # Cria uma nova conta e adiciona ao banco de dados
        new_account = BankAccount(account_name=account_name, bank_id=bank_id, balance=balance, user_id=session['user_id'])
        db.session.add(new_account)
        db.session.commit()

        # Busca a categoria "Ajuste de Saldo" no banco de dados
        ajuste_categoria = Category.query.filter_by(name='Ajuste de Saldo').first()
        categoria_id = ajuste_categoria.id if ajuste_categoria else None

        # Adiciona uma transação de saldo inicial
        if categoria_id:
            initial_transaction = Transaction(
                description='Saldo Inicial',
                amount=balance,
                date=datetime.now(),
                user_id=session['user_id'],
                bank_account_id=new_account.id,
                category_id=categoria_id,
                status='Confirmado'
            )
            db.session.add(initial_transaction)
            db.session.commit()
    return redirect(url_for('configuracoes_contas'))




@app.route('/configuracoes/contas/editar/<int:account_id>', methods=['GET', 'POST'])
def editar_conta(account_id):
    if not session['user_id']:
        return redirect(url_for('login'))
    
    # Busca a conta pelo ID
    account = BankAccount.query.filter_by(id=account_id, user_id=session['user_id']).first()
    if not account:
        return redirect(url_for('configuracoes_contas'))  # Redireciona se a conta não existir ou não pertencer ao usuário
    
    if request.method == 'POST':
        # Atualiza os dados da conta (nome e banco)
        account.account_name = request.form['account_name']
        account.bank_id = request.form['bank_id']
        # Calcula o saldo atual (soma das transações)
        current_sum = sum([float(t.amount) for t in account.transactions]) if account.transactions else 0.0
        # Novo saldo informado pelo usuário
        new_balance_str = request.form['balance']
        print(f"Novo saldo informado: {new_balance_str}")
        try:
            new_balance = float(str(new_balance_str))
        except Exception:
            new_balance = 0.0
        # Diferença necessária para ajustar o saldo
        diff = new_balance - current_sum
        if abs(diff) > 0.005:
            ajuste_categoria = Category.query.filter_by(name='Ajuste de Saldo').first()
            categoria_id = ajuste_categoria.id if ajuste_categoria else None
            if categoria_id:
                ajuste = Transaction(
                    description='Ajuste de Saldo',
                    amount=diff,
                    date=datetime.now(),
                    user_id=session['user_id'],
                    bank_account_id=account.id,
                    category_id=categoria_id,
                    status='Confirmado'
                )
                db.session.add(ajuste)
                db.session.commit()
        # Atualiza o saldo da conta para a soma das transações
        account.balance = sum([float(t.amount) for t in account.transactions]) if account.transactions else 0.0
        db.session.commit()
        return redirect(url_for('configuracoes_contas'))
    
    # Renderiza o formulário de edição com os dados da conta
    banks = Bank.query.all()
    return render_template('configuracoes/contas/editar_conta.html', account=account, banks=banks)




@app.route('/configuracoes/contas/excluir/<int:account_id>', methods=['GET', 'POST'])
def excluir_conta(account_id):
    if not session['user_id']:
        return redirect(url_for('login'))
    
    # Busca a conta pelo ID
    account = BankAccount.query.filter_by(id=account_id, user_id=session['user_id']).first()
    if not account:
        return redirect(url_for('configuracoes_contas'))
    # Remove a conta do banco de dados
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('configuracoes_contas'))




@app.route('/configuracoes/cartoes', methods=['GET', 'POST'])
def configuracoes_cartoes():
    if not session['user_id']:
        return redirect(url_for('login'))
    banks = Bank.query.all() 
    credit_cards = CreditCard.query.filter_by(user_id=session['user_id']).all()
    return render_template('configuracoes/cartoes/configurar_cartoes.html', banks=banks, credit_cards=credit_cards)




@app.route('/configuracoes/cartoes/adicionar', methods=['GET', 'POST'])
def adicionar_cartao():
    if not session['user_id']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        bank_id = request.form['bank_id']
        balance = request.form['balance']
        limit = request.form['limit']
        closing_date = request.form['closing_date']
        due_date = request.form['due_date']

        new_credit_card = CreditCard(
            name=name,
            bank_id=bank_id,
            balance=balance,
            limit=limit,
            closing_date=closing_date,
            due_date=due_date,
            user_id=session['user_id']
        )
        db.session.add(new_credit_card)
        db.session.commit()
    return redirect(url_for('configuracoes_cartoes'))




@app.route('/configuracoes/cartoes/editar/<int:credit_card_id>', methods=['GET', 'POST'])
def editar_cartao(credit_card_id):
    if not session['user_id']:
        return redirect(url_for('login'))
    # Busca o cartão pelo ID e usuário
    credit_card = CreditCard.query.filter_by(id=credit_card_id, user_id=session['user_id']).first()
    if not credit_card:
        return redirect(url_for('configuracoes_cartoes'))
    if request.method == 'POST':
        credit_card.name = request.form['credit_card_name']
        credit_card.bank_id = request.form['bank_id']
        credit_card.balance = request.form['balance_cents']
        credit_card.limit = request.form['limit']
        db.session.commit()
        return redirect(url_for('configuracoes_cartoes'))
    banks = Bank.query.all()
    return render_template('configuracoes/cartoes/editar_cartao.html', credit_card=credit_card, banks=banks)




@app.route('/configuracoes/cartoes/excluir/<int:credit_card_id>', methods=['GET', 'POST'])
def excluir_cartao(credit_card_id):
    if not session['user_id']:
        return redirect(url_for('login'))
    credit_card = CreditCard.query.filter_by(id=credit_card_id, user_id=session['user_id']).first()
    if not credit_card:
        return redirect(url_for('configuracoes_cartoes'))
    db.session.delete(credit_card)
    db.session.commit()
    return redirect(url_for('configuracoes_cartoes'))




@app.route('/configuracoes/categorias', methods=['GET', 'POST'])
def configuracoes_categorias():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    categories = Category.query.order_by(Category.name).all()
    return render_template('configuracoes/categorias/configurar_categorias.html', categories=categories)

@app.route('/configuracoes/categorias/adicionar', methods=['POST'])
def adicionar_categoria():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    name = request.form['category_name']
    if name and not Category.query.filter_by(name=name).first():
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
    return redirect(url_for('configuracoes_categorias'))

@app.route('/configuracoes/categorias/editar/<int:category_id>', methods=['GET', 'POST'])
def editar_categoria(category_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['category_name']
        db.session.commit()
        return redirect(url_for('configuracoes_categorias'))
    return render_template('configuracoes/categorias/editar_categoria.html', category=category)

@app.route('/configuracoes/categorias/excluir/<int:category_id>', methods=['POST'])
def excluir_categoria(category_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('configuracoes_categorias'))


@app.route('/transacoes/editar/<int:transaction_id>', methods=['GET', 'POST'])
def editar_transacao(transaction_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=session['user_id']).first_or_404()
    contas = BankAccount.query.filter_by(user_id=session['user_id']).all()
    cartoes = CreditCard.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        if 'delete' in request.form:
            bank_account_id = transaction.bank_account_id
            db.session.delete(transaction)
            db.session.commit()
            # Atualiza o saldo da conta após deletar a transação
            if bank_account_id:
                bank_account = BankAccount.query.get(bank_account_id)
                if bank_account:
                    bank_account.balance = sum([float(t.amount) for t in bank_account.transactions]) if bank_account.transactions else 0.0
                    db.session.commit()
            return redirect(url_for('transacoes'))
        # Update transaction
        old_status = transaction.status
        transaction.description = request.form['descricao']
        transaction.amount = request.form['valor']
        transaction.date = datetime.strptime(request.form['data'], '%Y-%m-%d')
        transaction.category_id = request.form['category_id']
        new_status = request.form.get('status', 'Confirmado')
        transaction.status = new_status
        conta_id = request.form.get('conta_id')
        cartao_id = request.form.get('cartao_id')
        transaction.bank_account_id = conta_id if conta_id else None
        transaction.credit_card_id = cartao_id if cartao_id else None
        db.session.commit()
        # Só recalcula o saldo se o status mudou para Confirmado
        if old_status != 'Confirmado' and new_status == 'Confirmado' and transaction.bank_account_id:
            bank_account = BankAccount.query.get(transaction.bank_account_id)
            if bank_account:
                bank_account.balance = sum([float(t.amount) for t in bank_account.transactions]) if bank_account.transactions else 0.0
                db.session.commit()
        return redirect(url_for('transacoes'))
    return render_template('transacoes/editar_transacao.html', transaction=transaction, contas=contas, cartoes=cartoes, categories=categories)

def recalculate_account_balance(account):
    """
    Recalculate the balance of a bank account, summing only transactions with status 'Confirmado'.
    """
    confirmed_sum = sum(float(t.amount) for t in account.transactions if getattr(t, 'status', 'Confirmado') == 'Confirmado')
    account.balance = confirmed_sum
    db.session.commit()



if __name__ == '__main__':
    app.run(debug=True)