from flask import Blueprint, render_template, request, redirect
from database import conectar

orcamento_bp = Blueprint("orcamento", __name__)

# Página do orçamento
@orcamento_bp.route("/orcamento")
def pagina_adicionar_orcamento():
    return render_template("orcamento.html")

