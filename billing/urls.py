from django.urls import path

from billing import views


app_name = "billing"

urlpatterns = [
    path("empresas/<int:empresa_id>/plano/", views.PlanoAdminView.as_view(), name="plano-admin"),
]
