from django.urls import path

from catalogo import views


app_name = "catalogo"

urlpatterns = [
    path(
        "empresas/<int:empresa_id>/produtos/",
        views.ProdutoListCreateView.as_view(),
        name="produto-list-create",
    ),
    path(
        "empresas/<int:empresa_id>/catalogo/compartilhar/",
        views.CatalogoCompartilharView.as_view(),
        name="catalogo-compartilhar",
    ),
    path(
        "empresas/<int:empresa_id>/produtos/<int:pk>/",
        views.ProdutoDetailView.as_view(),
        name="produto-detail",
    ),
]
