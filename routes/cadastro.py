import sqlite3
from flask import Blueprint, render_template, request, redirect
from database import conectar

cadastro_bp = Blueprint("cadastro", __name__)

@cadastro_bp.route("/cadastro")
def listar_cadastros():
    return render_template("gerenciar_clientes.html")

@cadastro_bp.route("/clientes/novo")
def pagina_adicionar_cliente():
    return render_template("adicionar_clientes.html")


conexao = sqlite3.connect("database/sistema.db")

cursor = conexao.cursor()

#CRUD

#CREATE

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
        INSERT INTO clientes (nome, cpf, telefone, email, endereco)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, cpf, telefone, email, endereco))

    conexao.commit()
    conexao.close()

    return redirect("/cadastro")



#READ
def listar_clientes():
    comando = f'SELECT * FROM clientes'
    cursor.execute(comando)
    resultados = cursor.fetchall()

    for linha in resultados:
        print(linha)

    cursor.close()
    conexao.close()

#UPDATE

def atualizar_cliente():
    nome = input("Digite o nome do cliente que deseja atualizar: ")
    telefone = input("Digite o novo telefone do cliente: ")
    endereco = input("Digite o novo endereço do cliente: ")

    comando = f'UPDATE clientes SET telefone = "{telefone}", endereco = "{endereco}" WHERE nome = "{nome}"'
    cursor.execute(comando)
    conexao.commit()

#DELETE

def deletar_cliente():
    nome = input("Digite o nome do cliente que deseja deletar: ") 
    comando = f'DELETE FROM clientes WHERE nome = "{nome}"'
    cursor.execute(comando)
    conexao.commit()