from django.views.generic import DetailView

from core.mixins import EmpresaScopedQuerysetMixin
from vendas.models import Pedido


class PedidoDetailView(EmpresaScopedQuerysetMixin, DetailView):
    model = Pedido
    template_name = "vendas/pedido_detail.html"
    context_object_name = "pedido"

    def get_queryset(self):
        return super().get_queryset().select_related("cliente", "vendedor").prefetch_related("itens__produto")
