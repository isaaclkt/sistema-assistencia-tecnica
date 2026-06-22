import sqlite3
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, send_file
from database import conectar

estoque_bp = Blueprint('estoque', __name__)


@estoque_bp.route('/estoque')
def listar_estoque():
    db = conectar()

    busca = request.args.get('busca', '')
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 5

    if pagina < 1:
        pagina = 1

    termo_busca = f'%{busca}%'
    parametros_busca = (termo_busca,) * 3

    total_filtrado = db.execute("""
        SELECT COUNT(*) AS total
        FROM pecas
        WHERE nome LIKE ?
           OR descricao LIKE ?
           OR fornecedor LIKE ?
    """, parametros_busca).fetchone()['total']

    total_paginas = max(1, (total_filtrado + por_pagina - 1) // por_pagina)

    if pagina > total_paginas:
        pagina = total_paginas

    offset = (pagina - 1) * por_pagina

    pecas = db.execute("""
        SELECT *
        FROM pecas
        WHERE nome LIKE ?
           OR descricao LIKE ?
           OR fornecedor LIKE ?
        ORDER BY nome
        LIMIT ? OFFSET ?
    """, parametros_busca + (por_pagina, offset)).fetchall()

    total_pecas = db.execute(
        "SELECT COUNT(*) AS total FROM pecas"
    ).fetchone()['total']

    estoque_baixo = db.execute(
        "SELECT COUNT(*) AS total FROM pecas WHERE quantidade <= estoque_minimo"
    ).fetchone()['total']

    total_movimentacoes = db.execute(
        "SELECT COUNT(*) AS total FROM movimentacoes_estoque"
    ).fetchone()['total']

    db.close()

    return render_template(
        'estoque.html',
        pecas=pecas,
        busca=busca,
        pagina=pagina,
        total_paginas=total_paginas,
        total_pecas=total_pecas,
        estoque_baixo=estoque_baixo,
        total_movimentacoes=total_movimentacoes
    )


@estoque_bp.route('/estoque/cadastrar', methods=['POST'])
def cadastrar_peca():
    nome = request.form['nome']
    descricao = request.form['descricao']
    fornecedor = request.form['fornecedor']

    try:
        quantidade = int(request.form['quantidade'] or 0)
        estoque_minimo = int(request.form['estoque_minimo'] or 0)
        preco_unitario = float(request.form['preco_unitario'] or 0)
    except ValueError:
        flash("Quantidade, estoque mínimo e preço devem ser números válidos.", "erro")
        return redirect('/estoque')

    if quantidade < 0 or estoque_minimo < 0 or preco_unitario < 0:
        flash("Quantidade, estoque mínimo e preço não podem ser negativos.", "erro")
        return redirect('/estoque')

    db = conectar()
    db.execute("""
        INSERT INTO pecas
        (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor))
    db.commit()
    db.close()

    flash(f'Peça "{nome}" cadastrada com sucesso.', "sucesso")
    return redirect('/estoque')


@estoque_bp.route('/estoque/editar/<int:id>')
def editar_peca(id):
    db = conectar()
    peca = db.execute("SELECT * FROM pecas WHERE id = ?", (id,)).fetchone()
    db.close()

    if peca is None:
        flash("Peça não encontrada.", "erro")
        return redirect('/estoque')

    return render_template('editar_peca.html', peca=peca)


@estoque_bp.route('/estoque/atualizar/<int:id>', methods=['POST'])
def atualizar_peca(id):
    nome = request.form['nome']
    descricao = request.form['descricao']
    fornecedor = request.form['fornecedor']

    try:
        quantidade = int(request.form['quantidade'] or 0)
        estoque_minimo = int(request.form['estoque_minimo'] or 0)
        preco_unitario = float(request.form['preco_unitario'] or 0)
    except ValueError:
        flash("Quantidade, estoque mínimo e preço devem ser números válidos.", "erro")
        return redirect(f'/estoque/editar/{id}')

    if quantidade < 0 or estoque_minimo < 0 or preco_unitario < 0:
        flash("Quantidade, estoque mínimo e preço não podem ser negativos.", "erro")
        return redirect(f'/estoque/editar/{id}')

    db = conectar()
    db.execute("""
        UPDATE pecas
        SET nome = ?, descricao = ?, quantidade = ?, estoque_minimo = ?,
            preco_unitario = ?, fornecedor = ?
        WHERE id = ?
    """, (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor, id))
    db.commit()
    db.close()

    flash("Peça atualizada com sucesso.", "sucesso")
    return redirect('/estoque')


@estoque_bp.route('/estoque/excluir/<int:id>', methods=['POST'])
def excluir_peca(id):
    db = conectar()
    try:
        db.execute("DELETE FROM pecas WHERE id = ?", (id,))
        db.commit()
        flash("Peça excluída com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        db.rollback()
        flash(
            "Não é possível excluir esta peça porque ela possui movimentações ou "
            "está vinculada a ordens de serviço.",
            "erro",
        )
    finally:
        db.close()

    return redirect('/estoque')


@estoque_bp.route('/estoque/movimentar/<int:id>')
def movimentar_peca(id):
    db = conectar()
    peca = db.execute("SELECT * FROM pecas WHERE id = ?", (id,)).fetchone()
    db.close()

    if peca is None:
        flash("Peça não encontrada.", "erro")
        return redirect('/estoque')

    return render_template('movimentar_estoque.html', peca=peca)


@estoque_bp.route('/estoque/movimentar/<int:id>', methods=['POST'])
def salvar_movimentacao(id):
    tipo = request.form['tipo']
    observacao = request.form['observacao']

    if tipo not in ('Entrada', 'Saida'):
        flash("Tipo de movimentação inválido.", "erro")
        return redirect(f'/estoque/movimentar/{id}')

    try:
        quantidade = int(request.form['quantidade'] or 0)
    except ValueError:
        flash("A quantidade deve ser um número válido.", "erro")
        return redirect(f'/estoque/movimentar/{id}')

    if quantidade <= 0:
        flash("A quantidade deve ser maior que zero.", "erro")
        return redirect(f'/estoque/movimentar/{id}')

    db = conectar()
    peca = db.execute("SELECT quantidade FROM pecas WHERE id = ?", (id,)).fetchone()

    if peca is None:
        db.close()
        flash("Peça não encontrada.", "erro")
        return redirect('/estoque')

    estoque_atual = peca['quantidade']

    if tipo == 'Entrada':
        novo_estoque = estoque_atual + quantidade
    else:
        novo_estoque = estoque_atual - quantidade
        if novo_estoque < 0:
            db.close()
            flash(
                f"Estoque insuficiente: há apenas {estoque_atual} unidade(s) disponível(is).",
                "erro",
            )
            return redirect(f'/estoque/movimentar/{id}')

    db.execute("UPDATE pecas SET quantidade = ? WHERE id = ?", (novo_estoque, id))
    db.execute("""
        INSERT INTO movimentacoes_estoque
        (peca_id, tipo, quantidade, data_movimentacao, observacao)
        VALUES (?, ?, ?, ?, ?)
    """, (
        id,
        tipo,
        quantidade,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        observacao,
    ))
    db.commit()
    db.close()

    flash(
        f"{tipo} de {quantidade} unidade(s) registrada. Novo estoque: {novo_estoque}.",
        "sucesso",
    )
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
        INNER JOIN pecas p ON p.id = m.peca_id
        ORDER BY m.data_movimentacao DESC
    """).fetchall()
    db.close()

    return render_template('historico_movimentacoes.html', movimentacoes=movimentacoes)


@estoque_bp.route('/estoque/relatorio/pdf')
def gerar_relatorio_pdf():
    import tempfile
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    db = conectar()
    pecas = db.execute("SELECT * FROM pecas ORDER BY nome").fetchall()
    total_pecas = len(pecas)
    estoque_baixo = sum(
        1 for peca in pecas if peca['quantidade'] <= peca['estoque_minimo']
    )
    db.close()

    arquivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(arquivo_temp.name)
    estilos = getSampleStyleSheet()

    elementos = [
        Paragraph("SISTEMA DE ASSISTÊNCIA TÉCNICA", estilos['Title']),
        Paragraph("Relatório de Estoque", estilos['Heading2']),
        Paragraph(
            f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            estilos['Normal'],
        ),
        Spacer(1, 20),
        Paragraph(f"Total de peças cadastradas: {total_pecas}", estilos['Normal']),
        Paragraph(f"Itens com estoque baixo: {estoque_baixo}", estilos['Normal']),
        Spacer(1, 20),
    ]

    dados = [["Nome", "Quantidade", "Est. Mínimo", "Preço", "Status"]]
    for peca in pecas:
        status = "Baixo Estoque" if peca['quantidade'] <= peca['estoque_minimo'] else "OK"
        dados.append([
            peca['nome'],
            str(peca['quantidade']),
            str(peca['estoque_minimo']),
            f"R$ {peca['preco_unitario']}",
            status,
        ])

    tabela = Table(dados)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elementos.append(tabela)
    pdf.build(elementos)

    return send_file(
        arquivo_temp.name,
        as_attachment=True,
        download_name="relatorio_estoque.pdf",
    )
