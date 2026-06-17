from flask import Blueprint, render_template, request, redirect
from database import conectar

orcamento_bp = Blueprint("orcamento", __name__)


@orcamento_bp.route("/orcamento")
def pagina_orcamento():
    conexao = conectar()
    cursor = conexao.cursor()
<<<<<<< HEAD
=======
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()
>>>>>>> 808bbc70007ed59da307e4f9d07aaecddb6301e2

    cursor.execute("""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            clientes.nome AS cliente_nome
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        ORDER BY ordens_servico.ordem_id DESC
    """)
    ordens_servico = cursor.fetchall()

    cursor.execute("""
        SELECT
            orcamentos.id,
            orcamentos.ordem_id,
            orcamentos.equipamento,
            orcamentos.valor_orcamento,
            clientes.nome AS nome_cliente,
<<<<<<< HEAD
            ordens_servico.problema_relatado
=======
            ordens_servico.defeito_relatado AS problema_informado,
            pecas.nome AS peca_necessaria,
            orcamentos.quantidade,
            orcamentos.valor_unitario,
            orcamentos.valor_mao_obra,
            orcamentos.valor_total,
            orcamentos.status
>>>>>>> 808bbc70007ed59da307e4f9d07aaecddb6301e2
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
        orcamentos=orcamentos
    )


@orcamento_bp.route("/orcamentos/cadastrar", methods=["POST"])
def criar_orcamento():
    ordem_id = request.form["ordem_id"]
    valor_orcamento = request.form["valor_orcamento"]

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT cliente_id, equipamento
        FROM ordens_servico
        WHERE ordem_id = ?
    """, (ordem_id,))
    ordem = cursor.fetchone()

    if ordem is None:
        conexao.close()
        return "Ordem de serviço não encontrada"

    cursor.execute("""
        INSERT INTO orcamentos
        (ordem_id, cliente_id, equipamento, valor_orcamento)
        VALUES (?, ?, ?, ?)
    """, (
        ordem_id,
        ordem["cliente_id"],
        ordem["equipamento"],
        valor_orcamento
    ))

    conexao.commit()
    conexao.close()

    return redirect("/orcamento")
