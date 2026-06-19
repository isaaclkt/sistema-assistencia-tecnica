from flask import Blueprint, flash, render_template, request, redirect, send_file
from database import conectar
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile


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

    total_pecas = db.execute("""
        SELECT COUNT(*) as total
        FROM pecas
    """).fetchone()['total']

    estoque_baixo = db.execute("""
        SELECT COUNT(*) as total
        FROM pecas
        WHERE quantidade <= estoque_minimo
    """).fetchone()['total']

    total_movimentacoes = db.execute("""
        SELECT COUNT(*) as total
        FROM movimentacoes_estoque
    """).fetchone()['total']

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
    quantidade = int(request.form['quantidade'])
    estoque_minimo = int(request.form['estoque_minimo'] or 0)
    preco_unitario = float(request.form['preco_unitario'] or 0)
    fornecedor = request.form['fornecedor']

    if quantidade < 0:
        return "Quantidade não pode ser negativa"
    
    if estoque_minimo < 0:
        return "Estoque mínimo não pode ser negativo"
    
    if preco_unitario < 0:
        return "Preço unitário não pode ser negativo"

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

    if quantidade <= 0:
        return "Quantidade deve ser maior que zero"
    
    if tipo == 'saida' and quantidade > peca['quantidade']:
        return flash("Estoque insuficiente")

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

@estoque_bp.route('/estoque/relatorio/pdf')
def gerar_relatorio_pdf():
    from flask import send_file
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    import tempfile
    from datetime import datetime

    db = conectar()

    pecas = db.execute("""
        SELECT *
        FROM pecas
        ORDER BY nome
    """).fetchall()

    total_pecas = len(pecas)

    estoque_baixo = sum(
        1 for peca in pecas
        if peca['quantidade'] <= peca['estoque_minimo']
    )

    db.close()

    arquivo_temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    pdf = SimpleDocTemplate(arquivo_temp.name)

    estilos = getSampleStyleSheet()

    elementos = []

    elementos.append(
        Paragraph(
            "SISTEMA DE ASSISTÊNCIA TÉCNICA",
            estilos['Title']
        )
    )

    elementos.append(
        Paragraph(
            "Relatório de Estoque",
            estilos['Heading2']
        )
    )

    data_emissao = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    elementos.append(
        Paragraph(
            f"Data de emissão: {data_emissao}",
            estilos['Normal']
        )
    )

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph(
            f"Total de peças cadastradas: {total_pecas}",
            estilos['Normal']
        )
    )

    elementos.append(
        Paragraph(
            f"Itens com estoque baixo: {estoque_baixo}",
            estilos['Normal']
        )
    )

    elementos.append(Spacer(1, 20))

    dados = [
        [
            "Nome",
            "Quantidade",
            "Est. Mínimo",
            "Preço",
            "Status"
        ]
    ]

    for peca in pecas:

        status = (
            "Baixo Estoque"
            if peca['quantidade'] <= peca['estoque_minimo']
            else "OK"
        )

        dados.append([
            peca['nome'],
            str(peca['quantidade']),
            str(peca['estoque_minimo']),
            f"R$ {peca['preco_unitario']}",
            status
        ])

    tabela = Table(dados)

    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
    ]))

    elementos.append(tabela)

    pdf.build(elementos)

    return send_file(
        arquivo_temp.name,
        as_attachment=True,
        download_name="relatorio_estoque.pdf"
    )

