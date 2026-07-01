from django.urls import path

from crm import views


app_name = "crm"

urlpatterns = [
    path("workspace/<int:cliente_id>/", views.ClienteWorkspaceView.as_view(), name="workspace-cliente"),
    path("workspace/oportunidade/<int:id>/", views.OportunidadeWorkspaceView.as_view(), name="workspace-oportunidade"),
    path("empresas/<int:empresa_id>/crm/clientes/", views.ClienteListView.as_view(), name="cliente-list"),
    path("empresas/<int:empresa_id>/crm/clientes/novo/", views.ClienteCreateView.as_view(), name="cliente-create"),
    path("empresas/<int:empresa_id>/crm/clientes/<int:pk>/", views.ClienteDetailView.as_view(), name="cliente-detail"),
    path("empresas/<int:empresa_id>/crm/leads/", views.LeadListView.as_view(), name="lead-list"),
    path("empresas/<int:empresa_id>/crm/leads/novo/", views.LeadCreateView.as_view(), name="lead-create"),
    path("empresas/<int:empresa_id>/crm/leads/<int:pk>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("empresas/<int:empresa_id>/crm/leads/<int:pk>/converter/", views.LeadConvertView.as_view(), name="lead-convert"),
    path("empresas/<int:empresa_id>/crm/oportunidades/", views.OportunidadeListView.as_view(), name="oportunidade-list"),
    path("empresas/<int:empresa_id>/crm/oportunidades/novo/", views.OportunidadeCreateView.as_view(), name="oportunidade-create"),
    path("empresas/<int:empresa_id>/crm/oportunidades/<int:pk>/", views.OportunidadeDetailView.as_view(), name="oportunidade-detail"),
    path("empresas/<int:empresa_id>/crm/historicos/novo/", views.HistoricoContatoCreateView.as_view(), name="historico-create"),
    path("empresas/<int:empresa_id>/crm/proximas-acoes/", views.ProximaAcaoListView.as_view(), name="proxima-acao-list"),
    path("empresas/<int:empresa_id>/crm/proximas-acoes/novo/", views.ProximaAcaoCreateView.as_view(), name="proxima-acao-create"),
    path("empresas/<int:empresa_id>/crm/proximas-acoes/<int:pk>/editar/", views.ProximaAcaoUpdateView.as_view(), name="proxima-acao-update"),
    path("empresas/<int:empresa_id>/crm/proximas-acoes/<int:pk>/concluir/", views.ProximaAcaoConcluirView.as_view(), name="proxima-acao-concluir"),
]
