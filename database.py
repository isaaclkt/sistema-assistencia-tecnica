import sqlite3


def _coluna_existe(conexao, tabela, coluna):
    colunas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
    return any(item["name"] == coluna for item in colunas)


def _garantir_schema(conexao):
    if not _coluna_existe(conexao, "ordens_servico", "funcionario_id"):
        conexao.execute(
            "ALTER TABLE ordens_servico ADD COLUMN funcionario_id INTEGER REFERENCES funcionarios(id)"
        )

    # Datas reais da OS (NULL para ordens antigas; preenchidas a partir de agora)
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

    conexao.execute("""
        UPDATE orcamentos
        SET valor_total = valor_orcamento
        WHERE valor_total = 0
          AND valor_orcamento IS NOT NULL
    """)
    conexao.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_orcamentos_ordem_id
        ON orcamentos (ordem_id)
    """)
    conexao.commit()


def conectar():
    conexao = sqlite3.connect("database/sistema.db")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    _garantir_schema(conexao)
    return conexao
