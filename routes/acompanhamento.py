from flask import Blueprint, render_template, request
from database import conectar
acompanhamento_bp = Blueprint("acompanhamento", __name__)

# Número de WhatsApp da assistência (formato internacional: 55 + DDD + número).
# Mantém apenas dígitos, removendo +, espaços, parênteses e traços.
# TODO: confirmar o número real — celulares BR têm 13 dígitos (55 + DDD + 9 + 8 dígitos).
_WHATSAPP_BRUTO = "5541992121508"
WHATSAPP_NUMERO = "".join(c for c in _WHATSAPP_BRUTO if c.isdigit())


def buscar_ordens(consulta):
    db = conectar()

    if consulta.isdigit():
        filtro = "ordens_servico.ordem_id = ?"
        parametros = (int(consulta),)
    else:
        filtro = "clientes.nome LIKE ?"
        parametros = (f"%{consulta}%",)

    ordens = db.execute(f"""
        SELECT
            ordens_servico.ordem_id,
            ordens_servico.equipamento,
            ordens_servico.problema_relatado,
            ordens_servico.status,
            ordens_servico.data_abertura,
            ordens_servico.data_finalizacao,
            clientes.nome AS cliente_nome,
            funcionarios.nome AS funcionario_nome,
            orcamentos.problema_analisado AS diagnostico,
            orcamentos.valor_total AS valor_servico,
            equipamentos.tipo AS equipamento_tipo,
            equipamentos.marca AS equipamento_marca,
            equipamentos.modelo AS equipamento_modelo
        FROM ordens_servico
        JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        LEFT JOIN funcionarios
            ON funcionarios.id = ordens_servico.funcionario_id
        LEFT JOIN orcamentos
            ON orcamentos.ordem_id = ordens_servico.ordem_id
        LEFT JOIN equipamentos
            ON equipamentos.cliente_id = clientes.id
           AND (
                LOWER(ordens_servico.equipamento) LIKE '%' || LOWER(equipamentos.tipo) || '%'
                OR LOWER(ordens_servico.equipamento) LIKE '%' || LOWER(equipamentos.marca) || '%'
                OR LOWER(ordens_servico.equipamento) LIKE '%' || LOWER(equipamentos.modelo) || '%'
           )
        WHERE {filtro}
        GROUP BY ordens_servico.ordem_id
        ORDER BY ordens_servico.ordem_id DESC
    """, parametros).fetchall()

    db.close()
    return ordens


@acompanhamento_bp.route("/acompanhamento")
def pagina_acompanhamento():
    return render_template("acompanhamento.html")


@acompanhamento_bp.route("/acompanhamento/resultado", methods=["POST"])
def resultado_acompanhamento():
    consulta = request.form.get("consulta", "").strip()

    if not consulta:
        ordens = []
    else:
        ordens = buscar_ordens(consulta)

    return render_template(
        "resultado_acompanhamento.html",
        ordens=ordens,
        consulta=consulta,
        whatsapp=WHATSAPP_NUMERO,
    )
