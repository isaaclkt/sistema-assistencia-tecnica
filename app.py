from flask import Flask, render_template
from routes.estoque import estoque_bp
from routes.ordem_servico import ordem_servico_bp
from routes.cadastro import cadastro_bp

# Cria a aplicação Flask
app = Flask(__name__)

# Registra o módulo estoque
app.register_blueprint(estoque_bp)

# Registra o módulo ordem_servico
app.register_blueprint(ordem_servico_bp)

# Registra o módulo cadastro
app.register_blueprint(cadastro_bp)


# Página inicial
@app.route("/")
def home():
    return render_template("home.html")

# Executa o servidor
if __name__ == "__main__":
    app.run(debug=True, port=5001)
