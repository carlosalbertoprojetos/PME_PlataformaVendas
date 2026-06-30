from django.urls import path

from vendas import views


app_name = "vendas"

urlpatterns = [
    path("empresas/<int:empresa_id>/pedidos/<int:pk>/", views.PedidoDetailView.as_view(), name="pedido-detail"),
]
