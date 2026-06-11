from flask import Blueprint, render_template, request, redirect
from database import conectar

estoque_bp = Blueprint('estoque', __name__)

@estoque_bp.route('/estoque')
def listar_estoque():
    db = conectar()

    pecas = db.execute("""
        SELECT *
        FROM pecas
        ORDER BY nome
    """).fetchall()

    db.close()

    return render_template('estoque.html', pecas=pecas)


@estoque_bp.route('/estoque/cadastrar', methods=['POST'])
def cadastrar_peca():
    nome = request.form['nome']
    descricao = request.form['descricao']
    quantidade = request.form['quantidade']
    estoque_minimo = request.form['estoque_minimo']
    preco_unitario = request.form['preco_unitario']
    fornecedor = request.form['fornecedor']

    db = conectar()

    db.execute("""
        INSERT INTO pecas 
        (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor))

    db.commit()
    db.close()

    return redirect('/estoque')

    
@estoque_bp.route('/estoque/excluir/<int:id>', methods=['POST'])
def excluir_peca(id):
    db = conectar()

    db.execute("""
        DELETE FROM pecas
        WHERE id = ?
    """, (id,))

    db.commit()
    db.close()

    return redirect('/estoque')