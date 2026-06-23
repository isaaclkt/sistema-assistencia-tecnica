from datetime import datetime

from flask import Blueprint, flash, render_template, request, redirect, send_file
from database import conectar, estornar_estoque

ordem_servico_bp = Blueprint("ordem_servico", __name__)


def _carregar_ordem_completa(db, ordem_id):
    """Carrega uma OS com dados do cliente, atendente e peças vinculadas."""
    ordem = db.execute("""
        SELECT
            os.ordem_id,
            os.equipamento,
            os.problema_relatado,
            os.status,
            os.laudo,
            os.garantia,
            os.prazo_entrega,
            c.nome AS cliente_nome,
            c.cpf AS cliente_cpf,
            c.telefone AS cliente_telefone,
            c.email AS cliente_email,
            c.endereco AS cliente_endereco,
            f.nome AS funcionario_nome
        FROM ordens_servico os
        JOIN clientes c ON c.id = os.cliente_id
        LEFT JOIN funcionarios f ON f.id = os.funcionario_id
        WHERE os.ordem_id = ?
    """, (ordem_id,)).fetchone()

    pecas = db.execute("""
        SELECT p.nome AS nome, op.quantidade AS quantidade, op.valor_unitario AS valor_unitario
        FROM ordem_pecas op
        JOIN pecas p ON p.id = op.peca_id
        WHERE op.ordem_id = ?
        ORDER BY op.id
    """, (ordem_id,)).fetchall()

    return ordem, pecas


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

    funcionarios = db.execute("""
        SELECT id, nome
        FROM funcionarios
        ORDER BY nome
    """).fetchall()

    db.close()

    return render_template(
        "nova-ordem-servico.html",
        clientes=clientes,
        funcionarios=funcionarios
    )


@ordem_servico_bp.route("/ordem-servico/cadastrar", methods=["POST"])
def cadastrar_ordem():
    cliente_id = request.form["cliente_id"]
    funcionario_id = request.form["funcionario_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    laudo = request.form.get("laudo", "")
    garantia = request.form.get("garantia", "")
    prazo_entrega = request.form.get("prazo_entrega", "")

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    data_finalizacao = agora if status == "Finalizado" else None

    db = conectar()
    db.execute("""
        INSERT INTO ordens_servico
        (cliente_id, funcionario_id, equipamento, problema_relatado, status,
         data_abertura, data_finalizacao, laudo, garantia, prazo_entrega)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente_id, funcionario_id, equipamento, problema_relatado, status,
          agora, data_finalizacao, laudo, garantia, prazo_entrega))
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
            status,
            laudo,
            garantia,
            prazo_entrega
        FROM ordens_servico
        WHERE ordem_id = ?
    """, (ordem_id,)).fetchone()

    clientes = db.execute("""
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """).fetchall()

    funcionarios = db.execute("""
        SELECT id, nome
        FROM funcionarios
        ORDER BY nome
    """).fetchall()

    db.close()

    if ordem is None:
        return redirect("/ordem-servico")

    return render_template(
        "editar-ordem-servico.html",
        ordem=ordem,
        clientes=clientes,
        funcionarios=funcionarios
    )


@ordem_servico_bp.route("/ordem-servico/atualizar/<int:ordem_id>", methods=["POST"])
def atualizar_ordem(ordem_id):
    cliente_id = request.form["cliente_id"]
    funcionario_id = request.form["funcionario_id"]
    equipamento = request.form["equipamento"]
    problema_relatado = request.form["problema_relatado"]
    status = request.form["status"]
    laudo = request.form.get("laudo", "")
    garantia = request.form.get("garantia", "")
    prazo_entrega = request.form.get("prazo_entrega", "")

    db = conectar()

    atual = db.execute(
        "SELECT data_finalizacao FROM ordens_servico WHERE ordem_id = ?",
        (ordem_id,),
    ).fetchone()

    if status == "Finalizado":
        data_finalizacao = (
            atual["data_finalizacao"]
            if atual and atual["data_finalizacao"]
            else datetime.now().strftime("%d/%m/%Y %H:%M")
        )
    else:
        data_finalizacao = None

    db.execute("""
        UPDATE ordens_servico
        SET cliente_id = ?,
            funcionario_id = ?,
            equipamento = ?,
            problema_relatado = ?,
            status = ?,
            data_finalizacao = ?,
            laudo = ?,
            garantia = ?,
            prazo_entrega = ?
        WHERE ordem_id = ?
    """, (cliente_id, funcionario_id, equipamento, problema_relatado, status,
          data_finalizacao, laudo, garantia, prazo_entrega, ordem_id))
    db.commit()
    db.close()

    flash("Ordem de serviço atualizada com sucesso.", "sucesso")
    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/excluir/<int:ordem_id>", methods=["POST"])
def excluir_ordem(ordem_id):
    db = conectar()

    # Se houver orçamento aprovado, devolve as peças ao estoque antes de apagar.
    orc = db.execute(
        "SELECT status FROM orcamentos WHERE ordem_id = ?", (ordem_id,)
    ).fetchone()
    if orc and orc["status"] == "Aprovado":
        estornar_estoque(db, ordem_id)

    db.execute("DELETE FROM orcamentos WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordem_pecas WHERE ordem_id = ?", (ordem_id,))
    db.execute("DELETE FROM ordens_servico WHERE ordem_id = ?", (ordem_id,))

    db.commit()
    db.close()

    flash("Ordem de serviço excluída com sucesso.", "sucesso")
    return redirect("/ordem-servico")


@ordem_servico_bp.route("/ordem-servico/visualizar/<int:ordem_id>")
def visualizar_ordem(ordem_id):
    db = conectar()
    ordem, pecas = _carregar_ordem_completa(db, ordem_id)
    db.close()

    if ordem is None:
        flash("Ordem de serviço não encontrada.", "erro")
        return redirect("/ordem-servico")

    return render_template(
        "visualizar-ordem-servico.html",
        ordem=ordem,
        pecas=pecas,
        emissao=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )


@ordem_servico_bp.route("/ordem-servico/<int:ordem_id>/pdf")
def gerar_os_pdf(ordem_id):
    import tempfile

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    db = conectar()
    ordem, pecas = _carregar_ordem_completa(db, ordem_id)
    db.close()

    if ordem is None:
        flash("Ordem de serviço não encontrada.", "erro")
        return redirect("/ordem-servico")

    emissao = datetime.now().strftime("%d/%m/%Y")

    est_empresa = ParagraphStyle("empresa", fontName="Helvetica-Bold", fontSize=11, leading=13)
    est_os = ParagraphStyle("os", fontName="Helvetica-Bold", fontSize=9, leading=12, alignment=2)
    est_band = ParagraphStyle("band", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white)
    est_label = ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, leading=10)
    est_valor = ParagraphStyle("valor", fontName="Helvetica", fontSize=8.5, leading=11)

    L = A4[0] - 24 * mm
    COL_ROTULO = L * 0.26
    COL_VALOR = L * 0.74
    azul = colors.HexColor("#123a66")
    laranja = colors.HexColor("#d9531e")
    cinza = colors.HexColor("#999999")

    def P(texto, estilo):
        return Paragraph(str(texto) if texto not in (None, "") else " ", estilo)

    def via_flowables(com_assinatura, titulo_via):
        elems = []

        cab = Table([[
            Paragraph(
                "SISTEMA DE ASSISTÊNCIA TÉCNICA"
                "<br/><font size=7 color='#555555'>Endereço: ____________________________"
                "<br/>Telefone / WhatsApp: __________________</font>",
                est_empresa,
            ),
            Paragraph(
                f"ORDEM DE SERVIÇO<br/>Nº {ordem['ordem_id']}<br/>"
                f"<font size=8>Data: {emissao}</font><br/>"
                f"<font color='#155da5' size=8>{titulo_via}</font>",
                est_os,
            ),
        ]], colWidths=[L * 0.6, L * 0.4])
        cab.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 1, azul),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elems.append(cab)

        linhas = []
        alturas = []
        estilo = [
            ("GRID", (0, 0), (-1, -1), 0.5, cinza),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        def add(rotulo, valor, altura=15):
            linhas.append([P(rotulo, est_label), P(valor, est_valor)])
            alturas.append(altura)

        def add_banda(texto, cor):
            i = len(linhas)
            linhas.append([P(texto, est_band), ""])
            alturas.append(14)
            estilo.append(("SPAN", (0, i), (1, i)))
            estilo.append(("BACKGROUND", (0, i), (1, i), cor))

        add_banda("DADOS DO CLIENTE", laranja)
        add("Nome", ordem["cliente_nome"])
        add("Cpf ou Rg", ordem["cliente_cpf"])
        add("Telefone", ordem["cliente_telefone"])

        add_banda("EQUIPAMENTO", azul)
        add("Equipamento", ordem["equipamento"])
        add("Marca", "")
        add("Modelo", "")
        add("Nº de série", "")
        add("Acessórios", "")
        add("Defeito", ordem["problema_relatado"], altura=36)
        add("Laudo técnico", ordem["laudo"], altura=36)

        add("Garantia", ordem["garantia"])
        add("Prazo de entrega", ordem["prazo_entrega"])
        add("Observações", "", altura=32)
        add("Atendente", ordem["funcionario_nome"])

        if com_assinatura:
            i = len(linhas)
            linhas.append([
                P("Assinatura do cliente", est_label),
                Paragraph("___________________________________________", est_valor),
            ])
            alturas.append(36)
            estilo.append(("VALIGN", (0, i), (1, i), "BOTTOM"))

        corpo = Table(linhas, colWidths=[COL_ROTULO, COL_VALOR], rowHeights=alturas)
        corpo.setStyle(TableStyle(estilo))
        elems.append(corpo)

        return elems

    arquivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(
        arquivo_temp.name, pagesize=A4,
        leftMargin=12 * mm, rightMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm,
    )

    elementos = []
    elementos += via_flowables(com_assinatura=True, titulo_via="VIA DA EMPRESA")
    elementos.append(Spacer(1, 8))
    elementos.append(HRFlowable(width="100%", thickness=0.7, dash=(3, 3), color=colors.HexColor("#999999")))
    elementos.append(Paragraph("recorte aqui", ParagraphStyle(
        "corte", fontName="Helvetica-Oblique", fontSize=6.5, alignment=1,
        textColor=colors.HexColor("#999999"))))
    elementos.append(Spacer(1, 6))
    elementos += via_flowables(com_assinatura=False, titulo_via="VIA DO CLIENTE")

    pdf.build(elementos)

    return send_file(
        arquivo_temp.name,
        as_attachment=True,
        download_name=f"OS_{ordem_id}.pdf",
    )
