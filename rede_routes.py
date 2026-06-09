from flask import Blueprint, jsonify, session
from rede import resumo_rede

rede_bp = Blueprint("rede", __name__, url_prefix="/rede")


@rede_bp.route("/", methods=["GET"])
def minha_rede():
    uid = session.get("usuario_id")
    if not uid:
        return jsonify({"erro": "Não autenticado"}), 401
    return jsonify(resumo_rede(uid))
