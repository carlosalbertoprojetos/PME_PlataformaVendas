from dataclasses import dataclass, field
from typing import Any


class EventType:
    CLIENTE_CRIADO = "cliente_criado"
    LEAD_CRIADO = "lead_criado"
    PRODUTO_CRIADO = "produto_criado"
    PEDIDO_CRIADO = "pedido_criado"
    PEDIDO_CONFIRMADO = "pedido_confirmado"
    OPORTUNIDADE_CRIADA = "oportunidade_criada"
    OPORTUNIDADE_ATUALIZADA = "oportunidade_atualizada"
    PROXIMA_ACAO_CRIADA = "proxima_acao_criada"
    PROXIMA_ACAO_CONCLUIDA = "proxima_acao_concluida"
    CATALOGO_COMPARTILHADO = "catalogo_compartilhado"


EVENT_TYPE_LABELS = {
    EventType.CLIENTE_CRIADO: "Cliente criado",
    EventType.LEAD_CRIADO: "Lead criado",
    EventType.PRODUTO_CRIADO: "Produto criado",
    EventType.PEDIDO_CRIADO: "Pedido criado",
    EventType.PEDIDO_CONFIRMADO: "Pedido confirmado",
    EventType.OPORTUNIDADE_CRIADA: "Oportunidade criada",
    EventType.OPORTUNIDADE_ATUALIZADA: "Mudanca de status",
    EventType.PROXIMA_ACAO_CRIADA: "Proxima acao criada",
    EventType.PROXIMA_ACAO_CONCLUIDA: "Proxima acao concluida",
    EventType.CATALOGO_COMPARTILHADO: "Catalogo compartilhado",
}


@dataclass(frozen=True)
class DomainEvent:
    tipo: str
    empresa: Any
    titulo: str = ""
    descricao: str = ""
    ator: Any = None
    entidade_tipo: str = ""
    entidade_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    cliente_id: int | None = None
    lead_id: int | None = None
    oportunidade_id: int | None = None
    pedido_id: int | None = None
    produto_id: int | None = None
    proxima_acao_id: int | None = None

    def titulo_final(self):
        return self.titulo or EVENT_TYPE_LABELS.get(self.tipo, self.tipo)
