from flask import Flask, render_template, request, redirect, session
from routes.estoque import estoque_bp
from routes.ordem_servico import ordem_servico_bp
from routes.cadastro import cadastro_bp
from routes.orcamento import orcamento_bp
from routes.funcionarios import funcionarios_bp, criar_tabela_funcionarios
from routes.home import home_bp
from routes.acompanhamento import acompanhamento_bp

# Cria a aplicação Flask
app = Flask(__name__)
app.secret_key = "sistema-assistencia-tecnica"


@app.template_filter("moeda")
def formatar_moeda(valor):
    """Formata um número no padrão monetário brasileiro: R$ 1.234,56."""
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        numero = 0.0
    formatado = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


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


# Página inicial
@app.before_request
def proteger_rotas():
    rotas_livres = (
        "/login",
        "/funcionarios/cadastrar",
        "/acompanhamento",
        "/static",
    )

    if request.path.startswith(rotas_livres):
        return None
    # Coloquem as rotas que queiram acessar depois de logado
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

    return None


if __name__ == "__main__":
    app.run(debug=True, port=5001)
