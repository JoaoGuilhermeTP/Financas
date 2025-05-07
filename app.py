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
    return render_template('transacoes.html')  # Página de transações




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




if __name__ == '__main__':
    app.run(debug=True)