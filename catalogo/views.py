import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from catalogo.models import Produto
from billing.services import pode_criar_recurso
from core.mixins import EmpresaRequiredMixin, EmpresaScopedQuerysetMixin
from eventos.dispatcher import dispatch_event
from eventos.events import DomainEvent, EventType
from whatsapp.services import gerar_link_catalogo, gerar_link_produto


def serialize_produto(produto):
    return {
        "id": produto.id,
        "empresa_id": produto.empresa_id,
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco": str(produto.preco),
        "ativo": produto.ativo,
    }


class ProdutoListCreateView(EmpresaRequiredMixin, View):
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        produtos = Produto.objects.da_empresa(self.empresa).ativos()
        if request.headers.get("Accept", "").startswith("text/html"):
            return render(
                request,
                "catalogo/produto_list.html",
                {
                    "empresa": self.empresa,
                    "produtos": produtos,
                    "whatsapp_catalogo_url": reverse_catalogo_compartilhar(self.empresa),
                },
            )
        return JsonResponse({"results": [serialize_produto(produto) for produto in produtos]})

    def post(self, request, *args, **kwargs):
        permitido, limite = pode_criar_recurso(self.empresa, "produtos")
        if not permitido:
            return JsonResponse({"error": limite.aviso}, status=403)

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            preco = Decimal(str(payload.get("preco", "")))
        except (json.JSONDecodeError, InvalidOperation):
            return JsonResponse({"error": "Payload invalido."}, status=400)

        produto = Produto(
            empresa=self.empresa,
            nome=payload.get("nome", "").strip(),
            descricao=payload.get("descricao", "").strip(),
            preco=preco,
            ativo=payload.get("ativo", True),
        )

        try:
            produto.full_clean()
            produto.save()
        except ValidationError as exc:
            return JsonResponse({"errors": exc.message_dict}, status=400)

        return JsonResponse(serialize_produto(produto), status=201)


def reverse_catalogo_compartilhar(empresa):
    from django.urls import reverse

    return reverse("catalogo:catalogo-compartilhar", args=[empresa.id])


class CatalogoCompartilharView(EmpresaRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        dispatch_event(
            DomainEvent(
                tipo=EventType.CATALOGO_COMPARTILHADO,
                empresa=self.empresa,
                ator=request.user,
                descricao=f"Catalogo da empresa {self.empresa.nome} compartilhado.",
                entidade_tipo="empresa",
                entidade_id=self.empresa.id,
                payload={"canal": "whatsapp"},
            )
        )
        return redirect(gerar_link_catalogo(request, self.empresa))


class ProdutoDetailView(EmpresaScopedQuerysetMixin, SingleObjectMixin, View):
    model = Produto
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        produto = self.get_object()
        if request.headers.get("Accept", "").startswith("text/html"):
            return render(
                request,
                "catalogo/produto_detail.html",
                {
                    "empresa": self.empresa,
                    "produto": produto,
                    "whatsapp_produto_url": gerar_link_produto(request, produto),
                },
            )
        return JsonResponse(serialize_produto(produto))
