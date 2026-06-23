CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    data_cadastro TEXT
);

CREATE TABLE equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    marca TEXT,
    modelo TEXT,
    numero_serie TEXT,
    descricao TEXT,

    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE ordens_servico (
    ordem_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    funcionario_id INTEGER,
    equipamento TEXT NOT NULL,
    problema_relatado TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Aberto',
    data_abertura TEXT,
    data_finalizacao TEXT,
    laudo TEXT,
    garantia TEXT,
    prazo_entrega TEXT,

    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
);

CREATE TABLE orcamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordem_id INTEGER NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL,
    peca_id INTEGER,
    equipamento TEXT NOT NULL,
    problema_analisado TEXT NOT NULL DEFAULT '',
    valor_orcamento REAL NOT NULL,
    valor_peca REAL NOT NULL DEFAULT 0,
    valor_mao_obra REAL NOT NULL DEFAULT 0,
    valor_total REAL NOT NULL DEFAULT 0,
    desconto REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Pendente',
    validade TEXT,
    data_cadastro TEXT,

    FOREIGN KEY (ordem_id) REFERENCES ordens_servico(ordem_id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (peca_id) REFERENCES pecas(id)
);

CREATE TABLE pecas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 1,
    preco_unitario REAL DEFAULT 0,
    fornecedor TEXT,
    data_cadastro TEXT
);

CREATE TABLE movimentacoes_estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peca_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    data_movimentacao TEXT NOT NULL,
    observacao TEXT,

    FOREIGN KEY (peca_id) REFERENCES pecas(id)
);

CREATE TABLE ordem_pecas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordem_id INTEGER NOT NULL,
    peca_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_unitario REAL DEFAULT 0,

    FOREIGN KEY (ordem_id) REFERENCES ordens_servico(ordem_id),
    FOREIGN KEY (peca_id) REFERENCES pecas(id)
);

CREATE TABLE funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    cargo TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    perfil TEXT NOT NULL DEFAULT 'atendente'
);
