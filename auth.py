from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from modelos.models import Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

TIPOS_PIX_VALIDOS = ["cpf", "email", "telefone", "aleatorio"]


@auth_bp.route("/cadastro", methods=["POST"])
def cadastro():
    dados = request.get_json()

    # Campos obrigatórios
    campos = ["nome", "email", "senha", "pix_tipo", "pix_chave"]
    for campo in campos:
        if not dados.get(campo):
            return jsonify({"erro": f"Campo '{campo}' é obrigatório"}), 400

    if dados["pix_tipo"] not in TIPOS_PIX_VALIDOS:
        return jsonify({"erro": "Tipo de PIX inválido. Use: cpf, email, telefone ou aleatorio"}), 400

    if Usuario.query.filter_by(email=dados["email"]).first():
        return jsonify({"erro": "E-mail já cadastrado"}), 400

    # Processa código de indicação (opcional)
    indicador = None
    codigo_ref = dados.get("codigo_indicacao", "").strip().upper()
    if codigo_ref:
        indicador = Usuario.query.filter_by(codigo_indicacao=codigo_ref).first()
        if not indicador:
            return jsonify({"erro": "Código de indicação inválido"}), 400

    novo = Usuario(
        nome=dados["nome"],
        email=dados["email"],
        senha_hash=generate_password_hash(dados["senha"]),
        instagram=dados.get("instagram", ""),
        pix_tipo=dados["pix_tipo"],
        pix_chave=dados["pix_chave"],
        indicado_por_id=indicador.id if indicador else None,
    )

    db.session.add(novo)
    db.session.commit()

    return jsonify({
        "mensagem": "Cadastro realizado com sucesso!",
        "usuario": novo.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not check_password_hash(usuario.senha_hash, senha):
        return jsonify({"erro": "E-mail ou senha incorretos"}), 401

    if not usuario.ativo:
        return jsonify({"erro": "Conta desativada"}), 403

    session["usuario_id"] = usuario.id
    session["admin"] = getattr(usuario, "is_admin", False)

    return jsonify({"mensagem": "Login realizado", "usuario": usuario.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado"})


@auth_bp.route("/perfil", methods=["GET"])
def perfil():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    usuario = Usuario.query.get_or_404(uid)
    return jsonify(usuario.to_dict())


@auth_bp.route("/perfil/pix", methods=["PUT"])
def atualizar_pix():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401

    dados = request.get_json()
    usuario = Usuario.query.get_or_404(uid)

    if dados.get("pix_tipo") and dados["pix_tipo"] not in TIPOS_PIX_VALIDOS:
        return jsonify({"erro": "Tipo de PIX inválido"}), 400

    if dados.get("pix_tipo"):
        usuario.pix_tipo = dados["pix_tipo"]
    if dados.get("pix_chave"):
        usuario.pix_chave = dados["pix_chave"]

    db.session.commit()
    return jsonify({"mensagem": "Dados PIX atualizados", "usuario": usuario.to_dict()})
