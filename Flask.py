from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import check_password_hash
from DB import *

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta-aqui'

criar_tabelas()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        numero_processo = request.form.get('numero_processo', '').strip()
        password = request.form.get('password', '')

        if not numero_processo or not password:
            flash('Preencha todos os campos.', 'danger')
            return render_template('login.html')

        con = conectar()
        cur = con.cursor()
        if numero_processo.lower() == 'admin':
            cur.execute("SELECT * FROM users WHERE nickname = ? AND tipo = 'admin'", (numero_processo,))
        else:
            cur.execute("SELECT * FROM users WHERE numero_processo = ?", (numero_processo,))
        user = cur.fetchone()
        con.close()

        if user and check_password_hash(user[3], password):
            session['user'] = {
                'id': user[0],
                'numero_processo': user[1],
                'nickname': user[2],
                'tipo': user[4]
            }
            flash(f'Bem-vindo, {user[2]}!', 'success')
            return redirect('/dashboard')
        else:
            flash('Credenciais inválidas.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão terminada.', 'info')
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    tipo = session['user']['tipo']
    if tipo == 'admin':
        return redirect('/admin')
    elif tipo == 'professor':
        return redirect('/professor')
    elif tipo == 'aluno':
        return redirect('/aluno')
    return redirect('/logout')

# -------------------- ADMIN --------------------
@app.route('/admin')
def admin_dashboard():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    turmas = listar_turmas()
    professores = listar_professores()
    alunos = listar_alunos()
    disciplinas = listar_disciplinas()
    return render_template('admin_dashboard.html',
                           turmas=turmas,
                           professores=professores,
                           alunos=alunos,
                           disciplinas=disciplinas)

@app.route('/admin/criar_conta', methods=['POST'])
def admin_criar_conta():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    numero = request.form['numero_processo']
    nickname = request.form['nickname']
    password = request.form['password']
    tipo = request.form['tipo']

    sucesso, msg, _ = criar_conta_por_admin(numero, nickname, password, tipo)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/criar_turma', methods=['POST'])
def admin_criar_turma():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    nome = request.form['nome']
    ano = request.form.get('ano', type=int)
    sucesso, msg = criar_turma(nome, ano)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/criar_disciplina', methods=['POST'])
def admin_criar_disciplina():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    nome = request.form['nome']
    sucesso, msg = criar_disciplina(nome)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/designar_dt', methods=['POST'])
def admin_designar_dt():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    turma_id = request.form['turma_id']
    professor_id = request.form['professor_id']
    sucesso, msg = designar_dt(turma_id, professor_id)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/associar_professor_disciplina', methods=['POST'])
def admin_associar_professor_disciplina():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    professor_id = request.form['professor_id']
    disciplina_id = request.form['disciplina_id']
    sucesso, msg = associar_professor_disciplina(professor_id, disciplina_id)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/alocar_professor', methods=['POST'])
def admin_alocar_professor():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    professor_id = request.form['professor_id']
    turma_id = request.form['turma_id']
    disciplina_id = request.form['disciplina_id']
    sucesso, msg = alocar_professor_turma_disciplina(professor_id, turma_id, disciplina_id)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

@app.route('/admin/matricular_aluno', methods=['POST'])
def admin_matricular_aluno():
    if session.get('user', {}).get('tipo') != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')

    aluno_id = request.form['aluno_id']
    turma_id = request.form['turma_id']
    sucesso, msg = matricular_aluno(aluno_id, turma_id)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect('/admin')

# -------------------- TURMAS (PÚBLICO) --------------------
@app.route('/turmas')
def ver_turmas():
    turmas = listar_turmas()
    return render_template('turmas.html', lista_turmas=turmas)

@app.route('/turma/<int:turma_id>')
def detalhes_turma(turma_id):
    dados = obter_detalhes_turma(turma_id)
    if not dados:
        flash('Turma não encontrada.', 'danger')
        return redirect('/turmas')
    return render_template('detalhes_turma.html',
                           turma=dados['turma'],
                           alunos=dados['alunos'],
                           professores=dados['professores'])

# -------------------- PROFESSORES (PÚBLICO) --------------------
@app.route('/professores')
def ver_professores():
    professores = listar_professores_completo()
    return render_template('professores.html', professores=professores)

# -------------------- ALUNOS (PÚBLICO) --------------------
@app.route('/alunos')
def ver_alunos():
    alunos = listar_alunos_completo()
    return render_template('alunos_lista.html', alunos=alunos)

# -------------------- PLACEHOLDERS --------------------
@app.route('/professor')
def professor_dashboard():
    if session.get('user', {}).get('tipo') != 'professor':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')
    return "<h1>Dashboard do Professor</h1><p>Em construção.</p><a href='/logout'>Sair</a>"

@app.route('/aluno')
def aluno_dashboard():
    if session.get('user', {}).get('tipo') != 'aluno':
        flash('Acesso negado.', 'danger')
        return redirect('/dashboard')
    return "<h1>Dashboard do Aluno</h1><p>Em construção.</p><a href='/logout'>Sair</a>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')