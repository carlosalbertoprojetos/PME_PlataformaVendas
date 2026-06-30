import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Produto
from empresas.models import Empresa, EmpresaMembership


class ProdutoTenantIsolationTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A")
        self.empresa_b = Empresa.objects.create(nome="Empresa B")

        self.admin_a = User.objects.create_user("admin_a", password="senha-segura")
        self.vendedor_a = User.objects.create_user("vendedor_a", password="senha-segura")
        self.admin_b = User.objects.create_user("admin_b", password="senha-segura")
        self.sem_empresa = User.objects.create_user("sem_empresa", password="senha-segura")

        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=self.admin_a,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=self.vendedor_a,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        EmpresaMembership.objects.create(
            empresa=self.empresa_b,
            usuario=self.admin_b,
            papel=EmpresaMembership.Papel.ADMIN,
        )

        self.produto_a = Produto.objects.create(
            empresa=self.empresa_a,
            nome="Produto A",
            preco="10.00",
        )
        self.produto_b = Produto.objects.create(
            empresa=self.empresa_b,
            nome="Produto B",
            preco="20.00",
        )

    def test_admin_lista_apenas_produtos_da_propria_empresa(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_a.id])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["id"], self.produto_a.id)

    def test_admin_nao_lista_produtos_de_outra_empresa(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_b.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_vendedor_nao_acessa_empresa_de_outro_tenant(self):
        self.client.force_login(self.vendedor_a)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_b.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_sem_empresa_nao_acessa_catalogo(self):
        self.client.force_login(self.sem_empresa)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_a.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_anonimo_recebe_403(self):
        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_a.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_produto_de_outra_empresa_retorna_404_mesmo_com_id_valido(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("catalogo:produto-detail", args=[self.empresa_a.id, self.produto_b.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_cria_produto_somente_na_empresa_do_path(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("catalogo:produto-list-create", args=[self.empresa_a.id]),
            data=json.dumps({"nome": "Produto Novo", "preco": "99.90"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        produto = Produto.objects.get(nome="Produto Novo")
        self.assertEqual(produto.empresa, self.empresa_a)

    def test_usuario_nao_cria_produto_em_empresa_sem_membership(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("catalogo:produto-list-create", args=[self.empresa_b.id]),
            data=json.dumps({"nome": "Produto Invasor", "preco": "99.90"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Produto.objects.filter(nome="Produto Invasor").exists())

    def test_membership_inativa_nao_autoriza_acesso(self):
        membership = EmpresaMembership.objects.get(
            empresa=self.empresa_a,
            usuario=self.admin_a,
        )
        membership.ativo = False
        membership.save(update_fields=["ativo"])
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa_a.id])
        )

        self.assertEqual(response.status_code, 403)
