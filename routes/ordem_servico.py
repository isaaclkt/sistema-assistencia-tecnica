from flask import Blueprint, render_template
from database import conectar

ordem_servico_bp = Blueprint("ordem_servico", __name__)

# Página com as ordens de serviço
@ordem_servico_bp.route("/ordem-servico")
def listar_ordens():
    db = conectar()

    ordens = db.execute("""
        SELECT * FROM ordens_servico
    """).fetchall()

    db.close()

    return render_template("ordem-servico.html", ordens=ordens)

# Página pra criar uma nova ordem de serviço
@ordem_servico_bp.route("/ordem-servico/nova")
def pagina_nova_ordem():
    db = conectar()

    equipamentos = db.execute("""
        SELECT
            equipamentos.id,
            equipamentos.tipo,
            equipamentos.marca,
            equipamentos.modelo,
            clientes.nome AS cliente_nome
        FROM equipamentos
        JOIN clientes
            ON clientes.id = equipamentos.cliente_id
    """).fetchall()

    db.close()

    return render_template(
        "nova-ordem-servico.html",
        equipamentos=equipamentos
    )