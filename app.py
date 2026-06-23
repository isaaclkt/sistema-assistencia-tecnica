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

app = Flask(__name__)
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

app.register_blueprint(estoque_bp)

app.register_blueprint(ordem_servico_bp)

app.register_blueprint(cadastro_bp)

app.register_blueprint(orcamento_bp)

app.register_blueprint(funcionarios_bp)

app.register_blueprint(home_bp)

app.register_blueprint(acompanhamento_bp)


def _sem_funcionarios():
    """True quando ainda não existe nenhum funcionário (permite criar o 1º admin)."""
    conexao = conectar()
    total = conexao.execute("SELECT COUNT(*) FROM funcionarios").fetchone()[0]
    conexao.close()
    return total == 0


# ---------------------------------------------------------------------------
# RBAC — permissões por endpoint (papéis: admin, atendente, tecnico).
# Endpoints não listados exigem apenas estar autenticado (ex.: dashboard).
# ---------------------------------------------------------------------------
TODOS = {"admin", "atendente", "tecnico"}

PERMISSOES = {
    # Clientes
    "cadastro.listar_cadastros": {"admin", "atendente"},
    "cadastro.pagina_adicionar_cliente": {"atendente"},
    "cadastro.cadastrar_cliente": {"atendente"},
    "cadastro.pagina_atualizar_cliente": {"atendente"},
    "cadastro.atualizar_cliente": {"atendente"},
    "cadastro.deletar_cliente": {"admin"},
    # Ordens de serviço
    "ordem_servico.listar_ordens": TODOS,
    "ordem_servico.visualizar_ordem": TODOS,
    "ordem_servico.gerar_os_pdf": TODOS,
    "ordem_servico.pagina_nova_ordem": {"atendente"},
    "ordem_servico.cadastrar_ordem": {"atendente"},
    "ordem_servico.pagina_editar_ordem": {"atendente", "tecnico"},
    "ordem_servico.atualizar_ordem": {"atendente", "tecnico"},
    "ordem_servico.excluir_ordem": {"admin"},
    # Orçamentos
    "orcamento.pagina_orcamento": TODOS,
    "orcamento.criar_orcamento": {"atendente", "tecnico"},
    "orcamento.aprovar_orcamento": {"admin", "atendente"},
    "orcamento.recusar_orcamento": {"admin", "atendente"},
    "orcamento.excluir_orcamento": {"admin"},
    # Estoque
    "estoque.listar_estoque": TODOS,
    "estoque.historico_movimentacoes": TODOS,
    "estoque.cadastrar_peca": {"admin"},
    "estoque.editar_peca": {"admin"},
    "estoque.atualizar_peca": {"admin"},
    "estoque.excluir_peca": {"admin"},
    "estoque.movimentar_peca": {"admin"},
    "estoque.salvar_movimentacao": {"admin"},
    "estoque.gerar_relatorio_pdf": {"admin"},
    "estoque.gerar_relatorio_excel": {"admin"},
    # Funcionários (administração)
    "funcionarios.listar_funcionarios": {"admin"},
    "funcionarios.pagina_editar_funcionario": {"admin"},
    "funcionarios.atualizar_funcionario": {"admin"},
    "funcionarios.alternar_status_funcionario": {"admin"},
    "funcionarios.redefinir_senha": {"admin"},
    "funcionarios.cadastrar_funcionario": {"admin"},
    "funcionarios.configuracoes": {"admin"},
}


@app.context_processor
def injetar_permissoes():
    """Expõe o perfil atual e o helper pode(*perfis) para os templates."""
    perfil = session.get("funcionario_perfil")
    return {
        "perfil_atual": perfil,
        "pode": lambda *perfis: perfil in perfis,
    }


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

    # Tudo o que não é público exige autenticação.
    if "funcionario_id" not in session:
        return redirect("/login")

    # RBAC por endpoint: quem não tem o papel exigido é barrado.
    permitido = PERMISSOES.get(request.endpoint)
    if permitido is not None and session.get("funcionario_perfil") not in permitido:
        flash("Você não tem permissão para acessar esta área.", "erro")
        return redirect("/")

    return None


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=5001)
