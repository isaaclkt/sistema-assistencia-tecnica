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
    #pra quem ta vendo depois isso é para quem não ta logado não conseguir ver o resto do site mas talvez de errado com os outros modulos se for por mais coisa depois
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
    )

    # Bloqueia a home e os modulos internos quando nao ha funcionario autenticado.
    if (request.path == "/" or request.path.startswith(rotas_protegidas)) and "funcionario_id" not in session:
        return redirect("/login")

    return None


if __name__ == "__main__":
    app.run(debug=True, port=5001)
