# Financas

Financas é uma aplicação web de controle financeiro pessoal desenvolvida com Flask. Permite aos usuários registrar transações, gerenciar contas bancárias, categorizar despesas e visualizar dados financeiros em um painel intuitivo.

## Funcionalidades

- Autenticação de usuários (cadastro, login, logout)
- Dashboard com visão geral financeira e gráficos
- Adição, edição e exclusão de transações
- Gerenciamento de contas bancárias e categorias
- Transações agendadas e confirmadas
- Interface responsiva com CSS customizado
- Dados armazenados em banco SQLite

## Tecnologias Utilizadas

- Python 3.12
- Flask
- Flask-Login (sessão de usuários)
- Flask-WTF (formulários e proteção CSRF)
- Flask-SQLAlchemy (ORM)
- Flask-Session (sessão no servidor)
- SQLite

## Primeiros Passos

### Pré-requisitos

- Python 3.12+
- pip

### Instalação

1. Clone o repositório ou baixe os arquivos do projeto.
2. (Recomendado) Crie e ative um ambiente virtual:
   ```
   python -m venv env
   .\env\Scripts\activate  # No Windows
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Inicialize o banco de dados com dados básicos:
   ```
   python populate_banks.py
   python populate_categories.py
   ```

### Executando a Aplicação

Inicie o servidor Flask:
```
flask --debug run
```
Acesse em [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Estrutura do Projeto

- `app.py` - Aplicação Flask principal e rotas
- `models.py` - Modelos do banco de dados (veja abaixo)
- `extensions.py` - Configuração das extensões Flask
- `templates/` - Templates HTML
- `static/` - Arquivos estáticos e CSS
- `seeds/` - Scripts para popular dados iniciais
- `finances.db` - Banco de dados SQLite

## Modelos do Banco de Dados

Os principais modelos estão definidos em `models.py` usando SQLAlchemy:

### User (Usuário)
- `id`: Chave primária
- `username`, `email`, `password`: Credenciais do usuário
- Relacionamentos: `bank_accounts`, `credit_cards`, `transactions`

### Bank (Banco)
- `id`, `name`: Informações do banco
- Relacionamentos: `bank_accounts`, `credit_cards`

### BankAccount (Conta Bancária)
- `id`, `account_name`, `balance`, `created_at`
- Chaves estrangeiras: `user_id`, `bank_id`
- Relacionamento: `transactions`

### CreditCard (Cartão de Crédito)
- `id`, `name`, `limit`, `balance`, `created_at`, `closing_date`, `due_date`
- Chaves estrangeiras: `user_id`, `bank_id`
- Relacionamento: `transactions`

### Transaction (Transação)
- `id`, `description`, `amount`, `date`, `created_at`, `status`
- Chaves estrangeiras: `user_id`, `bank_account_id`, `credit_card_id`, `category_id`
- Pertence a: Usuário, Conta Bancária ou Cartão de Crédito, Categoria

### Category (Categoria)
- `id`, `name`: Nome da categoria
- Relacionamento: `transactions`

## Exemplo de Esquema do Banco de Dados

```
User (id, username, email, password)
Bank (id, name)
BankAccount (id, account_name, balance, user_id, bank_id, created_at)
CreditCard (id, name, limit, balance, user_id, bank_id, created_at, closing_date, due_date)
Transaction (id, description, amount, date, user_id, bank_account_id, credit_card_id, category_id, created_at, status)
Category (id, name)
```

## Principais Classes e Suas Funções

- **User**: Representa o usuário da aplicação. Responsável pela autenticação e vinculação com contas e transações.
- **Bank**: Representa uma instituição financeira. Utilizado para agrupar contas e cartões.
- **BankAccount**: Conta bancária do usuário. Controla saldo e transações.
- **CreditCard**: Cartão de crédito do usuário. Controla limite, saldo e transações relacionadas.
- **Transaction**: Movimento financeiro (receita ou despesa). Vinculado a contas, cartões e categorias.
- **Category**: Classifica as transações (ex: Alimentação, Salário, Aluguel).

## Personalização

- Edite `static/styles.css` para customizar o visual.
- Modifique os templates em `templates/` para alterar a interface.

## Licença

Este projeto é para fins educacionais.
