from flask import Blueprint, request, jsonify, session
from datetime import datetime
from db import db
from modelos.models import Saque, Usuario, Transacao

saldo_bp = Blueprint("saldo", __name__, url_prefix="/saldo")

VALOR_MINIMO_SAQUE = 10.00


@saldo_bp.route("/", methods=["GET"])
def ver_saldo():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    usuario = Usuario.query.get_or_404(uid)
    return jsonify({"saldo": round(usuario.saldo, 2)})


@saldo_bp.route("/extrato", methods=["GET"])
def extrato():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    transacoes = (
        Transacao.query.filter_by(usuario_id=uid)
        .order_by(Transacao.criado_em.desc())
        .limit(50)
        .all()
    )
    return jsonify([t.to_dict() for t in transacoes])


@saldo_bp.route("/sacar", methods=["POST"])
def solicitar_saque():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401

    dados = request.get_json()
    valor = float(dados.get("valor", 0))

    if valor < VALOR_MINIMO_SAQUE:
        return jsonify({"erro": f"Valor mínimo para saque: R$ {VALOR_MINIMO_SAQUE:.2f}"}), 400

    usuario = Usuario.query.get_or_404(uid)
    if usuario.saldo < valor:
        return jsonify({"erro": "Saldo insuficiente"}), 400

    if not usuario.pix_chave:
        return jsonify({"erro": "Cadastre sua chave PIX antes de sacar"}), 400

    # Debita saldo imediatamente
    usuario.saldo -= valor

    saque = Saque(
        usuario_id=uid,
        valor=valor,
        pix_chave=usuario.pix_chave,
        pix_tipo=usuario.pix_tipo,
    )
    db.session.add(saque)

    db.session.add(Transacao(
        usuario_id=uid,
        tipo="saque",
        valor=-valor,
        descricao=f"Saque solicitado via PIX ({usuario.pix_tipo})",
    ))

    db.session.commit()
    return jsonify({"mensagem": "Saque solicitado! Será processado em até 24h.", "saque": saque.to_dict()}), 201


@saldo_bp.route("/saques", methods=["GET"])
def historico_saques():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    saques = Saque.query.filter_by(usuario_id=uid).order_by(Saque.criado_em.desc()).all()
    return jsonify([s.to_dict() for s in saques])


# ── Admin ─────────────────────────────────────────────────────────────────────

@saldo_bp.route("/admin/saques", methods=["GET"])
def admin_saques():
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403
    saques = Saque.query.filter_by(status="pendente").order_by(Saque.criado_em).all()
    return jsonify([s.to_dict() for s in saques])


@saldo_bp.route("/admin/saques/<int:saque_id>/pagar", methods=["POST"])
def marcar_pago(saque_id):
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403
    saque = Saque.query.get_or_404(saque_id)
    saque.status = "pago"
    saque.pago_em = datetime.utcnow()
    db.session.commit()
    return jsonify({"mensagem": "Saque marcado como pago"})


@saldo_bp.route("/admin/saques/<int:saque_id>/recusar", methods=["POST"])
def recusar_saque(saque_id):
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403
    saque = Saque.query.get_or_404(saque_id)
    if saque.status != "pendente":
        return jsonify({"erro": "Saque já processado"}), 400

    # Estorna saldo
    usuario = Usuario.query.get(saque.usuario_id)
    usuario.saldo += saque.valor
    saque.status = "recusado"

    db.session.add(Transacao(
        usuario_id=saque.usuario_id,
        tipo="saque",
        valor=saque.valor,
        descricao="Estorno — saque recusado pelo admin",
        referencia_id=saque.id,
    ))

    db.session.commit()
    return jsonify({"mensagem": "Saque recusado e saldo estornado"})
