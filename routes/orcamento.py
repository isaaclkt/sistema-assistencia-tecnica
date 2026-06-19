import sqlite3

from flask import Blueprint, flash, redirect, render_template, request

from database import conectar

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
            GROUP_CONCAT(
                pecas.nome || ' (' || ordem_pecas.quantidade || 'x)',
                ', '
            ) AS peca_nome,
            COALESCE(
                SUM(ordem_pecas.quantidade * ordem_pecas.valor_unitario),
                0
            ) AS valor_peca
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        LEFT JOIN pecas
            ON pecas.id = ordem_pecas.peca_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM orcamentos
            WHERE orcamentos.ordem_id = ordens_servico.ordem_id
        )
        GROUP BY
            ordens_servico.ordem_id,
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            clientes.nome
        ORDER BY ordens_servico.ordem_id DESC
    """)
    ordens_servico = cursor.fetchall()

    cursor.execute("""
        SELECT
            orcamentos.id,
            orcamentos.ordem_id,
            orcamentos.equipamento,
            orcamentos.problema_analisado,
            orcamentos.valor_peca,
            orcamentos.valor_mao_obra,
            orcamentos.valor_total,
            clientes.nome AS nome_cliente,
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
        ORDER BY orcamentos.id DESC
    """)
    orcamentos = cursor.fetchall()

    conexao.close()

    return render_template(
        "orcamento.html",
        ordens_servico=ordens_servico,
        orcamentos=orcamentos,
    )


@orcamento_bp.route("/orcamentos/cadastrar", methods=["POST"])
def criar_orcamento():
    ordem_id = request.form["ordem_id"]
    problema_analisado = request.form["problema_analisado"]
    valor_mao_obra = float(request.form["valor_mao_obra"] or 0)

    conexao = conectar()
    cursor = conexao.cursor()

    orcamento_existente = cursor.execute("""
        SELECT 1
        FROM orcamentos
        WHERE ordem_id = ?
    """, (ordem_id,)).fetchone()

    if orcamento_existente:
        conexao.close()
        flash("Esta ordem de serviço já possui um orçamento.", "erro")
        return redirect("/orcamento")

    ordem = cursor.execute("""
        SELECT
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            MIN(ordem_pecas.peca_id) AS peca_id,
            COALESCE(
                SUM(ordem_pecas.quantidade * ordem_pecas.valor_unitario),
                0
            ) AS valor_peca
        FROM ordens_servico
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        WHERE ordens_servico.ordem_id = ?
        GROUP BY
            ordens_servico.ordem_id,
            ordens_servico.cliente_id,
            ordens_servico.equipamento
    """, (ordem_id,)).fetchone()

    if ordem is None:
        conexao.close()
        flash("Ordem de serviço não encontrada.", "erro")
        return redirect("/orcamento")

    if ordem["peca_id"] is None:
        conexao.close()
        flash(
            "Esta ordem de serviço não possui peças vinculadas. "
            "Edite a ordem e selecione ao menos uma peça antes de gerar o orçamento.",
            "erro",
        )
        return redirect("/orcamento")

    valor_peca = float(ordem["valor_peca"] or 0)
    valor_total = valor_peca + valor_mao_obra

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
                valor_total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ordem_id,
            ordem["cliente_id"],
            ordem["peca_id"],
            ordem["equipamento"],
            problema_analisado,
            valor_total,
            valor_peca,
            valor_mao_obra,
            valor_total,
        ))
        conexao.commit()
        flash("Orçamento cadastrado com sucesso.", "sucesso")
    except sqlite3.IntegrityError:
        conexao.rollback()
        flash("Esta ordem de serviço já possui um orçamento.", "erro")

    conexao.close()
    return redirect("/orcamento")


@orcamento_bp.route("/orcamentos/excluir/<int:orcamento_id>", methods=["POST"])
def excluir_orcamento(orcamento_id):
    conexao = conectar()
    conexao.execute(
        "DELETE FROM orcamentos WHERE id = ?",
        (orcamento_id,),
    )
    conexao.commit()
    conexao.close()

    flash("Orçamento excluído com sucesso.", "sucesso")
    return redirect("/orcamento")
