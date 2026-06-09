from db import db
from modelos.models import Usuario, Transacao

# Percentuais de comissão por nível
COMISSAO_NIVEL_1 = 0.10   # 10% sobre o ganho do indicado direto
COMISSAO_NIVEL_2 = 0.05   # 5% sobre o ganho do indicado do indicado


def pagar_comissoes(usuario_id: int, valor_tarefa: float, submissao_id: int):
    """
    Calcula e credita comissões na rede de indicação do usuário.
    Nível 1: quem indicou diretamente o executor
    Nível 2: quem indicou o indicador
    """
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return

    # --- Nível 1 ---
    if usuario.indicado_por_id:
        n1 = Usuario.query.get(usuario.indicado_por_id)
        if n1:
            comissao_n1 = round(valor_tarefa * COMISSAO_NIVEL_1, 2)
            n1.saldo += comissao_n1

            db.session.add(Transacao(
                usuario_id=n1.id,
                tipo="comissao_n1",
                valor=comissao_n1,
                descricao=f"Comissão N1 — {usuario.nome} completou uma tarefa",
                referencia_id=submissao_id,
            ))

            # --- Nível 2 ---
            if n1.indicado_por_id:
                n2 = Usuario.query.get(n1.indicado_por_id)
                if n2:
                    comissao_n2 = round(valor_tarefa * COMISSAO_NIVEL_2, 2)
                    n2.saldo += comissao_n2

                    db.session.add(Transacao(
                        usuario_id=n2.id,
                        tipo="comissao_n2",
                        valor=comissao_n2,
                        descricao=f"Comissão N2 — {usuario.nome} completou uma tarefa",
                        referencia_id=submissao_id,
                    ))

    db.session.commit()


def resumo_rede(usuario_id: int):
    """Retorna estatísticas da rede de indicados do usuário."""
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return {}

    indicados_n1 = Usuario.query.filter_by(indicado_por_id=usuario_id).all()

    indicados_n2 = []
    for n1 in indicados_n1:
        filhos = Usuario.query.filter_by(indicado_por_id=n1.id).all()
        indicados_n2.extend(filhos)

    total_ganho_n1 = sum(
        t.valor for n1 in indicados_n1
        for t in Transacao.query.filter_by(usuario_id=usuario_id, tipo="comissao_n1").all()
    )
    total_ganho_n2 = sum(
        t.valor for t in Transacao.query.filter_by(usuario_id=usuario_id, tipo="comissao_n2").all()
    )

    return {
        "codigo_indicacao": usuario.codigo_indicacao,
        "nivel_1": {
            "total": len(indicados_n1),
            "percentual": f"{int(COMISSAO_NIVEL_1 * 100)}%",
            "total_ganho": round(total_ganho_n1, 2),
            "membros": [{"id": u.id, "nome": u.nome, "instagram": u.instagram} for u in indicados_n1],
        },
        "nivel_2": {
            "total": len(indicados_n2),
            "percentual": f"{int(COMISSAO_NIVEL_2 * 100)}%",
            "total_ganho": round(total_ganho_n2, 2),
            "membros": [{"id": u.id, "nome": u.nome, "instagram": u.instagram} for u in indicados_n2],
        },
    }
