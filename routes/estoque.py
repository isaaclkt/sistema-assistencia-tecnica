from flask import Blueprint, render_template, request, redirect
from database import conectar
from datetime import datetime

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

@estoque_bp.route('/estoque/editar/<int:id>')
def editar_peca(id):
    db = conectar()

    peca = db.execute("""
        SELECT *
        FROM pecas
        WHERE id = ?
    """, (id,)).fetchone()

    db.close()

    return render_template('editar_peca.html', peca=peca)


@estoque_bp.route('/estoque/atualizar/<int:id>', methods=['POST'])
def atualizar_peca(id):
    nome = request.form['nome']
    descricao = request.form['descricao']
    quantidade = request.form['quantidade']
    estoque_minimo = request.form['estoque_minimo']
    preco_unitario = request.form['preco_unitario']
    fornecedor = request.form['fornecedor']

    db = conectar()

    db.execute("""
        UPDATE pecas
        SET nome = ?,
            descricao = ?,
            quantidade = ?,
            estoque_minimo = ?,
            preco_unitario = ?,
            fornecedor = ?
        WHERE id = ?
    """, (
        nome,
        descricao,
        quantidade,
        estoque_minimo,
        preco_unitario,
        fornecedor,
        id
    ))

    db.commit()
    db.close()

    return redirect('/estoque')

@estoque_bp.route('/estoque/movimentar/<int:id>')
def movimentar_peca(id):
    db = conectar()

    peca = db.execute("""
        SELECT *
        FROM pecas
        WHERE id = ?
    """, (id,)).fetchone()

    db.close()
    return render_template('movimentar_estoque.html', peca=peca)

@estoque_bp.route('/estoque/movimentar/<int:id>', methods=['POST'])
def salvar_movimentacao(id):

    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])
    observacao = request.form['observacao']

    db = conectar()

    peca = db.execute("""
        SELECT quantidade
        FROM pecas
        WHERE id = ?
    """, (id,)).fetchone()

    estoque_atual = peca['quantidade']

    if tipo == 'Entrada':
        novo_estoque = estoque_atual + quantidade
    else:
        novo_estoque = estoque_atual - quantidade

        if novo_estoque < 0:
            db.close()
            return "Estoque insuficiente"

    db.execute("""
        UPDATE pecas
        SET quantidade = ?
        WHERE id = ?
    """, (novo_estoque, id))

    db.execute("""
        INSERT INTO movimentacoes_estoque
        (
            peca_id,
            tipo,
            quantidade,
            data_movimentacao,
            observacao
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        id,
        tipo,
        quantidade,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        observacao
    ))

    db.commit()
    db.close()

    return redirect('/estoque')

@estoque_bp.route('/estoque/historico')
def historico_movimentacoes():
    db = conectar()

    movimentacoes = db.execute("""
         SELECT
            m.id,
            p.nome AS nome_peca,
            m.tipo,
            m.quantidade,
            m.data_movimentacao,
            m.observacao
        FROM movimentacoes_estoque m
        INNER JOIN pecas p
            ON p.id = m.peca_id
        ORDER BY m.data_movimentacao DESC
    """).fetchall()

    db.close()

    return render_template('historico_movimentacoes.html', movimentacoes=movimentacoes)