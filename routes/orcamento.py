from flask import Blueprint, render_template, request, redirect
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
            pecas.id AS peca_id,
            pecas.nome AS peca_nome,
            pecas.preco_unitario AS valor_peca
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        LEFT JOIN pecas
            ON pecas.id = ordem_pecas.peca_id
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
            pecas.nome AS peca_nome
        FROM orcamentos
        JOIN clientes
            ON clientes.id = orcamentos.cliente_id
        JOIN ordens_servico
            ON ordens_servico.ordem_id = orcamentos.ordem_id
        LEFT JOIN pecas
            ON pecas.id = orcamentos.peca_id
        ORDER BY orcamentos.id DESC
    """)
    orcamentos = cursor.fetchall()

    conexao.close()

    return render_template(
        "orcamento.html",
        ordens_servico=ordens_servico,
        orcamentos=orcamentos
    )


@orcamento_bp.route("/orcamentos/cadastrar", methods=["POST"])
def criar_orcamento():
    ordem_id = request.form["ordem_id"]
    problema_analisado = request.form["problema_analisado"]
    valor_mao_obra = float(request.form["valor_mao_obra"] or 0)

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            ordem_pecas.peca_id,
            pecas.preco_unitario AS valor_peca
        FROM ordens_servico
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        LEFT JOIN pecas
            ON pecas.id = ordem_pecas.peca_id
        WHERE ordens_servico.ordem_id = ?
    """, (ordem_id,))
    ordem = cursor.fetchone()

    if ordem is None:
        conexao.close()
        return "Ordem de serviço nao encontrada"

    if ordem["peca_id"] is None:
        conexao.close()
        return "Ordem de serviço sem peça vinculada"

    valor_peca = float(ordem["valor_peca"] or 0)
    valor_total = valor_peca + valor_mao_obra

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
        valor_total
    ))

    conexao.commit()
    conexao.close()

    return redirect("/orcamento")
