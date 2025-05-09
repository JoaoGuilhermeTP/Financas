from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from models import *

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
    if not session['user_id']:
        return redirect(url_for('login'))
    return render_template('dashboard.html')  # Página do dashboard




@app.route('/transacoes')
def transacoes():
    if not session['user_id']:
        return redirect(url_for('login'))
    description_filter = request.args.get('description')
    amount_filter = request.args.get('amount')
    date_filter = request.args.get('date')
    type_filter = request.args.get('type')
    bank_account_filter = request.args.get('bank_account')
    category_filter = request.args.get('category')
    transactions = Transaction.query.filter_by(user_id=session['user_id'])
    if description_filter:
        transactions = transactions.filter(Transaction.description.contains(description_filter))
    if amount_filter:
        transactions = transactions.filter(Transaction.amount == amount_filter)
    if date_filter:
        from datetime import datetime
        try:
            date = datetime.strptime(date_filter, '%Y-%m-%d')
            transactions = transactions.filter(Transaction.date == date)
        except ValueError:
            pass
    if type_filter:
        transactions = transactions.filter(Transaction.type == type_filter)
    if bank_account_filter:
        transactions = transactions.filter(Transaction.bank_account_id == bank_account_filter)
    if category_filter:
        transactions = transactions.filter(Transaction.category_id == category_filter)
    transactions = transactions.all()
    bank_accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('transacoes.html', transactions=transactions, bank_accounts=bank_accounts, categories=categories)  # Página de transações




@app.route('/transacoes/adicionar', methods=['POST'])
def adicionar_transacao():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    description = request.form['description']
    amount = int(request.form['amount'])
    type_ = request.form['type']
    date_str = request.form['date']
    bank_account_id = request.form.get('bank_account_id')
    category_id = request.form.get('category_id')

    # Only allow transactions for bank accounts on this page
    if not bank_account_id:
        return redirect(url_for('transacoes'))

    from datetime import datetime
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except Exception:
        date = datetime.utcnow()

    new_transaction = Transaction(
        description=description,
        amount=amount,
        type=type_,
        date=date,
        user_id=session['user_id'],
        bank_account_id=bank_account_id,
        category_id=category_id if category_id else None
    )
    db.session.add(new_transaction)
    db.session.commit()
    return redirect(url_for('transacoes'))




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
    return render_template('configuracoes.html', banks=banks)  # Página de configurações




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
    return render_template('configurar_contas.html', banks=banks, bank_accounts=bank_accounts)



@app.route('/configuracoes/contas/adicionar', methods=['GET', 'POST'])
def adicionar_conta():
    if not session['user_id']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        account_number = request.form['account_number']
        bank_id = request.form['bank_id']
        balance = request.form['balance_cents']

        # Cria uma nova conta e adiciona ao banco de dados
        new_account = BankAccount(account_number=account_number, bank_id=bank_id, balance_cents=balance, user_id=session['user_id'])
        db.session.add(new_account)
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
        # Atualiza os dados da conta
        account.account_number = request.form['account_number']
        account.bank_id = request.form['bank_id']
        account.balance_cents = request.form['balance_cents']
        db.session.commit()
        return redirect(url_for('configuracoes_contas'))
    
    # Renderiza o formulário de edição com os dados da conta
    banks = Bank.query.all()
    return render_template('editar_conta.html', account=account, banks=banks)




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
    return render_template('configurar_cartoes.html', banks=banks, credit_cards=credit_cards)




@app.route('/configuracoes/cartoes/adicionar', methods=['GET', 'POST'])
def adicionar_cartao():
    if not session['user_id']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        credit_card_name = request.form['credit_card_name']
        bank_id = request.form['bank_id']
        balance = request.form['balance_cents']
        limit = request.form['limit']

        # Cria uma nova conta e adiciona ao banco de dados
        new_credit_card = CreditCard(name=credit_card_name, bank_id=bank_id, balance=balance, limit=limit, user_id=session['user_id'])
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
    return render_template('editar_cartao.html', credit_card=credit_card, banks=banks)




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
    return render_template('configurar_categorias.html', categories=categories)

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
    return render_template('editar_categoria.html', category=category)

@app.route('/configuracoes/categorias/excluir/<int:category_id>', methods=['POST'])
def excluir_categoria(category_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('configuracoes_categorias'))


if __name__ == '__main__':
    app.run(debug=True)