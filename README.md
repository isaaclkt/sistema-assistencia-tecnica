# Sistema de Assistência Técnica

Aplicação web para gestão de uma assistência técnica, desenvolvida em **Python/Flask** com **SQLite**. O sistema centraliza o atendimento de uma empresa de reparos — do cadastro do cliente à ordem de serviço, ao orçamento e ao controle de estoque de peças — com painel de indicadores, geração de documentos em PDF e exportação em Excel.

Projeto acadêmico desenvolvido na **PUCPR**.

---

## 📋 Descrição

O objetivo é substituir controles manuais (papel/planilhas) por uma solução informatizada, oferecendo:

- Registro e acompanhamento de **ordens de serviço**;
- **Orçamentos** integrados às ordens, com aprovação comercial;
- **Controle de estoque** de peças com movimentações, histórico e alertas;
- **Cadastro de clientes** e **gestão de funcionários** com níveis de acesso;
- **Dashboard** gerencial e **relatórios** prontos para impressão/exportação.

---

## 🛠 Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Linguagem | **Python 3** |
| Framework web | **Flask 3** |
| Templates | **Jinja2** |
| Banco de dados | **SQLite** |
| Segurança de senha | **Werkzeug** (hash de senha) |
| Relatórios PDF | **ReportLab** |
| Exportação Excel | **OpenPyXL** |
| Frontend | **HTML5**, **CSS3** (design system próprio), **JavaScript** (interações pontuais) |
| Versionamento | **Git** / **GitHub** |

---

## ✨ Funcionalidades

### 🔐 Login e Funcionários
- Login por e-mail e senha (senha armazenada com **hash**).
- Controle de **sessão** e proteção de rotas internas.
- **Perfis de acesso** (admin / técnico / atendente / funcionário) — área de gestão de funcionários restrita a **administradores** (RBAC).
- **CRUD de funcionários**: cadastrar, editar, ativar/desativar e redefinir senha.
- Bloqueio de login para contas **desativadas**.
- **Usuário de demonstração** criado automaticamente.

### 👥 Clientes
- Cadastro, edição, exclusão e consulta.
- **Busca** e **paginação**.
- **Validação** de CPF (11 dígitos) e e-mail no servidor.
- Registro de data de cadastro.

### 🛠️ Ordens de Serviço
- Cadastro, edição e exclusão.
- Vínculo a **cliente**, **funcionário responsável** e **múltiplas peças**.
- Status: *Aberto*, *Em andamento*, *Finalizado*, *Cancelado*.
- Campos de **laudo técnico**, **garantia** e **prazo de entrega**.
- Datas reais de **abertura** e **finalização**.
- Tela de **visualização** da OS e **geração de PDF** profissional em **duas vias** (empresa + cliente; assinatura apenas na via da empresa).
- **Integração com o estoque**: ao usar uma peça, o estoque é **baixado automaticamente** (com **estorno** ao editar/excluir).

### 📦 Estoque / Peças
- Cadastro, edição e exclusão de peças.
- **Movimentações** de entrada e saída + **histórico**.
- **Controle de estoque mínimo** com destaque visual e **notificação** (sino na barra superior).
- **Busca**, **ordenação por coluna** e **paginação**.
- **Relatório PDF** (resumo executivo, tabela de peças, histórico, paginação) e **Exportação Excel (.xlsx)** com duas abas, filtros e formatação.
- Exportações **respeitam o filtro de busca** atual.

### 📄 Orçamentos *(módulo integrador)*
- Criação a partir de uma ordem de serviço (liga **Cliente ↔ OS ↔ Estoque**).
- **Status comercial**: Pendente, Aprovado, Recusado.
- **Validade**, **desconto** e cálculo de **valor total**.
- Aprovar/recusar reflete no status da OS.

### 📊 Dashboard
- Indicadores (KPIs) com contexto: clientes, ordens em aberto/finalizadas, orçamentos, peças e itens com estoque baixo.
- **Alertas** operacionais (estoque baixo / ordens em aberto).
- **Gráficos** (em HTML/CSS): ordens por status, movimentações dos últimos 14 dias e peças mais movimentadas.
- **Atividade recente** e acesso rápido aos módulos.

### 🔎 Acompanhamento (consulta pública)
- Página pública para o cliente consultar o andamento da OS por nome ou número.
- Geração de **link de acompanhamento** e botão **"Falar com a Assistência"** via WhatsApp.

---

## 📁 Estrutura de Pastas

```
sistema-de-assistencia-tecnica/
│
├── app.py                  # Aplicação Flask: filtros, contexto, proteção de rotas, blueprints
├── database.py             # Conexão SQLite + migrações idempotentes (schema)
├── init_db.py              # Cria o banco a partir de database/schema.sql
├── seed_demo.py            # Popula dados fictícios realistas para demonstração
├── requirements.txt
├── README.md
│
├── database/
│   ├── schema.sql          # Definição das tabelas
│   └── sistema.db          # Banco SQLite (gerado)
│
├── routes/                 # Blueprints por módulo
│   ├── home.py             # Dashboard
│   ├── funcionarios.py     # Login, sessão, perfis e CRUD de funcionários
│   ├── cadastro.py         # Clientes
│   ├── ordem_servico.py    # Ordens de serviço + PDF
│   ├── estoque.py          # Estoque, movimentações, relatórios PDF/Excel
│   ├── orcamento.py        # Orçamentos (integrador)
│   └── acompanhamento.py   # Consulta pública da OS
│
├── templates/              # Páginas Jinja2 (base.html, partials/, telas dos módulos)
│   └── partials/           # _sidebar, _navbar, _flash, _icons
│
└── static/
    └── css/                # Design system (global.css, layout.css) + CSS por tela
```

---

## ⚙️ Instalação

### 1. Clonar o projeto
```bash
git clone <url-do-repositorio>
cd sistema-de-assistencia-tecnica
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Preparar o banco de dados (opcional)
O repositório já inclui um banco em `database/sistema.db`. Para recriar do zero e/ou popular dados de demonstração:
```bash
python init_db.py     # cria o banco a partir do schema (se necessário)
python seed_demo.py   # popula clientes, OS, peças, orçamentos e movimentações fictícias
```
> As migrações de colunas são aplicadas automaticamente ao iniciar a aplicação.

### 5. Executar a aplicação
```bash
python app.py
```
Acesse: **http://localhost:5001**

> Variáveis de ambiente opcionais: `SECRET_KEY` (chave de sessão em produção) e `FLASK_DEBUG=0` (desliga o modo debug).

---

## 🗄️ Banco de Dados

- **SGBD:** SQLite (arquivo único `database/sistema.db`).
- **Definição:** `database/schema.sql`.
- **Principais tabelas:** `funcionarios`, `clientes`, `pecas`, `movimentacoes_estoque`, `ordens_servico`, `ordem_pecas`, `orcamentos`, `equipamentos`, `config_sistema`.
- **Integridade:** chaves estrangeiras habilitadas (`PRAGMA foreign_keys = ON`); migrações idempotentes em `database.py` garantem o esquema atualizado a cada execução.

---

## 👤 Usuário de Demonstração

O sistema cria automaticamente um administrador para apresentação (também exibido na tela de login):

```
E-mail: admin@sistema.com
Senha:  admin123
```

Perfil **administrador** — acesso total a todos os módulos.

---

## 🧾 Relatórios

- **PDF (ReportLab):**
  - **Ordem de Serviço** — documento em duas vias (empresa e cliente).
  - **Relatório de Estoque** — cabeçalho institucional, resumo executivo, tabela de peças com status, histórico de movimentações, paginação e rodapé.
- **Excel (OpenPyXL):**
  - Arquivo `estoque.xlsx` com abas **Estoque** e **Movimentações**, cabeçalhos formatados, filtros automáticos, congelamento de cabeçalho, formato monetário e destaque para estoque baixo.
- Ambos os relatórios de estoque respeitam o **filtro de busca** aplicado na tela.

---

## 📈 Dashboard

Tela inicial com consolidação dos módulos:
- **Indicadores:** total de clientes, ordens em aberto e finalizadas, orçamentos, peças cadastradas e itens com estoque baixo.
- **Gráficos:** ordens por status, movimentações dos últimos 14 dias (entradas/saídas) e top peças mais movimentadas.
- **Alertas** de estoque baixo e ordens em aberto + **atividade recente**.

---

## 🖼️ Capturas de Tela

> Seção reservada para imagens do sistema. Adicione os prints em `docs/` e referencie aqui, por exemplo:
>
> `![Dashboard](docs/dashboard.png)`

---

## 👨‍💻 Equipe

Projeto desenvolvido em equipe — PUCPR:

- André Fochesatto
- Arthur Diniz Azevedo
- Isaac (isaaclkt)
- Lucas Buzzi Lima

---

## 📄 Licença

Projeto de uso **acadêmico**, desenvolvido para fins educacionais na PUCPR.
Sinta-se à vontade para estudar e adaptar o código para fins não comerciais.
