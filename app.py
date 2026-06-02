from flask import Flask, render_template
from routes.estoque import estoque_bp

# Cria a aplicação Flask
app = Flask(__name__)

# Registra o módulo estoque
app.register_blueprint(estoque_bp)

# Página inicial
@app.route("/")
def home():
    return render_template("home.html")

# Executa o servidor
if __name__ == "__main__":
    app.run(debug=True)
