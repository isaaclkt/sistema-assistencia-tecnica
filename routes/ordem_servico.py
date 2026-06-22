from flask import Blueprint, flash, render_template, request, redirect
from database import conectar

ordem_servico_bp = Blueprint("ordem_servico", __name__)


def salvar_pecas_da_ordem(db, ordem_id, pecas_ids, quantidades):
    itens = {}

    for peca_id, quantidade_texto in zip(pecas_ids, quantidades):
        if not peca_id:
            continue

        quantidade = max(int(quantidade_texto or 1), 1)
        itens[peca_id] = itens.get(peca_id, 0) + quantidade

    for peca_id, quantidade in itens.items():
        peca = db.execute("""
            SELECT preco_unitario
            FROM pecas
            WHERE id = ?
        """, (peca_id,)).fetchone()

        if peca is not None:
            db.execute("""
                INSERT INTO ordem_pecas
                (ordem_id, peca_id, quantidade, valor_unitario)
                VALUES (?, ?, ?, ?)
            """, (
                ordem_id,
                peca_id,
                quantidade,
                peca["preco_unitario"]
            ))


def atualizar_valores_orcamento(db, ordem_id):
    resumo = db.execute("""
        SELECT
            MIN(peca_id) AS peca_id,
            COALESCE(SUM(quantidade * valor_unitario), 0) AS valor_pecas
        FROM ordem_pecas
        WHERE ordem_id = ?
    """, (ordem_id,)).fetchone()

    db.execute("""
        UPDATE orcamentos
        SET peca_id = ?,
            valor_peca = ?,
            valor_orcamento = ? + valor_mao_obra,
            valor_total = ? + valor_mao_obra
        WHERE ordem_id = ?
    """, (
        resumo["peca_id"],
        resumo["valor_pecas"],
        resumo["valor_pecas"],
        resumo["valor_pecas"],
        ordem_id,
    ))


@ordem_servico_bp.route("/ordem-servico")
def listar_ordens():
    db = conectar()

    ordens = db.execute("""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            ordens_servico.status,
            clientes.nome AS cliente_nome,
            funcionarios.nome AS funcionario_nome,
            GROUP_CONCAT(
                pecas.nome || ' (' || ordem_pecas.quantidade || 'x)',
                ', '
            ) AS pecas_nomes
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN funcionarios
            ON funcionarios.id = ordens_servico.funcionario_id
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        LEFT JOIN pecas
            ON pecas.id = ordem_pecas.peca_id
        GROUP BY
            ordens_servico.ordem_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            ordens_servico.status,
            clientes.nome,
            funcionarios.nome
        ORDER BY ordens_servico.ordem_id DESC
    """).fetchall()

    db.close()

    return render_template("ordem-servico.html", ordens=ordens)


@ordem_servico_bp.route("/ordem-servico/nova")
def pagina_nova_ordem():
    db = conectar()

    clientes = db.execute("""
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """).fetchall()

    pecas = db.execute("""
        SELECT id, nome, preco_unitario
        FROM pecas
        ORDER BY nome
    """).fetchall()

    funcionarios = db.execute("""
        SELECT id, nome
        FROM funcionarios
        ORDER BY nome
    """).fetchall()

    db.close()

    return render_template(
        "nova-ordem-servico.html",
        clientes=clientes,
        pecas=pecas,
        funcionarios=funcionarios
    )


@ordem_servico_bp.route("/ordem-servico/cadastrar", methods=["POST"])
def cadastrar_ordem():
    cliente_id = request.form["cliente_id"]
    funcionario_id = request.form["funcionario_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    pecas_ids = request.form.getlist("peca_id")
    quantidades = request.form.getlist("quantidade")

    db = conectar()

    cursor = db.execute("""
        INSERT INTO ordens_servico
        (cliente_id, funcionario_id, equipamento, problema_relatado, status)
        VALUES (?, ?, ?, ?, ?)
    """, (cliente_id, funcionario_id, equipamento, problema_relatado, status))

    salvar_pecas_da_ordem(
        db,
        cursor.lastrowid,
        pecas_ids,
        quantidades
    )

    db.commit()
    db.close()

    flash("Ordem de serviço criada com sucesso.", "sucesso")
    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/editar/<int:ordem_id>")
def pagina_editar_ordem(ordem_id):
    db = conectar()

    ordem = db.execute("""
        SELECT
            ordem_id,
            cliente_id,
            funcionario_id,
            equipamento,
            problema_relatado,
            status
        FROM ordens_servico
        WHERE ordem_id = ?
    """, (ordem_id,)).fetchone()

    clientes = db.execute("""
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """).fetchall()

    pecas = db.execute("""
        SELECT id, nome, preco_unitario
        FROM pecas
        ORDER BY nome
    """).fetchall()

    funcionarios = db.execute("""
        SELECT id, nome
        FROM funcionarios
        ORDER BY nome
    """).fetchall()

    pecas_vinculadas = db.execute("""
        SELECT peca_id, quantidade
        FROM ordem_pecas
        WHERE ordem_id = ?
        ORDER BY id
    """, (ordem_id,)).fetchall()

    db.close()

    if ordem is None:
        return redirect("/ordem-servico")

    return render_template(
        "editar-ordem-servico.html",
        ordem=ordem,
        clientes=clientes,
        pecas=pecas,
        funcionarios=funcionarios,
        pecas_vinculadas=pecas_vinculadas
    )


@ordem_servico_bp.route("/ordem-servico/atualizar/<int:ordem_id>", methods=["POST"])
def atualizar_ordem(ordem_id):
    cliente_id = request.form["cliente_id"]
    funcionario_id = request.form["funcionario_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    pecas_ids = request.form.getlist("peca_id")
    quantidades = request.form.getlist("quantidade")

    db = conectar()

    db.execute("""
        UPDATE ordens_servico
        SET cliente_id = ?,
            funcionario_id = ?,
            equipamento = ?,
            problema_relatado = ?,
            status = ?
        WHERE ordem_id = ?
    """, (cliente_id, funcionario_id, equipamento, problema_relatado, status, ordem_id))

    db.execute("""
        DELETE FROM ordem_pecas
        WHERE ordem_id = ?
    """, (ordem_id,))

    salvar_pecas_da_ordem(
        db,
        ordem_id,
        pecas_ids,
        quantidades
    )
    atualizar_valores_orcamento(db, ordem_id)

    db.commit()
    db.close()

    flash("Ordem de serviço atualizada com sucesso.", "sucesso")
    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/excluir/<int:ordem_id>", methods=["POST"])
def excluir_ordem(ordem_id):
    db = conectar()

    db.execute("DELETE FROM orcamentos WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordem_pecas WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordens_servico WHERE ordem_id = ?", (ordem_id,))

    db.commit()
    db.close()

    flash("Ordem de serviço excluída com sucesso.", "sucesso")
    return redirect("/ordem-servico")