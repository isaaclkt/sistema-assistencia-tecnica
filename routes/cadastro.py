import sqlite3
from flask import Blueprint, render_template, request, redirect
from database import conectar

cadastro_bp = Blueprint("cadastro", __name__)


# Página adicionar cliente
@cadastro_bp.route("/clientes/novo")
def pagina_adicionar_cliente():
    return render_template("adicionar_clientes.html")



# CREATE
@cadastro_bp.route("/clientes/cadastrar", methods=["POST"])
def cadastrar_cliente():

    nome = request.form["nome"]
    cpf = request.form["cpf"]
    telefone = request.form["telefone"]
    email = request.form["email"]
    endereco = request.form["endereco"]

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO clientes
        (nome, cpf, telefone, email, endereco)

        VALUES (?, ?, ?, ?, ?)
    """, (nome, cpf, telefone, email, endereco))

    conexao.commit()
    conexao.close()

    return redirect("/cadastro")

@cadastro_bp.route("/cadastro")
def listar_cadastros():

    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    conexao.close()

    return render_template(
        "gerenciar_clientes.html",
        clientes=clientes
    )


# Página editar cliente
@cadastro_bp.route("/clientes/atualizar/<int:id>", methods=["GET"])
def pagina_atualizar_cliente(id):
    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente = cursor.fetchone()

    conexao.close()

    return render_template("editar_clientes.html", cliente=cliente)


# UPDATE
@cadastro_bp.route("/clientes/atualizar/<int:id>", methods=["POST"])
def atualizar_cliente(id):
    nome = request.form["nome"]
    cpf = request.form["cpf"]
    telefone = request.form["telefone"]
    email = request.form["email"]
    endereco = request.form["endereco"]

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE clientes
        SET nome = ?, cpf = ?, telefone = ?, email = ?, endereco = ?
        WHERE id = ?
    """, (nome, cpf, telefone, email, endereco, id))

    conexao.commit()
    conexao.close()

    return redirect("/cadastro")

# DELETE
@cadastro_bp.route("/clientes/excluir/<int:id>")
def deletar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))

    conexao.commit()
    conexao.close()

    return redirect("/cadastro")