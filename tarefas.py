import os
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from werkzeug.utils import secure_filename
from db import db
from modelos.models import Tarefa, Submissao, Usuario, Transacao
from rede import pagar_comissoes

tarefas_bp = Blueprint("tarefas", __name__, url_prefix="/tarefas")

UPLOAD_FOLDER = "static/uploads"
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}


def extensao_valida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS


# ── Usuário ──────────────────────────────────────────────────────────────────

@tarefas_bp.route("/", methods=["GET"])
def listar():
    tarefas = Tarefa.query.filter_by(ativa=True).order_by(Tarefa.criado_em.desc()).all()
    return jsonify([t.to_dict() for t in tarefas])


@tarefas_bp.route("/<int:tarefa_id>/submeter", methods=["POST"])
def submeter(tarefa_id):
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401

    tarefa = Tarefa.query.get_or_404(tarefa_id)
    if not tarefa.ativa:
        return jsonify({"erro": "Tarefa não disponível"}), 400

    # Evita dupla submissão pendente/aprovada
    duplicada = Submissao.query.filter_by(
        usuario_id=uid, tarefa_id=tarefa_id
    ).filter(Submissao.status.in_(["pendente", "aprovado"])).first()
    if duplicada:
        return jsonify({"erro": "Você já submeteu ou completou esta tarefa"}), 400

    if "print" not in request.files:
        return jsonify({"erro": "Envie o print como campo 'print'"}), 400

    arquivo = request.files["print"]
    if not extensao_valida(arquivo.filename):
        return jsonify({"erro": "Formato inválido. Use PNG, JPG ou WEBP"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    nome_arquivo = f"{uid}_{tarefa_id}_{int(datetime.utcnow().timestamp())}_{secure_filename(arquivo.filename)}"
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    arquivo.save(caminho)

    sub = Submissao(
        usuario_id=uid,
        tarefa_id=tarefa_id,
        imagem_url=caminho,
    )
    db.session.add(sub)
    db.session.commit()

    return jsonify({"mensagem": "Submissão enviada! Aguarde aprovação.", "submissao": sub.to_dict()}), 201


@tarefas_bp.route("/minhas", methods=["GET"])
def minhas_submissoes():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    subs = Submissao.query.filter_by(usuario_id=uid).order_by(Submissao.criado_em.desc()).all()
    return jsonify([s.to_dict() for s in subs])


# ── Admin ─────────────────────────────────────────────────────────────────────

@tarefas_bp.route("/admin/criar", methods=["POST"])
def criar_tarefa():
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403

    dados = request.get_json()
    for campo in ["tipo", "descricao", "valor"]:
        if not dados.get(campo):
            return jsonify({"erro": f"Campo '{campo}' obrigatório"}), 400

    tarefa = Tarefa(
        tipo=dados["tipo"],
        descricao=dados["descricao"],
        link_alvo=dados.get("link_alvo", ""),
        valor=float(dados["valor"]),
    )
    db.session.add(tarefa)
    db.session.commit()
    return jsonify({"mensagem": "Tarefa criada", "tarefa": tarefa.to_dict()}), 201


@tarefas_bp.route("/admin/submissoes", methods=["GET"])
def listar_submissoes():
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403
    subs = Submissao.query.filter_by(status="pendente").order_by(Submissao.criado_em).all()
    return jsonify([s.to_dict() for s in subs])


@tarefas_bp.route("/admin/submissoes/<int:sub_id>/aprovar", methods=["POST"])
def aprovar(sub_id):
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403

    sub = Submissao.query.get_or_404(sub_id)
    if sub.status != "pendente":
        return jsonify({"erro": "Submissão já avaliada"}), 400

    sub.status = "aprovado"
    sub.avaliado_em = datetime.utcnow()

    usuario = Usuario.query.get(sub.usuario_id)
    valor = sub.tarefa.valor
    usuario.saldo += valor

    db.session.add(Transacao(
        usuario_id=usuario.id,
        tipo="tarefa",
        valor=valor,
        descricao=f"Tarefa aprovada: {sub.tarefa.descricao[:60]}",
        referencia_id=sub.id,
    ))

    db.session.commit()

    # Pagar comissões na rede
    pagar_comissoes(usuario.id, valor, sub.id)

    return jsonify({"mensagem": "Aprovado e saldo creditado"})


@tarefas_bp.route("/admin/submissoes/<int:sub_id>/rejeitar", methods=["POST"])
def rejeitar(sub_id):
    if not session.get("admin"):
        return jsonify({"erro": "Acesso negado"}), 403

    sub = Submissao.query.get_or_404(sub_id)
    if sub.status != "pendente":
        return jsonify({"erro": "Submissão já avaliada"}), 400

    dados = request.get_json() or {}
    sub.status = "rejeitado"
    sub.motivo_rejeicao = dados.get("motivo", "Print inválido ou tarefa não executada corretamente")
    sub.avaliado_em = datetime.utcnow()

    db.session.commit()
    return jsonify({"mensagem": "Submissão rejeitada"})
