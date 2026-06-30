from django.urls import include, path


urlpatterns = [
    path("contas/", include("django.contrib.auth.urls")),
    path("", include("dashboard.urls")),
    path("", include("billing.urls")),
    path("", include("catalogo.urls")),
    path("", include("crm.urls")),
    path("", include("vendas.urls")),
]
