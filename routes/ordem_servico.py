from flask import Blueprint, render_template

ordem_servico_bp = Blueprint("ordem_servico", __name__)

@ordem_servico_bp.route("/ordem-servico")
def listar_ordens():
    return render_template("ordem-servico.html")
