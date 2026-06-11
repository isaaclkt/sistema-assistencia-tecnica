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