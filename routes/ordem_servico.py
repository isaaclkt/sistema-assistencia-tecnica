from flask import Blueprint, render_template, request, redirect
from database import conectar

ordem_servico_bp = Blueprint("ordem_servico", __name__)

# Página com as ordens de serviço
@ordem_servico_bp.route("/ordem-servico")
def listar_ordens():
    db = conectar()

    ordens = db.execute("""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            ordens_servico.status,
            clientes.nome AS cliente_nome
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
    """).fetchall()

    db.close()

    return render_template("ordem-servico.html", ordens=ordens)

# Página pra criar uma nova ordem de serviço
@ordem_servico_bp.route("/ordem-servico/nova")
def pagina_nova_ordem():
    db = conectar()

    clientes = db.execute("""
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """).fetchall()

    db.close()

    return render_template(
        "nova-ordem-servico.html",
        clientes=clientes
    )


@ordem_servico_bp.route("/ordem-servico/cadastrar", methods=["POST"])
def cadastrar_ordem():
    cliente_id = request.form["cliente_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]

    db = conectar()

    db.execute("""
        INSERT INTO ordens_servico
        (cliente_id, equipamento, problema_relatado, status)
        VALUES (?, ?, ?, ?)
    """, (cliente_id, equipamento, problema_relatado, status))

    db.commit()
    db.close()

    return redirect("/ordem-servico")
