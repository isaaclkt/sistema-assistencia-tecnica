from flask import Blueprint, render_template
from database import conectar

home_bp = Blueprint("home", __name__)


STATUS_EM_ABERTO = ("Aberto", "Em andamento")


def _porcentagem(valor, maximo):
    """Largura proporcional (0-100%) para os gráficos de barra em CSS."""
    if not maximo:
        return 0
    return round((valor / maximo) * 100)


@home_bp.route("/")
def home():
    db = conectar()

    total_clientes = db.execute(
        "SELECT COUNT(*) AS total FROM clientes"
    ).fetchone()["total"]

    total_pecas = db.execute(
        "SELECT COUNT(*) AS total FROM pecas"
    ).fetchone()["total"]

    total_orcamentos = db.execute(
        "SELECT COUNT(*) AS total FROM orcamentos"
    ).fetchone()["total"]

    ordens_abertas = db.execute(
        "SELECT COUNT(*) AS total FROM ordens_servico WHERE status IN (?, ?)",
        STATUS_EM_ABERTO,
    ).fetchone()["total"]

    ordens_finalizadas = db.execute(
        "SELECT COUNT(*) AS total FROM ordens_servico WHERE status = 'Finalizado'"
    ).fetchone()["total"]

    estoque_baixo = db.execute(
        "SELECT COUNT(*) AS total FROM pecas WHERE quantidade <= estoque_minimo"
    ).fetchone()["total"]

    orcamentos_pendentes = db.execute(
        "SELECT COUNT(*) AS total FROM orcamentos WHERE status = 'Pendente'"
    ).fetchone()["total"]

    indicadores = {
        "clientes": total_clientes,
        "ordens_abertas": ordens_abertas,
        "ordens_finalizadas": ordens_finalizadas,
        "orcamentos": total_orcamentos,
        "orcamentos_pendentes": orcamentos_pendentes,
        "pecas": total_pecas,
        "estoque_baixo": estoque_baixo,
    }

    linhas_status = db.execute("""
        SELECT status, COUNT(*) AS total
        FROM ordens_servico
        GROUP BY status
        ORDER BY total DESC
    """).fetchall()

    max_status = max((linha["total"] for linha in linhas_status), default=0)
    ordens_por_status = [
        {
            "rotulo": linha["status"],
            "total": linha["total"],
            "porcentagem": _porcentagem(linha["total"], max_status),
        }
        for linha in linhas_status
    ]

    linhas_mov = db.execute("""
        SELECT
            substr(data_movimentacao, 1, 10) AS dia,
            SUM(CASE WHEN tipo = 'Entrada' THEN quantidade ELSE 0 END) AS entradas,
            SUM(CASE WHEN tipo = 'Saida'   THEN quantidade ELSE 0 END) AS saidas
        FROM movimentacoes_estoque
        WHERE date(data_movimentacao) >= date('now', '-13 days')
        GROUP BY dia
        ORDER BY dia
    """).fetchall()

    max_mov = max(
        (max(linha["entradas"], linha["saidas"]) for linha in linhas_mov),
        default=0,
    )
    movimentacoes_periodo = [
        {
            "dia": linha["dia"][8:10] + "/" + linha["dia"][5:7],
            "entradas": linha["entradas"],
            "saidas": linha["saidas"],
            "pct_entradas": _porcentagem(linha["entradas"], max_mov),
            "pct_saidas": _porcentagem(linha["saidas"], max_mov),
        }
        for linha in linhas_mov
    ]

    linhas_top = db.execute("""
        SELECT p.nome AS nome, SUM(m.quantidade) AS total
        FROM movimentacoes_estoque m
        JOIN pecas p ON p.id = m.peca_id
        GROUP BY m.peca_id
        ORDER BY total DESC
        LIMIT 5
    """).fetchall()

    max_top = max((linha["total"] for linha in linhas_top), default=0)
    top_pecas = [
        {
            "nome": linha["nome"],
            "total": linha["total"],
            "porcentagem": _porcentagem(linha["total"], max_top),
        }
        for linha in linhas_top
    ]

    ultimas_ordens = db.execute("""
        SELECT
            o.ordem_id,
            o.equipamento,
            o.status,
            c.nome AS cliente_nome
        FROM ordens_servico o
        JOIN clientes c ON c.id = o.cliente_id
        ORDER BY o.ordem_id DESC
        LIMIT 5
    """).fetchall()

    ultimas_movimentacoes = db.execute("""
        SELECT
            m.tipo,
            m.quantidade,
            m.data_movimentacao,
            p.nome AS nome_peca
        FROM movimentacoes_estoque m
        JOIN pecas p ON p.id = m.peca_id
        ORDER BY m.data_movimentacao DESC
        LIMIT 5
    """).fetchall()

    db.close()

    return render_template(
        "home.html",
        indicadores=indicadores,
        ordens_por_status=ordens_por_status,
        movimentacoes_periodo=movimentacoes_periodo,
        top_pecas=top_pecas,
        ultimas_ordens=ultimas_ordens,
        ultimas_movimentacoes=ultimas_movimentacoes,
    )
