import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "agenda.db"

def conectar():
    return sqlite3.connect(DATABASE)

def criar_tabelas():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            nickname TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('admin', 'professor', 'aluno')),
            ativo BOOLEAN DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ano INTEGER,
            dt_id INTEGER UNIQUE,
            FOREIGN KEY (dt_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS professor_disciplina (
            professor_id INTEGER NOT NULL,
            disciplina_id INTEGER NOT NULL,
            PRIMARY KEY (professor_id, disciplina_id),
            FOREIGN KEY (professor_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS turma_disciplina_professor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turma_id INTEGER NOT NULL,
            disciplina_id INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            UNIQUE(turma_id, disciplina_id, professor_id),
            FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE CASCADE,
            FOREIGN KEY (professor_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aluno_turma (
            aluno_id INTEGER NOT NULL,
            turma_id INTEGER NOT NULL,
            PRIMARY KEY (aluno_id, turma_id),
            FOREIGN KEY (aluno_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE
        )
    """)

    con.commit()

    cur.execute("SELECT COUNT(*) FROM users WHERE tipo = 'admin'")
    if cur.fetchone()[0] == 0:
        hash_pw = generate_password_hash("admin123!")
        cur.execute("INSERT INTO users (numero_processo, nickname, password_hash, tipo) VALUES (NULL, ?, ?, 'admin')",
                    ("admin1", hash_pw))
        con.commit()

    con.close()

def criar_conta_por_admin(numero_processo, nickname, password, tipo):
    if tipo not in ('professor', 'aluno'):
        return False, "Tipo inválido.", None
    if not numero_processo or not nickname or not password:
        return False, "Todos os campos são obrigatórios.", None

    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE numero_processo = ?", (numero_processo,))
    if cur.fetchone():
        con.close()
        return False, "Número de processo já registado.", None

    password_hash = generate_password_hash(password)
    try:
        cur.execute("INSERT INTO users (numero_processo, nickname, password_hash, tipo, ativo) VALUES (?, ?, ?, ?, 1)",
                    (numero_processo, nickname, password_hash, tipo))
        user_id = cur.lastrowid
        con.commit()
        con.close()
        return True, f"Conta de {tipo} criada.", user_id
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}", None

def listar_turmas():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT t.id, t.nome, t.ano, u.nickname
        FROM turmas t
        LEFT JOIN users u ON t.dt_id = u.id
        ORDER BY t.nome
    """)
    turmas = cur.fetchall()
    con.close()
    return turmas

def listar_professores():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, numero_processo, nickname FROM users WHERE tipo = 'professor' AND ativo = 1 ORDER BY nickname")
    profs = cur.fetchall()
    con.close()
    return profs

def listar_alunos():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, numero_processo, nickname FROM users WHERE tipo = 'aluno' AND ativo = 1 ORDER BY nickname")
    alunos = cur.fetchall()
    con.close()
    return alunos

def listar_disciplinas():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, nome FROM disciplinas ORDER BY nome")
    discs = cur.fetchall()
    con.close()
    return discs

def criar_turma(nome, ano=None):
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO turmas (nome, ano) VALUES (?, ?)", (nome, ano))
        con.commit()
        con.close()
        return True, "Turma criada."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Turma já existe."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def criar_disciplina(nome):
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO disciplinas (nome) VALUES (?)", (nome,))
        con.commit()
        con.close()
        return True, "Disciplina criada."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Disciplina já existe."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def designar_dt(turma_id, professor_id):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT tipo FROM users WHERE id = ?", (professor_id,))
    res = cur.fetchone()
    if not res or res[0] != 'professor':
        con.close()
        return False, "ID não é professor."
    try:
        cur.execute("UPDATE turmas SET dt_id = ? WHERE id = ?", (professor_id, turma_id))
        if cur.rowcount == 0:
            con.close()
            return False, "Turma não encontrada."
        con.commit()
        con.close()
        return True, "DT designado."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Professor já é DT de outra turma."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def associar_professor_disciplina(professor_id, disciplina_id):
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO professor_disciplina (professor_id, disciplina_id) VALUES (?, ?)",
                    (professor_id, disciplina_id))
        con.commit()
        con.close()
        return True, "Disciplina associada."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Associação já existe."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def alocar_professor_turma_disciplina(professor_id, turma_id, disciplina_id):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT 1 FROM professor_disciplina WHERE professor_id = ? AND disciplina_id = ?",
                (professor_id, disciplina_id))
    if not cur.fetchone():
        con.close()
        return False, "Professor não habilitado para esta disciplina."
    try:
        cur.execute("INSERT INTO turma_disciplina_professor (turma_id, disciplina_id, professor_id) VALUES (?, ?, ?)",
                    (turma_id, disciplina_id, professor_id))
        con.commit()
        con.close()
        return True, "Professor alocado."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Alocação já existe."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def matricular_aluno(aluno_id, turma_id):
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO aluno_turma (aluno_id, turma_id) VALUES (?, ?)", (aluno_id, turma_id))
        con.commit()
        con.close()
        return True, "Aluno matriculado."
    except sqlite3.IntegrityError:
        con.close()
        return False, "Aluno já está nesta turma."
    except Exception as e:
        con.close()
        return False, f"Erro: {str(e)}"

def obter_alunos_turma(turma_id):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT u.id, u.numero_processo, u.nickname
        FROM aluno_turma at
        JOIN users u ON at.aluno_id = u.id
        WHERE at.turma_id = ?
        ORDER BY u.nickname
    """, (turma_id,))
    alunos = cur.fetchall()
    con.close()
    return alunos

def obter_detalhes_turma(turma_id):
    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT t.id, t.nome, t.ano, t.dt_id, u.nickname
        FROM turmas t
        LEFT JOIN users u ON t.dt_id = u.id
        WHERE t.id = ?
    """, (turma_id,))
    turma_row = cur.fetchone()
    if not turma_row:
        con.close()
        return None

    turma_info = {
        'id': turma_row[0],
        'nome': turma_row[1],
        'ano': turma_row[2],
        'dt_id': turma_row[3],
        'dt_nome': turma_row[4]
    }

    cur.execute("""
        SELECT u.id, u.numero_processo, u.nickname
        FROM aluno_turma at
        JOIN users u ON at.aluno_id = u.id
        WHERE at.turma_id = ?
        ORDER BY u.nickname
    """, (turma_id,))
    alunos = cur.fetchall()

    cur.execute("""
        SELECT DISTINCT u.id, u.numero_processo, u.nickname
        FROM turma_disciplina_professor tdp
        JOIN users u ON tdp.professor_id = u.id
        WHERE tdp.turma_id = ?
        ORDER BY u.nickname
    """, (turma_id,))
    professores_rows = cur.fetchall()

    professores = []
    for prof in professores_rows:
        prof_id = prof[0]
        cur.execute("""
            SELECT d.id, d.nome
            FROM turma_disciplina_professor tdp
            JOIN disciplinas d ON tdp.disciplina_id = d.id
            WHERE tdp.turma_id = ? AND tdp.professor_id = ?
            ORDER BY d.nome
        """, (turma_id, prof_id))
        disciplinas = cur.fetchall()
        professores.append({
            'id': prof_id,
            'numero_processo': prof[1],
            'nickname': prof[2],
            'disciplinas': disciplinas,
            'is_dt': (prof_id == turma_info['dt_id'])
        })

    con.close()
    return {'turma': turma_info, 'alunos': alunos, 'professores': professores}

def listar_professores_completo():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT 
            u.id, 
            u.numero_processo, 
            u.nickname,
            t.nome,
            d.nome,
            CASE WHEN t.dt_id = u.id THEN 1 ELSE 0 END as is_dt
        FROM users u
        LEFT JOIN turma_disciplina_professor tdp ON u.id = tdp.professor_id
        LEFT JOIN turmas t ON tdp.turma_id = t.id
        LEFT JOIN disciplinas d ON tdp.disciplina_id = d.id
        WHERE u.tipo = 'professor' AND u.ativo = 1
        ORDER BY u.nickname, t.nome, d.nome
    """)
    resultado = cur.fetchall()
    con.close()
    return resultado

def listar_alunos_completo():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT 
            u.id, 
            u.numero_processo, 
            u.nickname,
            t.nome
        FROM users u
        LEFT JOIN aluno_turma at ON u.id = at.aluno_id
        LEFT JOIN turmas t ON at.turma_id = t.id
        WHERE u.tipo = 'aluno' AND u.ativo = 1
        ORDER BY u.nickname, t.nome
    """)
    resultado = cur.fetchall()
    con.close()
    return resultado