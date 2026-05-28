from flask import Blueprint, render_template

estoque_bp = Blueprint('estoque', __name__)

@estoque_bp.route('/estoque')
def listar_estoque():
    return render_template('estoque.html')