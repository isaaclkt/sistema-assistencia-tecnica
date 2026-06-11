from flask import Blueprint, render_template, request, redirect
from database import conectar

orcamento_bp = Blueprint("orcamento", __name__)


@orcamento_bp.route("/orcamento")
def pagina_orcamento():
    conexao = conectar()
    cursor = conexao.cursor()

    # Buscar clientes para aparecer no select
    cursor.execute("SELECT id, nome, produto FROM clientes")
    clientes = cursor.fetchall()

    # Buscar ordens de serviço para aparecer no select
    cursor.execute("""
        SELECT id, defeito_relatado AS problema
        FROM ordens_servico
    """)
    ordens_servico = cursor.fetchall()

    # Buscar peças para aparecer no select
    cursor.execute("SELECT id, nome, preco_unitario FROM pecas")
    pecas = cursor.fetchall()

    # Buscar orçamentos cadastrados
    cursor.execute("""
        SELECT 
            orcamentos.id,
            clientes.nome AS nome_cliente,
            clientes.produto AS produto_cliente,
            ordens_servico.defeito_relatado AS problema_informado,
            pecas.nome AS peca_necessaria,
            orcamentos.quantidade,
            orcamentos.valor_unitario,
            orcamentos.valor_mao_obra,
            orcamentos.valor_total,
            orcamentos.status
        FROM orcamentos
        JOIN clientes 
            ON orcamentos.cliente_id = clientes.id
        JOIN ordens_servico 
            ON orcamentos.ordem_servico_id = ordens_servico.id
        JOIN pecas 
            ON orcamentos.peca_id = pecas.id
    """)
    orcamentos = cursor.fetchall()

    conexao.close()

    return render_template(
        "orcamento.html",
        clientes=clientes,
        ordens_servico=ordens_servico,
        pecas=pecas,
        orcamentos=orcamentos
    )


@orcamento_bp.route("/orcamentos/cadastrar", methods=["POST"])
def criar_orcamento():
    cliente_id = request.form["cliente_id"]
    ordem_servico_id = request.form["ordem_servico_id"]
    peca_id = request.form["peca_id"]
    quantidade = int(request.form["quantidade"])
    valor_mao_obra = float(request.form["valor_mao_obra"])
    status = request.form["status"]

    conexao = conectar()
    cursor = conexao.cursor()

    # Buscar o preço da peça direto do estoque
    cursor.execute("SELECT preco_unitario FROM pecas WHERE id = ?", (peca_id,))
    peca = cursor.fetchone()

    valor_unitario = float(peca["preco_unitario"])
    valor_total = (valor_unitario * quantidade) + valor_mao_obra

    cursor.execute("""
        INSERT INTO orcamentos 
        (cliente_id, ordem_servico_id, peca_id, quantidade, valor_unitario, valor_mao_obra, valor_total, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente_id,
        ordem_servico_id,
        peca_id,
        quantidade,
        valor_unitario,
        valor_mao_obra,
        valor_total,
        status
    ))

    conexao.commit()
    conexao.close()

    return redirect("/orcamento")
