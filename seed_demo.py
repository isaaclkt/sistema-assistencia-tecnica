"""
Popula o banco com dados fictícios realistas para demonstração do sistema.

Uso:  python seed_demo.py

- Remove todos os dados de clientes, peças, OS, orçamentos e movimentações.
- Preserva o usuário administrador de demonstração (admin@sistema.com).
- Repopula com dados consistentes (sem registros órfãos).
"""

from datetime import datetime, timedelta

from database import conectar
from routes.funcionarios import criar_tabela_funcionarios

ADMIN_EMAIL = "admin@sistema.com"
AGORA = datetime.now()


def dia(n, hora=9, minuto=30):
    return (AGORA - timedelta(days=n)).replace(hour=hora, minute=minuto, second=0, microsecond=0)


def f_dt(dt):
    return dt.strftime("%d/%m/%Y %H:%M")


def f_mov(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def f_data(dt):
    return dt.strftime("%Y-%m-%d")


def seed():
    criar_tabela_funcionarios()  # garante o admin
    db = conectar()

    admin = db.execute(
        "SELECT id FROM funcionarios WHERE email = ?", (ADMIN_EMAIL,)
    ).fetchone()
    admin_id = admin["id"]

    # ---- Limpeza (ordem segura para as FKs) ----
    for tabela in ["movimentacoes_estoque", "ordem_pecas", "orcamentos",
                   "ordens_servico", "equipamentos", "pecas", "clientes"]:
        db.execute(f"DELETE FROM {tabela}")
    db.execute("DELETE FROM funcionarios WHERE email != ?", (ADMIN_EMAIL,))
    db.execute(
        "DELETE FROM sqlite_sequence WHERE name IN "
        "('movimentacoes_estoque','ordem_pecas','orcamentos','ordens_servico','equipamentos','pecas','clientes')"
    )

    def mov(peca_id, tipo, qtd, dt, obs):
        db.execute(
            "INSERT INTO movimentacoes_estoque (peca_id, tipo, quantidade, data_movimentacao, observacao) "
            "VALUES (?, ?, ?, ?, ?)",
            (peca_id, tipo, qtd, f_mov(dt), obs),
        )

    # ---- Clientes ----
    clientes = [
        ("Mariana Oliveira Costa", "047.812.339-21", "(41) 99812-4471", "mariana.costa@gmail.com", "Rua das Acácias, 320 - Curitiba/PR"),
        ("Tech Solutions Informática Ltda", "12.345.678/0001-90", "(41) 3322-1180", "contato@techsolutions.com.br", "Av. Sete de Setembro, 2450 - Curitiba/PR"),
        ("Rafael Mendes Pereira", "052.443.118-07", "(41) 99645-2210", "rafael.mendes@outlook.com", "Rua XV de Novembro, 88 - São José dos Pinhais/PR"),
        ("Advocacia Lima & Souza", "18.902.331/0001-45", "(41) 3045-7788", "adm@limaesouza.adv.br", "Rua Marechal Deodoro, 1010, sala 502 - Curitiba/PR"),
        ("Camila Fernandes Rocha", "089.221.764-55", "(41) 99923-7765", "camila.rocha@gmail.com", "Rua Brigadeiro Franco, 455 - Curitiba/PR"),
        ("Loja Estilo Calçados", "27.554.910/0001-12", "(41) 3278-9090", "vendas@estilocalcados.com.br", "Av. Rui Barbosa, 600 - Pinhais/PR"),
        ("João Pedro Almeida", "061.770.452-38", "(41) 99711-3322", "joao.almeida@hotmail.com", "Rua Itupava, 1234 - Curitiba/PR"),
        ("Padaria Pão Quente", "33.118.207/0001-67", "(41) 3019-4545", "contato@paoquente.com.br", "Rua Augusto Stresser, 77 - Curitiba/PR"),
        ("Beatriz Santos Lima", "075.339.881-04", "(41) 99588-1199", "beatriz.lima@gmail.com", "Rua Chile, 210 - Araucária/PR"),
        ("Clínica Odontológica Sorriso", "41.220.665/0001-29", "(41) 3344-2211", "recepcao@clinicasorriso.com.br", "Av. Iguaçu, 2890 - Curitiba/PR"),
        ("Lucas Gabriel Martins", "098.114.523-76", "(41) 99477-6655", "lucas.martins@gmail.com", "Rua Nilo Peçanha, 145 - Colombo/PR"),
        ("Mercado Bom Preço", "55.301.448/0001-83", "(41) 3266-8080", "gerencia@bompreco.com.br", "Rua Trajano Reis, 500 - Curitiba/PR"),
    ]
    cliente_id = []
    for i, (nome, cpf, tel, email, end) in enumerate(clientes):
        cur = db.execute(
            "INSERT INTO clientes (nome, cpf, telefone, email, endereco, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, cpf, tel, email, end, f_dt(dia(45 - i * 2))),
        )
        cliente_id.append(cur.lastrowid)

    # ---- Peças (nome, descrição, est_min, preço, fornecedor, entrada inicial) ----
    pecas = [
        ("Tela iPhone 11", "Display OLED compatível", 3, 480.00, "Apple Parts BR", 10),
        ("Bateria Samsung Galaxy S20", "Bateria 4000mAh", 5, 180.00, "Samsung Supply", 12),
        ("Conector de carga USB-C", "Flex de carga tipo C", 10, 35.00, "MobileParts", 40),
        ("SSD 480GB Kingston", "Unidade SATA 2.5\"", 4, 280.00, "Kingston Dist.", 8),
        ("Memória RAM DDR4 8GB", "2666MHz notebook", 6, 220.00, "TechMemory", 15),
        ("Fonte para notebook 65W", "Carregador universal", 5, 130.00, "PowerTech", 9),
        ("Cooler para notebook", "Ventoinha interna", 8, 75.00, "CoolParts", 20),
        ("Cabo Flat de tela", "Cabo LVDS notebook", 10, 60.00, "NoteParts", 25),
        ("Teclado notebook ABNT2", "Teclado padrão", 4, 150.00, "NoteParts", 7),
        ("Tela iPhone 12", "Display OLED", 3, 620.00, "Apple Parts BR", 4),
        ("Bateria iPhone 11", "Bateria 3110mAh", 5, 160.00, "Apple Parts BR", 11),
        ("Pasta térmica", "Seringa 4g", 15, 25.00, "TechSupply", 50),
        ("HD 1TB Seagate", "Disco 7200rpm", 4, 250.00, "Seagate Dist.", 5),
        ("Película de vidro", "Protetor 9H", 20, 15.00, "MobileParts", 60),
        ("Placa de carga Samsung A30", "Sub placa USB", 6, 90.00, "Samsung Supply", 6),
        ("Fonte ATX 500W", "Fonte para desktop", 3, 290.00, "PowerTech", 4),
        ("SSD M.2 NVMe 1TB", "NVMe Gen3", 3, 520.00, "Kingston Dist.", 4),
        ("Teclado mecânico USB", "Periférico gamer", 5, 240.00, "PerifericosBR", 4),
    ]
    peca_id = {}
    peca_preco = {}
    for i, (nome, desc, mn, preco, forn, entrada) in enumerate(pecas):
        cur = db.execute(
            "INSERT INTO pecas (nome, descricao, quantidade, estoque_minimo, preco_unitario, fornecedor, data_cadastro) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nome, desc, entrada, mn, preco, forn, f_dt(dia(40 - i))),
        )
        pid = cur.lastrowid
        peca_id[nome] = pid
        peca_preco[nome] = preco
        mov(pid, "Entrada", entrada, dia((i % 12) + 2, hora=8), "Entrada por compra")

    # ---- Ordens de serviço ----
    ordens = [
        dict(cli=0, equip="iPhone 11", prob="Tela trincada após queda", status="Finalizado",
             laudo="Substituição do display OLED. Aparelho testado e aprovado.", gar="90 dias",
             ab=12, fim=8, pecas=[("Tela iPhone 11", 1)], orc=("Aprovado", 120, 0)),
        dict(cli=1, equip="Notebook Dell Inspiron", prob="Não liga, sem carga", status="Finalizado",
             laudo="Troca da fonte de alimentação. Carregamento normalizado.", gar="90 dias",
             ab=18, fim=14, pecas=[("Fonte para notebook 65W", 1)], orc=("Aprovado", 90, 10)),
        dict(cli=2, equip="Samsung Galaxy S20", prob="Bateria viciada, descarrega rápido", status="Em andamento",
             laudo="Troca de bateria em andamento.", gar="90 dias",
             ab=9, fim=None, pecas=[("Bateria Samsung Galaxy S20", 1)], orc=("Aprovado", 80, 0)),
        dict(cli=3, equip="Notebook Lenovo ThinkPad", prob="Lentidão; solicitou formatação", status="Finalizado",
             laudo="Formatação, instalação do sistema e limpeza interna realizadas.", gar="30 dias",
             ab=25, fim=22, pecas=[], orc=None),
        dict(cli=4, equip="Desktop Montado", prob="Upgrade para SSD", status="Em andamento",
             laudo="Instalação do SSD e clonagem do sistema.", gar="90 dias",
             ab=6, fim=None, pecas=[("SSD 480GB Kingston", 1)], orc=("Pendente", 100, 0)),
        dict(cli=5, equip="iPhone 12", prob="Tela quebrada", status="Aberto",
             laudo="", gar="", ab=3, fim=None, pecas=[("Tela iPhone 12", 1)], orc=("Pendente", 150, 0)),
        dict(cli=6, equip="Notebook Acer Aspire", prob="Superaquecimento e desligamentos", status="Finalizado",
             laudo="Limpeza interna e troca da pasta térmica. Temperatura normalizada.", gar="90 dias",
             ab=14, fim=10, pecas=[("Pasta térmica", 1), ("Cooler para notebook", 1)], orc=None),
        dict(cli=7, equip="PC Gamer", prob="Fonte queimada", status="Em andamento",
             laudo="Substituição da fonte ATX.", gar="90 dias",
             ab=8, fim=None, pecas=[("Fonte ATX 500W", 1)], orc=("Aprovado", 100, 20)),
        dict(cli=8, equip="Notebook HP Pavilion", prob="Pouca memória; upgrade", status="Aberto",
             laudo="", gar="", ab=2, fim=None, pecas=[("Memória RAM DDR4 8GB", 2)], orc=None),
        dict(cli=9, equip="iPhone 11", prob="Bateria não segura carga", status="Finalizado",
             laudo="Troca de bateria. Saúde da bateria restaurada para 100%.", gar="90 dias",
             ab=20, fim=17, pecas=[("Bateria iPhone 11", 1)], orc=None),
        dict(cli=10, equip="Notebook Samsung Book", prob="Teclas não funcionam", status="Aberto",
             laudo="", gar="", ab=5, fim=None, pecas=[("Teclado notebook ABNT2", 1)], orc=None),
        dict(cli=11, equip="Desktop Escritório", prob="HD com defeito, barulho", status="Cancelado",
             laudo="Cliente optou por não realizar o reparo.", gar="",
             ab=16, fim=None, pecas=[("HD 1TB Seagate", 1)], consome=False, orc=("Recusado", 80, 0)),
        dict(cli=1, equip="MacBook Air", prob="Não carrega; conector danificado", status="Em andamento",
             laudo="Troca do conector de carga em andamento.", gar="90 dias",
             ab=7, fim=None, pecas=[("Conector de carga USB-C", 1)], orc=None),
        dict(cli=4, equip="Notebook Dell Vostro", prob="Imagem com falhas; cabo flat", status="Aberto",
             laudo="", gar="", ab=1, fim=None, pecas=[("Cabo Flat de tela", 1)], orc=None),
        dict(cli=2, equip="PC Workstation", prob="Upgrade de armazenamento NVMe", status="Cancelado",
             laudo="Orçamento não aprovado pelo cliente.", gar="",
             ab=11, fim=None, pecas=[("SSD M.2 NVMe 1TB", 1)], consome=False, orc=("Recusado", 120, 0)),
    ]

    orcamentos_para_criar = []
    for o in ordens:
        abertura = dia(o["ab"])
        data_final = f_dt(dia(o["fim"])) if o["status"] == "Finalizado" and o["fim"] else None
        prazo = f_data(abertura + timedelta(days=5))
        cur = db.execute(
            "INSERT INTO ordens_servico "
            "(cliente_id, funcionario_id, equipamento, problema_relatado, status, "
            " data_abertura, data_finalizacao, laudo, garantia, prazo_entrega) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cliente_id[o["cli"]], admin_id, o["equip"], o["prob"], o["status"],
             f_dt(abertura), data_final, o["laudo"], o["gar"], prazo),
        )
        oid = cur.lastrowid
        consome = o.get("consome", True)
        valor_peca = 0.0
        primeiro_peca_id = None
        for (pnome, qtd) in o["pecas"]:
            pid = peca_id[pnome]
            preco = peca_preco[pnome]
            valor_peca += preco * qtd
            if primeiro_peca_id is None:
                primeiro_peca_id = pid
            db.execute(
                "INSERT INTO ordem_pecas (ordem_id, peca_id, quantidade, valor_unitario) VALUES (?, ?, ?, ?)",
                (oid, pid, qtd, preco),
            )
            if consome:
                db.execute("UPDATE pecas SET quantidade = quantidade - ? WHERE id = ?", (qtd, pid))
                mov(pid, "Saida", qtd, abertura + timedelta(hours=2), f"Uso na ordem de serviço #{oid}")

        if o["orc"]:
            status_orc, mao, desc = o["orc"]
            orcamentos_para_criar.append(
                dict(oid=oid, cliente_id=cliente_id[o["cli"]], peca_id=primeiro_peca_id,
                     equip=o["equip"], prob=o["prob"], valor_peca=valor_peca,
                     mao=mao, desc=desc, status=status_orc, ab=o["ab"])
            )

    # ---- Orçamentos ----
    for oc in orcamentos_para_criar:
        total = max(oc["valor_peca"] + oc["mao"] - oc["desc"], 0)
        cadastro = dia(max(oc["ab"] - 1, 0))
        validade = f_data(cadastro + timedelta(days=20))
        analise = f"Análise técnica: {oc['prob']}. Serviço e peças orçados."
        db.execute(
            "INSERT INTO orcamentos "
            "(ordem_id, cliente_id, peca_id, equipamento, problema_analisado, "
            " valor_orcamento, valor_peca, valor_mao_obra, desconto, valor_total, status, validade, data_cadastro) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (oc["oid"], oc["cliente_id"], oc["peca_id"], oc["equip"], analise,
             total, oc["valor_peca"], oc["mao"], oc["desc"], total, oc["status"], validade, f_dt(cadastro)),
        )

    db.commit()

    # ---- Resumo ----
    def conta(sql):
        return db.execute(sql).fetchone()[0]

    print("Clientes:", conta("SELECT COUNT(*) FROM clientes"))
    print("Peças:", conta("SELECT COUNT(*) FROM pecas"))
    print("Estoque baixo:", conta("SELECT COUNT(*) FROM pecas WHERE quantidade <= estoque_minimo"))
    print("Ordens de serviço:", conta("SELECT COUNT(*) FROM ordens_servico"))
    print("Orçamentos:", conta("SELECT COUNT(*) FROM orcamentos"))
    print("Movimentações:", conta("SELECT COUNT(*) FROM movimentacoes_estoque"))
    print("Funcionários:", conta("SELECT COUNT(*) FROM funcionarios"))
    db.close()
    print("Base de demonstração criada com sucesso.")


if __name__ == "__main__":
    seed()
