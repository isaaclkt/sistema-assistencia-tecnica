import sqlite3
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request

from database import conectar, consumir_estoque, estornar_estoque, EstoqueInsuficiente

orcamento_bp = Blueprint("orcamento", __name__)


@orcamento_bp.route("/orcamento")
def pagina_orcamento():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            clientes.nome AS cliente_nome,
            funcionarios.nome AS funcionario_nome
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN funcionarios
            ON funcionarios.id = ordens_servico.funcionario_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM orcamentos
            WHERE orcamentos.ordem_id = ordens_servico.ordem_id
        )
        ORDER BY ordens_servico.ordem_id DESC
    """)
    ordens_servico = cursor.fetchall()

    pecas = cursor.execute("""
        SELECT id, nome, preco_unitario
        FROM pecas
        ORDER BY nome
    """).fetchall()

    cursor.execute("""
        SELECT
            orcamentos.id,
            orcamentos.ordem_id,
            orcamentos.equipamento,
            orcamentos.problema_analisado,
            orcamentos.valor_peca,
            orcamentos.valor_mao_obra,
            orcamentos.desconto,
            orcamentos.valor_total,
            orcamentos.status,
            orcamentos.validade,
            clientes.nome AS nome_cliente,
            funcionarios.nome AS funcionario_nome,
            ordens_servico.problema_relatado,
            (
                SELECT GROUP_CONCAT(
                    pecas.nome || ' (' || ordem_pecas.quantidade || 'x)',
                    ', '
                )
                FROM ordem_pecas
                JOIN pecas
                    ON pecas.id = ordem_pecas.peca_id
                WHERE ordem_pecas.ordem_id = orcamentos.ordem_id
            ) AS peca_nome
        FROM orcamentos
        JOIN clientes
            ON clientes.id = orcamentos.cliente_id
        JOIN ordens_servico
            ON ordens_servico.ordem_id = orcamentos.ordem_id
        LEFT JOIN funcionarios
            ON funcionarios.id = ordens_servico.funcionario_id
        ORDER BY orcamentos.id DESC
    """)
    orcamentos = cursor.fetchall()

    conexao.close()

    return render_template(
        "orcamento.html",
        ordens_servico=ordens_servico,
        pecas=pecas,
        orcamentos=orcamentos,
    )


@orcamento_bp.route("/orcamentos/cadastrar", methods=["POST"])
def criar_orcamento():
    ordem_id = request.form["ordem_id"]
    problema_analisado = request.form["problema_analisado"]
    validade = request.form.get("validade", "").strip()
    pecas_ids = request.form.getlist("peca_id")
    quantidades = request.form.getlist("quantidade")

    try:
        valor_mao_obra = float(request.form.get("valor_mao_obra") or 0)
        desconto = float(request.form.get("desconto") or 0)
    except ValueError:
        flash("Valor da mão de obra e desconto devem ser números válidos.", "erro")
        return redirect("/orcamento")

    if valor_mao_obra < 0 or desconto < 0:
        flash("Valor da mão de obra e desconto não podem ser negativos.", "erro")
        return redirect("/orcamento")

    conexao = conectar()
    cursor = conexao.cursor()

    existente = cursor.execute(
        "SELECT 1 FROM orcamentos WHERE ordem_id = ?", (ordem_id,)
    ).fetchone()
    if existente:
        conexao.close()
        flash("Esta ordem de serviço já possui um orçamento.", "erro")
        return redirect("/orcamento")

    ordem = cursor.execute(
        "SELECT cliente_id, equipamento FROM ordens_servico WHERE ordem_id = ?",
        (ordem_id,),
    ).fetchone()
    if ordem is None:
        conexao.close()
        flash("Ordem de serviço não encontrada.", "erro")
        return redirect("/orcamento")

    # Consolida as peças selecionadas (soma quantidades por peça)
    itens = {}
    try:
        for peca_id, quantidade_texto in zip(pecas_ids, quantidades):
            if not peca_id:
                continue
            itens[peca_id] = itens.get(peca_id, 0) + max(int(quantidade_texto or 1), 1)
    except ValueError:
        conexao.close()
        flash("Quantidade de peças inválida.", "erro")
        return redirect("/orcamento")

    # Vincula as peças à ordem (sem baixar o estoque — isso ocorre na aprovação)
    cursor.execute("DELETE FROM ordem_pecas WHERE ordem_id = ?", (ordem_id,))
    valor_peca = 0.0
    primeiro_peca_id = None
    for peca_id, quantidade in itens.items():
        peca = cursor.execute(
            "SELECT preco_unitario FROM pecas WHERE id = ?", (peca_id,)
        ).fetchone()
        if peca is None:
            continue
        preco = peca["preco_unitario"] or 0
        valor_peca += preco * quantidade
        if primeiro_peca_id is None:
            primeiro_peca_id = peca_id
        cursor.execute(
            "INSERT INTO ordem_pecas (ordem_id, peca_id, quantidade, valor_unitario) VALUES (?, ?, ?, ?)",
            (ordem_id, peca_id, quantidade, preco),
        )

    valor_total = max(valor_peca + valor_mao_obra - desconto, 0)

    try:
        cursor.execute("""
            INSERT INTO orcamentos
            (
                ordem_id,
                cliente_id,
                peca_id,
                equipamento,
                problema_analisado,
                valor_orcamento,
                valor_peca,
                valor_mao_obra,
                desconto,
                valor_total,
                status,
                validade,
                data_cadastro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ordem_id,
            ordem["cliente_id"],
            primeiro_peca_id,
            ordem["equipamento"],
            problema_analisado,
            valor_total,
            valor_peca,
            valor_mao_obra,
            desconto,
            valor_total,
            "Pendente",
            validade,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        ))
        conexao.commit()
        flash("Orçamento cadastrado com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash("Esta ordem de serviço já possui um orçamento.", "erro")

    conexao.close()
    return redirect("/orcamento")


@orcamento_bp.route("/orcamentos/aprovar/<int:orcamento_id>", methods=["POST"])
def aprovar_orcamento(orcamento_id):
    conexao = conectar()
    orc = conexao.execute(
        "SELECT ordem_id, status FROM orcamentos WHERE id = ?", (orcamento_id,)
    ).fetchone()

    if orc is None:
        conexao.close()
        flash("Orçamento não encontrado.", "erro")
        return redirect("/orcamento")

    if orc["status"] != "Pendente":
        conexao.close()
        flash("Este orçamento já foi processado.", "aviso")
        return redirect("/orcamento")

    try:
        # Aprovar baixa o estoque das peças do orçamento.
        consumir_estoque(conexao, orc["ordem_id"])
        conexao.execute(
            "UPDATE orcamentos SET status = 'Aprovado' WHERE id = ?", (orcamento_id,)
        )
        conexao.execute(
            "UPDATE ordens_servico SET status = 'Em andamento' WHERE ordem_id = ?",
            (orc["ordem_id"],),
        )
        conexao.commit()
        flash("Orçamento aprovado. Estoque baixado e ordem movida para 'Em andamento'.", "sucesso")
    except EstoqueInsuficiente as erro:
        conexao.rollback()
        flash(str(erro), "erro")

    conexao.close()
    return redirect("/orcamento")


@orcamento_bp.route("/orcamentos/recusar/<int:orcamento_id>", methods=["POST"])
def recusar_orcamento(orcamento_id):
    conexao = conectar()
    orc = conexao.execute(
        "SELECT ordem_id FROM orcamentos WHERE id = ?", (orcamento_id,)
    ).fetchone()

    if orc is None:
        conexao.close()
        flash("Orçamento não encontrado.", "erro")
        return redirect("/orcamento")

    conexao.execute(
        "UPDATE orcamentos SET status = 'Recusado' WHERE id = ?", (orcamento_id,)
    )
    conexao.execute(
        "UPDATE ordens_servico SET status = 'Cancelado' WHERE ordem_id = ?",
        (orc["ordem_id"],),
    )
    conexao.commit()
    conexao.close()

    flash("Orçamento recusado. Ordem de serviço movida para 'Cancelado'.", "aviso")
    return redirect("/orcamento")


@orcamento_bp.route("/orcamentos/excluir/<int:orcamento_id>", methods=["POST"])
def excluir_orcamento(orcamento_id):
    conexao = conectar()
    orc = conexao.execute(
        "SELECT ordem_id, status FROM orcamentos WHERE id = ?", (orcamento_id,)
    ).fetchone()

    if orc is not None:
        # Se já estava aprovado, o estoque foi baixado — devolve antes de excluir.
        if orc["status"] == "Aprovado":
            estornar_estoque(conexao, orc["ordem_id"])
        conexao.execute("DELETE FROM ordem_pecas WHERE ordem_id = ?", (orc["ordem_id"],))
        conexao.execute("DELETE FROM orcamentos WHERE id = ?", (orcamento_id,))
        conexao.commit()

    conexao.close()

    flash("Orçamento excluído com sucesso.", "sucesso")
    return redirect("/orcamento")
