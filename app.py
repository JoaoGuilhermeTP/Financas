# Importações de bibliotecas e módulos necessários para o funcionamento do app
from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from datetime import datetime
import pytz
from models import *
from collections import defaultdict
from dateutil.relativedelta import relativedelta

# Instanciação e configuração da aplicação Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finances.db'  # Caminho do banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa rastreamento de modificações do SQLAlchemy
app.config["TEMPLATES_AUTO_RELOAD"] = True  # Atualiza templates automaticamente
app.config["SESSION_PERMANENT"] = False  # Sessão não permanente
app.config["SESSION_TYPE"] = "filesystem"  # Sessão salva em arquivos
Session(app)  # Inicializa o controle de sessão
# Inicializa o banco de dados com a aplicação
db.init_app(app)


# Rota da página inicial
@app.route('/')
def home():
    """
    Renderiza a página inicial do sistema.
    """
    return render_template('index.html')

# Rota de registro de novo usuário
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Permite o cadastro de um novo usuário. Valida dados, verifica duplicidade e salva no banco.
    """
    # Obtém dados do formulário de registro
    if request.method == 'POST':
        username, email, password, confirm_password = request.form['username'], request.form['email'], request.form['password'], request.form['confirm_password']

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
    return render_template('register.html')  # Renderiza o formulário de registro

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Realiza o login do usuário, validando credenciais e criando sessão.
    """
    session.clear()  # Limpa a sessão antes de iniciar o login
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']

        # Verifica se o usuário existe
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'], session['username'], session['email'] = user.id, user.username, user.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='E-mail ou senha inválidos.')
    return render_template('login.html')  # Página de login

# Rota do dashboard principal
@app.route('/dashboard')
def dashboard():
    """
    Exibe o painel principal do usuário, com visão geral das contas, projeções, gráficos e transações recentes.
    """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    # Busca todas as contas bancárias do usuário logado
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    # Soma o saldo total de todas as contas
    total_balance = sum([float(a.balance) for a in accounts]) if accounts else 0.0

    # Projeção de saldos para os próximos 12 meses
    # Obtém a data atual para servir de referência
    today = datetime.today()
    # Gera uma lista com o primeiro dia dos próximos 12 meses, começando do mês atual
    months = get_next_12_month_starts(today)
    # Calcula as projeções de saldo para cada conta em cada mês
    projections = calculate_account_projections(accounts, months)
    # Cria os rótulos dos meses no formato 'Mês/Ano' para exibição nos gráficos
    projection_labels = [m.strftime('%b/%Y') for m in months]
    # Monta a estrutura de dados para o gráfico de projeção, associando cada conta à sua lista de saldos projetados
    projection_data = [
        {
            'account_name': account.account_name,  # Nome da conta bancária
            'balances': projections[account.id]    # Lista de saldos projetados para os próximos 12 meses
        }
        for account in accounts
    ]

    # Busca as 5 transações mais recentes
    recent_transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.date.desc()).limit(5).all()

    # Gera dados para o gráfico de categorias do mês atual
    start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = (start_month + relativedelta(months=1))
    cat_agg = db.session.query(Category.name, db.func.sum(Transaction.amount)) \
        .join(Transaction, Transaction.category_id == Category.id) \
        .filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount < 0) \
        .group_by(Category.name).all()
    category_labels = [c[0] for c in cat_agg]
    category_values = [float(abs(c[1])) for c in cat_agg]

    # Calcula resumo mensal (receitas, despesas e saldo líquido)
    income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount > 0).scalar() or 0.0
    expenses = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.user_id == session['user_id'], Transaction.date >= start_month, Transaction.date < end_month, Transaction.amount < 0).scalar() or 0.0
    net = float(income) + float(expenses)

    # Busca as próximas transações agendadas (status 'Previsto')
    upcoming_transactions = Transaction.query.filter_by(user_id=session['user_id'], status='Previsto').filter(Transaction.date > today).order_by(Transaction.date).limit(5).all()

    # Dados para gráfico de distribuição entre contas
    account_labels = [a.account_name for a in accounts]
    account_distribution = [float(a.balance) for a in accounts]

    # Renderiza o dashboard com todos os dados calculados
    return render_template('dashboard.html', accounts=accounts, total_balance=total_balance,
        projection_labels=projection_labels, projection_data=projection_data,
        recent_transactions=recent_transactions,
        category_labels=category_labels, category_values=category_values,
        income=income, expenses=expenses, net=net,
        upcoming_transactions=upcoming_transactions,
        account_labels=account_labels, account_distribution=account_distribution)

# Rota de listagem de transações
@app.route('/transacoes')
def transacoes():
    """
    Exibe as transações do usuário, permitindo filtrar por mês.
    """
    if not session['user_id']:
        return redirect(url_for('login'))

    # Obtém data e hora atual no fuso de Brasília
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(brasilia_tz)

    # Lista de nomes dos meses em português
    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    # Verifica se o usuário selecionou um mês específico para filtrar
    selected_month = request.args.get('month')
    if selected_month:
        try:
            # Converte o mês selecionado para datetime
            start_date = datetime.strptime(selected_month, '%Y-%m')
            end_date = datetime(start_date.year, start_date.month + 1, 1) if start_date.month < 12 else datetime(start_date.year + 1, 1, 1)
        except ValueError:
            start_date = None
            end_date = None
    else:
        # Se não selecionado, usa o mês atual
        start_date = datetime(now.year, now.month, 1, tzinfo=brasilia_tz)
        end_date = datetime(now.year, now.month + 1, 1, tzinfo=brasilia_tz) if now.month < 12 else datetime(now.year + 1, 1, 1, tzinfo=brasilia_tz)

    # Nome do mês e ano para exibição
    month_name = month_names[start_date.month - 1]
    year = start_date.year
    
    # Busca as transações do usuário no período selecionado
    transactions = Transaction.query.filter(
        Transaction.user_id == session['user_id'],
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).order_by(Transaction.date.desc()).all()

    # Busca contas bancárias e categorias para exibição
    bank_accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.order_by(Category.name).all()

    # Renderiza a página de transações
    return render_template('transacoes/transacoes.html', transactions=transactions, bank_accounts=bank_accounts, categories=categories, month_name=month_name, year=year)

# Rota para exibir formulário de nova transação
@app.route('/transacoes/nova_transacao', methods=['GET'])
def nova_transacao():
    """
    Exibe o formulário para adicionar uma nova transação.
    """
    return render_template('transacoes/nova_transacao.html')

# Rota para adicionar uma nova transação a uma conta
@app.route('/transacoes/nova/conta', methods=['GET', 'POST'])
def nova_transacao_conta():
    """
    Processa o cadastro de uma nova transação vinculada a uma conta bancária.
    """
    user_id = session.get('user_id')
    contas = BankAccount.query.filter_by(user_id=user_id).all()  # Busca contas do usuário
    categories = Category.query.order_by(Category.name).all()    # Busca categorias
    if request.method == 'POST':
        descricao = request.form['descricao']  # Descrição da transação
        valor = request.form['valor']          # Valor da transação
        data = request.form['data']            # Data da transação
        conta_id = request.form['conta_id']    # Conta selecionada
        category_id = request.form['category_id']  # Categoria selecionada
        status = request.form['status']        # Status da transação
        tipo = request.form.get('tipo')  # Tipo da transação (receita ou despesa)
        # Validações de preenchimento
        if not conta_id:
            return render_template('transacoes/nova_transacao.html', contas=contas, categories=categories, error='Selecione uma conta.')
        if not category_id:
            return render_template('transacoes/nova_transacao.html', contas=contas, categories=categories, error='Selecione uma categoria.')
        bank_account = BankAccount.query.filter_by(id=conta_id, user_id=user_id).first()
        if not bank_account:
            return render_template('transacoes/nova_transacao.html', contas=contas, categories=categories, error='Conta não encontrada.')
        # Ajusta o valor para negativo se o tipo for 'despesa' e positivo se for 'receita'
        try:
            valor_float = float(valor)
        except Exception:
            valor_float = 0.0
        if tipo == 'despesa' and valor_float > 0:
            valor_float = -valor_float
        if tipo == 'receita' and valor_float < 0:
            valor_float = abs(valor_float)
        # Cria e salva a nova transação
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
        # Se a transação for confirmada, atualiza o saldo da conta
        if transaction.status == 'Confirmado':
            recalculate_account_balance(bank_account)
        return redirect(url_for('transacoes'))
    return render_template('transacoes/nova_transacao.html', contas=contas, categories=categories)




@app.route('/logout')
def logout():
    """
    Realiza o logout do usuário, limpando a sessão.
    """
    session.clear()
    return redirect(url_for('home'))  # Redireciona para a página inicial após logout




@app.route('/sobre')
def sobre():
    """
    Renderiza a página com informações sobre o sistema.
    """
    return render_template('sobre.html')  # Página "Sobre"




@app.route('/ajuda')
def ajuda():
    """
    Renderiza a página de ajuda e suporte.
    """
    return render_template('ajuda.html')  # Página "Ajuda"




@app.route('/contato', methods=['GET', 'POST'])
def contato():
    """
    Processa o envio de mensagens de contato pelo usuário.
    """
    if request.method == 'POST':
        # Lógica para enviar mensagem de contato (não implementada aqui)
        return render_template('contato.html', success='Mensagem enviada com sucesso!')
    return render_template('contato.html')  # Página "Contato"




@app.route('/contas', methods=['GET', 'POST'])
def configuracoes_contas():
    """
    Exibe e permite a configuração das contas bancárias do usuário.
    """
    if not session['user_id']:
        return redirect(url_for('login'))
    banks = Bank.query.all() 
    bank_accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    return render_template('configuracoes/contas/configurar_contas.html', banks=banks, bank_accounts=bank_accounts)



@app.route('/configuracoes/contas/adicionar', methods=['GET', 'POST'])
def adicionar_conta():
    """
    Adiciona uma nova conta bancária às configurações do usuário.
    """
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
    """
    Edita os dados de uma conta bancária existente.
    """
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
    """
    Remove uma conta bancária das configurações do usuário.
    """
    if not session['user_id']:
        return redirect(url_for('login'))
    
    # Busca a conta pelo ID
    account = BankAccount.query.filter_by(id=account_id, user_id=session['user_id']).first()
    if not account:
        return redirect(url_for('configuracoes_contas'))
    # Remove todas as transações associadas à conta antes de deletar a conta
    Transaction.query.filter_by(bank_account_id=account.id).delete()
    # Remove a conta do banco de dados
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('configuracoes_contas'))




@app.route('/transacoes/editar/<int:transaction_id>', methods=['GET', 'POST'])
def editar_transacao(transaction_id):
    """
    Edita os dados de uma transação existente.
    """
    if not session.get('user_id'):
        return redirect(url_for('login'))
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=session['user_id']).first_or_404()
    contas = BankAccount.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        if 'delete' in request.form:
            bank_account_id = transaction.bank_account_id
            db.session.delete(transaction)
            db.session.commit()
            # Atualiza o saldo da conta após deletar a transação
            if bank_account_id:
                bank_account = BankAccount.query.get(bank_account_id)
                recalculate_account_balance(bank_account)
            return redirect(url_for('transacoes'))
        # Atualiza os dados da transação
        transaction.description = request.form['descricao']
        transaction.date = datetime.strptime(request.form['data'], '%Y-%m-%d')
        transaction.category_id = request.form['category_id']
        transaction.status = request.form['status']
        transaction.bank_account_id = request.form['conta_id']
        tipo = request.form.get('tipo')
        valor = request.form['valor']
        try:
            valor_float = float(valor) # Converte o valor para float
        except ValueError:
            valor_float = 0.0
        if tipo == 'despesa' and valor_float > 0:
            valor_float = -valor_float  # Transforma em negativo se for despesa     
        if tipo == 'receita' and valor_float < 0:
            valor_float = abs(valor_float)  # Transforma em positivo se for receita
        transaction.amount = valor_float  # Atualiza o valor da transação   
        db.session.add(transaction)
        db.session.commit()
        bank_account = BankAccount.query.get(transaction.bank_account_id)
        if bank_account:
            recalculate_account_balance(bank_account)
            db.session.commit()
        return redirect(url_for('transacoes'))
    return render_template('transacoes/editar_transacao.html', transaction=transaction, contas=contas, categories=categories)




def recalculate_account_balance(account):
    """
    Recalcula o saldo de uma conta bancária, somando apenas transações com status 'Confirmado'.
    """
    confirmed_sum = sum(float(t.amount) for t in account.transactions if getattr(t, 'status', 'Confirmado') == 'Confirmado')
    account.balance = confirmed_sum
    db.session.commit()

def get_next_12_month_starts(start_date):
    """
    Retorna uma lista com o primeiro dia dos próximos 12 meses, começando do mês fornecido.
    :param start_date: datetime - Data inicial (normalmente o mês atual)
    :return: list[datetime] - Lista de datas
    """
    months = []
    for i in range(12):
        month = start_date + relativedelta(months=i)
        month_start = month.replace(day=1)
        months.append(month_start)
    return months

def calculate_account_projections(accounts, months):
    """
    Calcula os saldos projetados para cada conta nos meses fornecidos.
    :param accounts: lista de contas bancárias
    :param months: lista de datas (primeiro dia de cada mês)
    :return: defaultdict(list) com os saldos projetados por conta
    """
    projections = defaultdict(list)
    for account in accounts:
        # Obtém todas as transações da conta
        transacoes = account.transactions
        for month_start in months:
            # Define o final do mês atual
            month_end = month_start + relativedelta(months=1)
            # Soma os valores das transações realizadas até o final do mês
            saldo_ate_mes = 0.0
            for transacao in transacoes:
                if transacao.date < month_end:
                    saldo_ate_mes += float(transacao.amount)
            projections[account.id].append(saldo_ate_mes)
    return projections



if __name__ == '__main__':
    app.run(debug=True)