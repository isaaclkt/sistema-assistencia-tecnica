import sqlite3

from flask import Blueprint, render_template, request, redirect, session
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

    conexao.commit()
    conexao.close()


@funcionarios_bp.route("/funcionarios/cadastrar", methods=["GET", "POST"])
def cadastrar_funcionario():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])
        cargo = request.form["cargo"]

        conexao = conectar()

        try:
            conexao.execute("""
                INSERT INTO funcionarios (nome, email, senha, cargo)
                VALUES (?, ?, ?, ?)
            """, (nome, email, senha, cargo))
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
            SELECT id, nome, email, senha, cargo
            FROM funcionarios
            WHERE email = ?
        """, (email,)).fetchone()
        conexao.close()

        if funcionario and check_password_hash(funcionario["senha"], senha):
            session["funcionario_id"] = funcionario["id"]
            session["funcionario_nome"] = funcionario["nome"]
            session["funcionario_cargo"] = funcionario["cargo"]

            return redirect("/")

        return render_template(
            "login.html",
            erro="Email ou senha invalidos. Tente novamente."
        )

    return render_template("login.html")


@funcionarios_bp.route("/logout")
def logout():
    session.clear()

    return redirect("/login")
