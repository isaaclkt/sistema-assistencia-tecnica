import sqlite3
from datetime import datetime


def _coluna_existe(conexao, tabela, coluna):
    colunas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
    return any(item["name"] == coluna for item in colunas)


def registrar_movimentacao(conexao, peca_id, tipo, quantidade, observacao=""):
    conexao.execute(
        """
        INSERT INTO movimentacoes_estoque
            (peca_id, tipo, quantidade, data_movimentacao, observacao)
        VALUES (?, ?, ?, ?, ?)
        """,
        (peca_id, tipo, quantidade,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), observacao),
    )


class EstoqueInsuficiente(Exception):
    def __init__(self, nome, disponivel, solicitado):
        super().__init__(
            f'Estoque insuficiente para "{nome}": '
            f"disponível {disponivel}, necessário {solicitado}."
        )


def consumir_estoque(conexao, ordem_id):
    itens = conexao.execute("""
        SELECT op.peca_id, op.quantidade, p.nome AS nome, p.quantidade AS saldo
        FROM ordem_pecas op
        JOIN pecas p ON p.id = op.peca_id
        WHERE op.ordem_id = ?
    """, (ordem_id,)).fetchall()

    for item in itens:
        if item["saldo"] < item["quantidade"]:
            raise EstoqueInsuficiente(item["nome"], item["saldo"], item["quantidade"])

    for item in itens:
        conexao.execute(
            "UPDATE pecas SET quantidade = quantidade - ? WHERE id = ?",
            (item["quantidade"], item["peca_id"]),
        )
        registrar_movimentacao(
            conexao, item["peca_id"], "Saida", item["quantidade"],
            f"Uso na ordem de serviço #{ordem_id} (orçamento aprovado)",
        )


def estornar_estoque(conexao, ordem_id):
    itens = conexao.execute(
        "SELECT peca_id, quantidade FROM ordem_pecas WHERE ordem_id = ?",
        (ordem_id,),
    ).fetchall()

    for item in itens:
        conexao.execute(
            "UPDATE pecas SET quantidade = quantidade + ? WHERE id = ?",
            (item["quantidade"], item["peca_id"]),
        )
        registrar_movimentacao(
            conexao, item["peca_id"], "Entrada", item["quantidade"],
            f"Estorno da ordem de serviço #{ordem_id}",
        )


def _garantir_schema(conexao):
    if not _coluna_existe(conexao, "ordens_servico", "funcionario_id"):
        conexao.execute(
            "ALTER TABLE ordens_servico ADD COLUMN funcionario_id INTEGER REFERENCES funcionarios(id)"
        )

    if not _coluna_existe(conexao, "ordens_servico", "data_abertura"):
        conexao.execute("ALTER TABLE ordens_servico ADD COLUMN data_abertura TEXT")

    if not _coluna_existe(conexao, "ordens_servico", "data_finalizacao"):
        conexao.execute("ALTER TABLE ordens_servico ADD COLUMN data_finalizacao TEXT")

    colunas_orcamento = {
        "peca_id": "ALTER TABLE orcamentos ADD COLUMN peca_id INTEGER",
        "problema_analisado": "ALTER TABLE orcamentos ADD COLUMN problema_analisado TEXT NOT NULL DEFAULT ''",
        "valor_peca": "ALTER TABLE orcamentos ADD COLUMN valor_peca REAL NOT NULL DEFAULT 0",
        "valor_mao_obra": "ALTER TABLE orcamentos ADD COLUMN valor_mao_obra REAL NOT NULL DEFAULT 0",
        "valor_total": "ALTER TABLE orcamentos ADD COLUMN valor_total REAL NOT NULL DEFAULT 0",
    }

    for coluna, comando in colunas_orcamento.items():
        if not _coluna_existe(conexao, "orcamentos", coluna):
            conexao.execute(comando)

    novas_colunas = {
        ("clientes", "data_cadastro"):
            "ALTER TABLE clientes ADD COLUMN data_cadastro TEXT",
        ("pecas", "data_cadastro"):
            "ALTER TABLE pecas ADD COLUMN data_cadastro TEXT",
        ("funcionarios", "ativo"):
            "ALTER TABLE funcionarios ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1",
        ("orcamentos", "status"):
            "ALTER TABLE orcamentos ADD COLUMN status TEXT NOT NULL DEFAULT 'Pendente'",
        ("orcamentos", "validade"):
            "ALTER TABLE orcamentos ADD COLUMN validade TEXT",
        ("orcamentos", "desconto"):
            "ALTER TABLE orcamentos ADD COLUMN desconto REAL NOT NULL DEFAULT 0",
        ("orcamentos", "data_cadastro"):
            "ALTER TABLE orcamentos ADD COLUMN data_cadastro TEXT",
        ("ordens_servico", "laudo"):
            "ALTER TABLE ordens_servico ADD COLUMN laudo TEXT",
        ("ordens_servico", "garantia"):
            "ALTER TABLE ordens_servico ADD COLUMN garantia TEXT",
        ("ordens_servico", "prazo_entrega"):
            "ALTER TABLE ordens_servico ADD COLUMN prazo_entrega TEXT",
    }
    for (tabela, coluna), comando in novas_colunas.items():
        if not _coluna_existe(conexao, tabela, coluna):
            conexao.execute(comando)

    if not _coluna_existe(conexao, "funcionarios", "perfil"):
        conexao.execute(
            "ALTER TABLE funcionarios ADD COLUMN perfil TEXT NOT NULL DEFAULT 'atendente'"
        )
        conexao.execute("UPDATE funcionarios SET perfil = 'admin'")

    conexao.execute("""
        UPDATE funcionarios
        SET perfil = 'atendente'
        WHERE perfil NOT IN ('admin', 'atendente', 'tecnico')
    """)

    conexao.execute("""
        UPDATE orcamentos
        SET valor_total = valor_orcamento
        WHERE valor_total = 0
          AND valor_orcamento IS NOT NULL
    """)
    conexao.execute("""
        UPDATE orcamentos
        SET desconto = CASE
                WHEN desconto < 0 THEN 0
                WHEN desconto > (valor_peca + valor_mao_obra) THEN (valor_peca + valor_mao_obra)
                ELSE desconto
            END,
            valor_orcamento = (valor_peca + valor_mao_obra),
            valor_total = MAX(
                (valor_peca + valor_mao_obra) -
                CASE
                    WHEN desconto < 0 THEN 0
                    WHEN desconto > (valor_peca + valor_mao_obra) THEN (valor_peca + valor_mao_obra)
                    ELSE desconto
                END,
                0
            )
        WHERE valor_peca > 0
           OR valor_mao_obra > 0
           OR desconto != 0
    """)
    conexao.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_orcamentos_ordem_id
        ON orcamentos (ordem_id)
    """)

    conexao.execute("DROP TABLE IF EXISTS usuarios")

    conexao.execute(
        "CREATE TABLE IF NOT EXISTS config_sistema (chave TEXT PRIMARY KEY, valor TEXT)"
    )
    ja_reconciliado = conexao.execute(
        "SELECT 1 FROM config_sistema WHERE chave = 'reconciliacao_estoque_os'"
    ).fetchone()
    if ja_reconciliado is None:
        itens = conexao.execute(
            "SELECT peca_id, SUM(quantidade) AS total FROM ordem_pecas GROUP BY peca_id"
        ).fetchall()
        for item in itens:
            peca = conexao.execute(
                "SELECT quantidade FROM pecas WHERE id = ?", (item["peca_id"],)
            ).fetchone()
            if peca is None:
                continue
            baixa = min(peca["quantidade"], item["total"])
            if baixa > 0:
                conexao.execute(
                    "UPDATE pecas SET quantidade = quantidade - ? WHERE id = ?",
                    (baixa, item["peca_id"]),
                )
                registrar_movimentacao(
                    conexao, item["peca_id"], "Saida", baixa,
                    "Baixa retroativa: peças vinculadas a ordens de serviço",
                )
        conexao.execute(
            "INSERT OR REPLACE INTO config_sistema (chave, valor) VALUES ('reconciliacao_estoque_os', '1')"
        )

    conexao.commit()


def conectar():
    conexao = sqlite3.connect("database/sistema.db")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    _garantir_schema(conexao)
    return conexao
