# TaskGram — Plataforma de Tarefas Instagram

Plataforma onde usuários recebem tarefas do Instagram (curtir, comentar, seguir) e ganham dinheiro por isso. Possui sistema de rede de indicação em 2 níveis com comissão automática.

---

## Instalação

```bash
pip install -r requisitos.txt
python main.py
```

---

## Estrutura de arquivos

```
taskgram/
├── main.py              # Inicialização da aplicação
├── db.py                # Conexão com banco de dados
├── auth.py              # Cadastro e login
├── tarefas.py           # Tarefas e submissão de prints
├── saldo.py             # Saldo, extrato e saques
├── rede.py              # Lógica de comissão em 2 níveis
├── rede_routes.py       # Rotas da rede de indicação
├── modelos/
│   └── models.py        # Todos os modelos do banco
├── static/uploads/      # Prints enviados pelos usuários
└── requisitos.txt
```

---

## Cadastro de usuário

**POST /auth/cadastro**

Campos obrigatórios:
| Campo           | Tipo   | Descrição                              |
|----------------|--------|----------------------------------------|
| nome           | string | Nome completo                          |
| email          | string | E-mail único                           |
| senha          | string | Senha de acesso                        |
| pix_tipo       | string | `cpf`, `email`, `telefone`, `aleatorio`|
| pix_chave      | string | Chave PIX correspondente ao tipo       |
| instagram      | string | Usuário do Instagram (opcional)        |
| codigo_indicacao | string | Código de quem indicou (opcional)   |

---

## Rotas da API

### Autenticação
| Método | Rota               | Descrição                   |
|--------|--------------------|-----------------------------|
| POST   | /auth/cadastro     | Cadastrar novo usuário      |
| POST   | /auth/login        | Login                       |
| POST   | /auth/logout       | Logout                      |
| GET    | /auth/perfil       | Ver perfil do usuário       |
| PUT    | /auth/perfil/pix   | Atualizar chave PIX         |

### Tarefas (usuário)
| Método | Rota                            | Descrição                    |
|--------|---------------------------------|------------------------------|
| GET    | /tarefas/                       | Listar tarefas disponíveis   |
| POST   | /tarefas/{id}/submeter          | Enviar print (multipart)     |
| GET    | /tarefas/minhas                 | Ver minhas submissões        |

### Tarefas (admin)
| Método | Rota                                    | Descrição              |
|--------|-----------------------------------------|------------------------|
| POST   | /tarefas/admin/criar                    | Criar tarefa           |
| GET    | /tarefas/admin/submissoes               | Ver prints pendentes   |
| POST   | /tarefas/admin/submissoes/{id}/aprovar  | Aprovar print          |
| POST   | /tarefas/admin/submissoes/{id}/rejeitar | Rejeitar print         |

### Saldo e saques
| Método | Rota                            | Descrição                  |
|--------|---------------------------------|----------------------------|
| GET    | /saldo/                         | Ver saldo atual            |
| GET    | /saldo/extrato                  | Histórico de transações    |
| POST   | /saldo/sacar                    | Solicitar saque via PIX    |
| GET    | /saldo/saques                   | Histórico de saques        |
| GET    | /saldo/admin/saques             | Saques pendentes (admin)   |
| POST   | /saldo/admin/saques/{id}/pagar  | Marcar como pago (admin)   |
| POST   | /saldo/admin/saques/{id}/recusar| Recusar e estornar (admin) |

### Rede de indicação
| Método | Rota   | Descrição                                    |
|--------|--------|----------------------------------------------|
| GET    | /rede/ | Ver rede, código de indicação e comissões    |

---

## Sistema de comissão

- **Nível 1**: 10% dos ganhos de quem você indicou diretamente
- **Nível 2**: 5% dos ganhos de quem seu indicado indicou

As comissões são creditadas automaticamente toda vez que uma submissão é aprovada.

---

## Exemplo: cadastro com indicação

```json
POST /auth/cadastro
{
  "nome": "Maria Silva",
  "email": "maria@email.com",
  "senha": "senha123",
  "pix_tipo": "cpf",
  "pix_chave": "123.456.789-00",
  "instagram": "@mariasilva",
  "codigo_indicacao": "AB12CD34"
}
```

## Exemplo: envio de print

```
POST /tarefas/3/submeter
Content-Type: multipart/form-data
Campo: print = arquivo.jpg
```
