from flask import Blueprint, render_template, request, redirect
from database import conectar

ordem_servico_bp = Blueprint("ordem_servico", __name__)

# Página com as ordens de serviço
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
            pecas.nome AS peca_nome
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        LEFT JOIN pecas
            ON pecas.id = ordem_pecas.peca_id
        ORDER BY ordens_servico.ordem_id DESC
    """).fetchall()

    db.close()

    return render_template("ordem-servico.html", ordens=ordens)

# Página pra criar uma nova ordem de serviço
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

    db.close()

    return render_template(
        "nova-ordem-servico.html",
        clientes=clientes,
        pecas=pecas
    )


@ordem_servico_bp.route("/ordem-servico/cadastrar", methods=["POST"])
def cadastrar_ordem():
    cliente_id = request.form["cliente_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    peca_id = request.form["peca_id"]

    db = conectar()

    cursor = db.execute("""
        INSERT INTO ordens_servico
        (cliente_id, equipamento, problema_relatado, status)
        VALUES (?, ?, ?, ?)
    """, (cliente_id, equipamento, problema_relatado, status))

    ordem_id = cursor.lastrowid

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
        """, (ordem_id, peca_id, 1, peca["preco_unitario"]))

    db.commit()
    db.close()

    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/editar/<int:ordem_id>")
def pagina_editar_ordem(ordem_id):
    db = conectar()

    ordem = db.execute("""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.cliente_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            ordens_servico.status,
            ordem_pecas.peca_id
        FROM ordens_servico
        LEFT JOIN ordem_pecas
            ON ordem_pecas.ordem_id = ordens_servico.ordem_id
        WHERE ordens_servico.ordem_id = ?
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

    db.close()

    if ordem is None:
        return redirect("/ordem-servico")

    return render_template(
        "editar-ordem-servico.html",
        ordem=ordem,
        clientes=clientes,
        pecas=pecas
    )


@ordem_servico_bp.route("/ordem-servico/atualizar/<int:ordem_id>", methods=["POST"])
def atualizar_ordem(ordem_id):
    cliente_id = request.form["cliente_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    peca_id = request.form["peca_id"]

    db = conectar()

    db.execute("""
        UPDATE ordens_servico
        SET cliente_id = ?,
            equipamento = ?,
            problema_relatado = ?,
            status = ?
        WHERE ordem_id = ?
    """, (cliente_id, equipamento, problema_relatado, status, ordem_id))

    peca = db.execute("""
        SELECT preco_unitario
        FROM pecas
        WHERE id = ?
    """, (peca_id,)).fetchone()

    db.execute("""
        DELETE FROM ordem_pecas
        WHERE ordem_id = ?
    """, (ordem_id,))

    if peca is not None:
        db.execute("""
            INSERT INTO ordem_pecas
            (ordem_id, peca_id, quantidade, valor_unitario)
            VALUES (?, ?, ?, ?)
        """, (ordem_id, peca_id, 1, peca["preco_unitario"]))

    db.commit()
    db.close()

    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/excluir/<int:ordem_id>", methods=["POST"])
def excluir_ordem(ordem_id):
    db = conectar()

    db.execute("DELETE FROM orcamentos WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordem_pecas WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordens_servico WHERE ordem_id = ?", (ordem_id,))

    db.commit()
    db.close()

    return redirect("/ordem-servico")
