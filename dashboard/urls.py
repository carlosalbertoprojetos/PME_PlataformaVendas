from django.urls import path

from dashboard import views


app_name = "dashboard"

urlpatterns = [
    path("empresas/<int:empresa_id>/dashboard/", views.DashboardEmpresaView.as_view(), name="empresa"),
    path("empresas/<int:empresa_id>/dashboard/vendedor/", views.DashboardVendedorView.as_view(), name="vendedor"),
    path(
        "empresas/<int:empresa_id>/dashboard/recomendacoes/",
        views.RecomendacoesComerciaisView.as_view(),
        name="recomendacoes",
    ),
]
