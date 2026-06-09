from flask import Flask
from db import db
from auth import auth_bp
from tarefas import tarefas_bp
from saldo import saldo_bp
from rede_routes import rede_bp


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskgram.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB por upload

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tarefas_bp)
    app.register_blueprint(saldo_bp)
    app.register_blueprint(rede_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
