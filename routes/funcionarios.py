import sqlite3

from flask import Blueprint, flash, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import conectar

funcionarios_bp = Blueprint("funcionarios", __name__)


def criar_tabela_funcionarios():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            cargo TEXT
        )
    """)

    existe = conexao.execute(
        "SELECT 1 FROM funcionarios WHERE email = ?", ("admin@sistema.com",)
    ).fetchone()
    if not existe:
        conexao.execute(
            """INSERT INTO funcionarios (nome, email, senha, cargo, ativo, perfil)
               VALUES (?, ?, ?, ?, 1, 'admin')""",
            ("Administrador", "admin@sistema.com",
             generate_password_hash("admin123"), "Administrador"),
        )

    conexao.commit()
    conexao.close()


@funcionarios_bp.route("/funcionarios/cadastrar", methods=["GET", "POST"])
def cadastrar_funcionario():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        cargo = request.form["cargo"]
        perfil = request.form.get("perfil", "funcionario")

        conexao = conectar()

        total = conexao.execute("SELECT COUNT(*) FROM funcionarios").fetchone()[0]
        if total == 0:
            perfil = "admin"
        elif perfil not in ("admin", "tecnico", "atendente", "funcionario"):
            perfil = "funcionario"

        try:
            conexao.execute("""
                INSERT INTO funcionarios (nome, email, senha, cargo, perfil)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, email, senha, cargo, perfil))
            conexao.commit()
        except sqlite3.IntegrityError:
            conexao.close()
            return render_template(
                "funcionario_cadastro.html",
                erro="Nao foi possivel cadastrar. Verifique se o email ja esta em uso."
            )

        conexao.close()

        return redirect("/login")

    return render_template("funcionario_cadastro.html")


@funcionarios_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conexao = conectar()
        funcionario = conexao.execute("""
            SELECT id, nome, email, senha, cargo, ativo, perfil
            FROM funcionarios
            WHERE email = ?
        """, (email,)).fetchone()
        conexao.close()

        if funcionario and check_password_hash(funcionario["senha"], senha):
            if not funcionario["ativo"]:
                return render_template(
                    "login.html",
                    erro="Esta conta está desativada. Procure um administrador."
                )

            session["funcionario_id"] = funcionario["id"]
            session["funcionario_nome"] = funcionario["nome"]
            session["funcionario_cargo"] = funcionario["cargo"]
            session["funcionario_perfil"] = funcionario["perfil"]

            return redirect("/")

        return render_template(
            "login.html",
            erro="Email ou senha invalidos. Tente novamente."
        )

    return render_template("login.html")


@funcionarios_bp.route("/configuracoes")
def configuracoes():
    conexao = conectar()
    funcionario = conexao.execute("""
        SELECT id, nome, email, cargo
        FROM funcionarios
        WHERE id = ?
    """, (session.get("funcionario_id"),)).fetchone()

    total_funcionarios = conexao.execute(
        "SELECT COUNT(*) AS total FROM funcionarios"
    ).fetchone()["total"]
    conexao.close()

    return render_template(
        "configuracoes.html",
        funcionario=funcionario,
        total_funcionarios=total_funcionarios,
    )


@funcionarios_bp.route("/funcionarios")
def listar_funcionarios():
    conexao = conectar()
    funcionarios = conexao.execute("""
        SELECT id, nome, email, cargo, ativo, perfil
        FROM funcionarios
        ORDER BY nome
    """).fetchall()
    conexao.close()

    return render_template("funcionarios_lista.html", funcionarios=funcionarios)


@funcionarios_bp.route("/funcionarios/editar/<int:id>")
def pagina_editar_funcionario(id):
    conexao = conectar()
    funcionario = conexao.execute(
        "SELECT id, nome, email, cargo, perfil FROM funcionarios WHERE id = ?", (id,)
    ).fetchone()
    conexao.close()

    if funcionario is None:
        flash("Funcionário não encontrado.", "erro")
        return redirect("/funcionarios")

    return render_template("funcionario_editar.html", funcionario=funcionario)


@funcionarios_bp.route("/funcionarios/atualizar/<int:id>", methods=["POST"])
def atualizar_funcionario(id):
    nome = request.form["nome"]
    email = request.form["email"]
    cargo = request.form["cargo"]
    perfil = request.form.get("perfil", "funcionario")
    if perfil not in ("admin", "tecnico", "atendente", "funcionario"):
        perfil = "funcionario"

    conexao = conectar()
    try:
        conexao.execute(
            "UPDATE funcionarios SET nome = ?, email = ?, cargo = ?, perfil = ? WHERE id = ?",
            (nome, email, cargo, perfil, id),
        )
        conexao.commit()
        flash("Funcionário atualizado com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash("Não foi possível atualizar: este e-mail já está em uso.", "erro")
    finally:
        conexao.close()

    return redirect("/funcionarios")


@funcionarios_bp.route("/funcionarios/<int:id>/status", methods=["POST"])
def alternar_status_funcionario(id):
    if id == session.get("funcionario_id"):
        flash("Você não pode desativar a própria conta em uso.", "erro")
        return redirect("/funcionarios")

    conexao = conectar()
    atual = conexao.execute(
        "SELECT ativo FROM funcionarios WHERE id = ?", (id,)
    ).fetchone()

    if atual is None:
        conexao.close()
        flash("Funcionário não encontrado.", "erro")
        return redirect("/funcionarios")

    novo = 0 if atual["ativo"] else 1
    conexao.execute("UPDATE funcionarios SET ativo = ? WHERE id = ?", (novo, id))
    conexao.commit()
    conexao.close()

    flash("Funcionário " + ("ativado." if novo else "desativado."), "sucesso")
    return redirect("/funcionarios")


@funcionarios_bp.route("/funcionarios/<int:id>/redefinir-senha", methods=["POST"])
def redefinir_senha(id):
    nova_senha = request.form.get("senha", "").strip()

    if len(nova_senha) < 4:
        flash("A nova senha deve ter pelo menos 4 caracteres.", "erro")
        return redirect(f"/funcionarios/editar/{id}")

    conexao = conectar()
    conexao.execute(
        "UPDATE funcionarios SET senha = ? WHERE id = ?",
        (generate_password_hash(nova_senha), id),
    )
    conexao.commit()
    conexao.close()

    flash("Senha redefinida com sucesso.", "sucesso")
    return redirect("/funcionarios")


@funcionarios_bp.route("/logout")
def logout():
    session.clear()

    flash("Sessão encerrada com sucesso.", "sucesso")
    return redirect("/login")
