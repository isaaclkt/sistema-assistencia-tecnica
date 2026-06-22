import sqlite3
from datetime import datetime

from flask import Blueprint, flash, render_template, request, redirect
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

    try:
        cursor.execute(
            """INSERT INTO clientes (nome, cpf, telefone, email, endereco, data_cadastro)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nome, cpf, telefone, email, endereco, datetime.now().strftime("%d/%m/%Y %H:%M")),
        )
        conexao.commit()
        flash(f'Cliente "{nome}" cadastrado com sucesso.', "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash("Não foi possível cadastrar: este CPF já está em uso.", "erro")

    conexao.close()

    return redirect("/cadastro")

# READ
@cadastro_bp.route("/cadastro")
def listar_cadastros():
    pagina = request.args.get("pagina", 1, type=int)
    busca = request.args.get("busca", "").strip()
    por_pagina = 5

    if pagina < 1:
        pagina = 1

    conexao = conectar()
    cursor = conexao.cursor()

    termo_busca = f"%{busca}%"
    parametros_busca = (termo_busca,) * 5
    filtro_busca = """
        WHERE nome LIKE ?
           OR cpf LIKE ?
           OR telefone LIKE ?
           OR email LIKE ?
           OR endereco LIKE ?
    """

    total_clientes = cursor.execute(
        f"SELECT COUNT(*) FROM clientes {filtro_busca}",
        parametros_busca
    ).fetchone()[0]
    total_paginas = max(1, (total_clientes + por_pagina - 1) // por_pagina)

    if pagina > total_paginas:
        pagina = total_paginas

    offset = (pagina - 1) * por_pagina
    cursor.execute(f"""
        SELECT *
        FROM clientes
        {filtro_busca}
        ORDER BY id
        LIMIT ? OFFSET ?
    """, parametros_busca + (por_pagina, offset))
    clientes = cursor.fetchall()

    conexao.close()

    return render_template(
        "gerenciar_clientes.html",
        clientes=clientes,
        busca=busca,
        pagina=pagina,
        total_paginas=total_paginas
    )


# Página editar cliente
@cadastro_bp.route("/clientes/atualizar/<int:id>", methods=["GET"])
def pagina_atualizar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente = cursor.fetchone()

    conexao.close()

    if cliente is None:
        flash("Cliente não encontrado.", "erro")
        return redirect("/cadastro")

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

    try:
        cursor.execute(
            """UPDATE clientes SET nome = ?, cpf = ?, telefone = ?, email = ?, endereco = ? WHERE id = ?""",
            (nome, cpf, telefone, email, endereco, id),
        )
        conexao.commit()
        flash("Cliente atualizado com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash("Não foi possível atualizar: este CPF já está em uso.", "erro")

    conexao.close()

    return redirect("/cadastro")

# DELETE
@cadastro_bp.route("/clientes/excluir/<int:id>", methods=["POST"])
def deletar_cliente(id):
    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conexao.commit()
        flash("Cliente excluído com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash(
            "Não é possível excluir este cliente porque ele possui registros vinculados.",
            "erro",
        )

    conexao.close()

    return redirect("/cadastro")
