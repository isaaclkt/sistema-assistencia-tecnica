CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'funcionario',
    ativo INTEGER DEFAULT 1
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    telefone TEXT,
    email TEXT,
    endereco TEXT
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    equipamento_id INTEGER NOT NULL,
    usuario_id INTEGER,
    defeito_relatado TEXT NOT NULL,
    diagnostico TEXT,
    status TEXT NOT NULL DEFAULT 'Aberta',
    valor_servico REAL DEFAULT 0,
    data_abertura TEXT NOT NULL,
    data_finalizacao TEXT,

    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE pecas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 1,
    preco_unitario REAL DEFAULT 0,
    fornecedor TEXT
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

    FOREIGN KEY (ordem_id) REFERENCES ordens_servico(id),
    FOREIGN KEY (peca_id) REFERENCES pecas(id)
);