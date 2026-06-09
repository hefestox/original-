from db import db
from datetime import datetime
import uuid


def gerar_codigo():
    return str(uuid.uuid4())[:8].upper()


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    instagram = db.Column(db.String(100), nullable=True)

    # PIX
    pix_tipo = db.Column(db.String(20), nullable=True)   # cpf | email | telefone | aleatorio
    pix_chave = db.Column(db.String(150), nullable=True)

    # Rede de indicação
    codigo_indicacao = db.Column(db.String(10), unique=True, default=gerar_codigo)
    indicado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    saldo = db.Column(db.Float, default=0.0)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    indicados = db.relationship("Usuario", backref=db.backref("indicador", remote_side=[id]))
    submissoes = db.relationship("Submissao", backref="usuario", lazy=True)
    saques = db.relationship("Saque", backref="usuario", lazy=True)
    transacoes = db.relationship("Transacao", backref="usuario", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "instagram": self.instagram,
            "pix_tipo": self.pix_tipo,
            "pix_chave": self.pix_chave,
            "codigo_indicacao": self.codigo_indicacao,
            "saldo": self.saldo,
            "indicado_por_id": self.indicado_por_id,
            "criado_em": self.criado_em.isoformat(),
        }


class Tarefa(db.Model):
    __tablename__ = "tarefas"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)        # curtir | comentar | seguir
    descricao = db.Column(db.Text, nullable=False)
    link_alvo = db.Column(db.String(300), nullable=True)   # perfil ou post alvo
    valor = db.Column(db.Float, nullable=False)
    ativa = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    submissoes = db.relationship("Submissao", backref="tarefa", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "link_alvo": self.link_alvo,
            "valor": self.valor,
            "ativa": self.ativa,
        }


class Submissao(db.Model):
    __tablename__ = "submissoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tarefa_id = db.Column(db.Integer, db.ForeignKey("tarefas.id"), nullable=False)
    imagem_url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="pendente")  # pendente | aprovado | rejeitado
    motivo_rejeicao = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    avaliado_em = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "tarefa_id": self.tarefa_id,
            "imagem_url": self.imagem_url,
            "status": self.status,
            "motivo_rejeicao": self.motivo_rejeicao,
            "criado_em": self.criado_em.isoformat(),
        }


class Transacao(db.Model):
    """Registro de todos os créditos e débitos do saldo."""
    __tablename__ = "transacoes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)   # tarefa | comissao_n1 | comissao_n2 | saque
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200), nullable=True)
    referencia_id = db.Column(db.Integer, nullable=True)  # id da submissao ou saque relacionado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "valor": self.valor,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat(),
        }


class Saque(db.Model):
    __tablename__ = "saques"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    pix_chave = db.Column(db.String(150), nullable=False)
    pix_tipo = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pendente")  # pendente | pago | recusado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    pago_em = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "valor": self.valor,
            "pix_chave": self.pix_chave,
            "pix_tipo": self.pix_tipo,
            "status": self.status,
            "criado_em": self.criado_em.isoformat(),
        }
