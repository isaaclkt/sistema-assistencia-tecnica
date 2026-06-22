import os

from flask import Flask, render_template, request, redirect, session, flash
from routes.estoque import estoque_bp
from routes.ordem_servico import ordem_servico_bp
from routes.cadastro import cadastro_bp
from routes.orcamento import orcamento_bp
from routes.funcionarios import funcionarios_bp, criar_tabela_funcionarios
from routes.home import home_bp
from routes.acompanhamento import acompanhamento_bp
from database import conectar

# Cria a aplicação Flask
app = Flask(__name__)
# Chave de sessão vem do ambiente em produção; fallback apenas para desenvolvimento.
app.secret_key = os.environ.get("SECRET_KEY", "dev-inseguro-troque-em-producao")


@app.template_filter("moeda")
def formatar_moeda(valor):
    """Formata um número no padrão monetário brasileiro: R$ 1.234,56."""
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        numero = 0.0
    formatado = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


@app.context_processor
def injetar_alertas_estoque():
    """Disponibiliza a contagem de peças com estoque baixo para a navbar."""
    if "funcionario_id" not in session:
        return {"alerta_estoque_baixo": 0}
    conexao = conectar()
    total = conexao.execute(
        "SELECT COUNT(*) FROM pecas WHERE quantidade <= estoque_minimo"
    ).fetchone()[0]
    conexao.close()
    return {"alerta_estoque_baixo": total}


criar_tabela_funcionarios()

# Registra o módulo estoque
app.register_blueprint(estoque_bp)

# Registra o módulo ordem_servico
app.register_blueprint(ordem_servico_bp)

# Registra o módulo cadastro
app.register_blueprint(cadastro_bp)

# Registra o módulo orçamento
app.register_blueprint(orcamento_bp)

#Registra o modulo de usuario e login
app.register_blueprint(funcionarios_bp)

# Registra a página home
app.register_blueprint(home_bp)

app.register_blueprint(acompanhamento_bp)


def _sem_funcionarios():
    """True quando ainda não existe nenhum funcionário (permite criar o 1º admin)."""
    conexao = conectar()
    total = conexao.execute("SELECT COUNT(*) FROM funcionarios").fetchone()[0]
    conexao.close()
    return total == 0


# Página inicial
@app.before_request
def proteger_rotas():
    rotas_livres = (
        "/login",
        "/acompanhamento",
        "/static",
    )

    if request.path.startswith(rotas_livres):
        return None

    # Bootstrap: criar o primeiro funcionário (admin) é permitido sem login.
    if request.path == "/funcionarios/cadastrar" and _sem_funcionarios():
        return None

    rotas_protegidas = (
        "/cadastro",
        "/clientes",
        "/equipamentos",
        "/ordem-servico",
        "/estoque",
        "/orcamento",
        "/orcamentos",
        "/relatorios",
        "/configuracoes",
        "/funcionarios",
    )

    # Bloqueia a home e os modulos internos quando nao ha funcionario autenticado.
    if (request.path == "/" or request.path.startswith(rotas_protegidas)) and "funcionario_id" not in session:
        return redirect("/login")

    # Área de funcionários (gestão de acessos) é exclusiva de administradores.
    if request.path.startswith("/funcionarios") and session.get("funcionario_perfil") != "admin":
        flash("Acesso restrito a administradores.", "erro")
        return redirect("/")

    return None


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=5001)
