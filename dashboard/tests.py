from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Produto
from crm.models import Cliente, Oportunidade
from dashboard.services import calcular_kpis_comerciais
from empresas.models import Empresa, EmpresaMembership
from vendas.models import Pedido, PedidoItem


class DashboardKpiTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A")
        self.empresa_b = Empresa.objects.create(nome="Empresa B")
        self.vendedor_a = User.objects.create_user("vendedor_a", password="senha-segura")
        self.vendedor_b = User.objects.create_user("vendedor_b", password="senha-segura")
        self.sem_empresa = User.objects.create_user("sem_empresa", password="senha-segura")

        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=self.vendedor_a,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        EmpresaMembership.objects.create(
            empresa=self.empresa_b,
            usuario=self.vendedor_b,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )

        self.cliente_a = Cliente.objects.create(empresa=self.empresa_a, nome="Cliente A")
        self.cliente_b = Cliente.objects.create(empresa=self.empresa_b, nome="Cliente B")
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
        self.oportunidade_a = Oportunidade.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=self.vendedor_a,
            titulo="Oportunidade A",
            valor_estimado="1000.00",
        )
        Oportunidade.objects.create(
            empresa=self.empresa_b,
            cliente=self.cliente_b,
            vendedor=self.vendedor_b,
            titulo="Oportunidade B",
            valor_estimado="500.00",
        )

        self.pedido_confirmado = Pedido.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            oportunidade=self.oportunidade_a,
            vendedor=self.vendedor_a,
            status=Pedido.Status.CONFIRMADO,
            valor_total="100.00",
            criado_em=timezone.now(),
        )
        PedidoItem.objects.create(
            pedido=self.pedido_confirmado,
            produto=self.produto_a,
            quantidade=3,
            preco_unitario="10.00",
        )
        Pedido.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=self.vendedor_a,
            status=Pedido.Status.CONFIRMADO,
            valor_total="200.00",
            criado_em=timezone.now(),
        )
        Pedido.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=self.vendedor_a,
            status=Pedido.Status.PENDENTE,
            valor_total="50.00",
            criado_em=timezone.now(),
        )
        pedido_b = Pedido.objects.create(
            empresa=self.empresa_b,
            cliente=self.cliente_b,
            vendedor=self.vendedor_b,
            status=Pedido.Status.CONFIRMADO,
            valor_total="999.00",
            criado_em=timezone.now(),
        )
        PedidoItem.objects.create(
            pedido=pedido_b,
            produto=self.produto_b,
            quantidade=9,
            preco_unitario="20.00",
        )

    def test_servico_calcula_kpis_da_empresa_sem_vazar_outro_tenant(self):
        kpis = calcular_kpis_comerciais(self.empresa_a)

        self.assertEqual(kpis["pedidos_do_dia"], 2)
        self.assertEqual(kpis["receita_do_mes"], Decimal("300"))
        self.assertEqual(kpis["ticket_medio"], Decimal("150"))
        self.assertEqual(kpis["pedidos_pendentes"], 1)
        self.assertEqual(kpis["clientes_ativos"], 1)
        self.assertEqual(kpis["oportunidades_abertas"], 1)
        self.assertEqual(kpis["produtos_mais_vendidos"][0]["produto__nome"], "Produto A")
        self.assertEqual(kpis["produtos_mais_vendidos"][0]["quantidade"], 3)
        self.assertEqual(kpis["vendedores_maior_receita"][0]["vendedor__username"], "vendedor_a")

    def test_dashboard_empresa_renderiza_metricas(self):
        self.client.force_login(self.vendedor_a)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard empresa")
        self.assertContains(response, "Pedidos do dia")
        self.assertContains(response, "Receita do mes")
        self.assertContains(response, "Produto A - 3")
        self.assertContains(response, "vendedor_a")
        self.assertNotContains(response, "Produto B")
        self.assertNotContains(response, "999")

    def test_dashboard_vendedor_renderiza_apenas_recorte_do_usuario(self):
        outro_vendedor = User.objects.create_user("outro_vendedor", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=outro_vendedor,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        Pedido.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=outro_vendedor,
            status=Pedido.Status.CONFIRMADO,
            valor_total="700.00",
            criado_em=timezone.now(),
        )
        self.client.force_login(self.vendedor_a)

        response = self.client.get(reverse("dashboard:vendedor", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard vendedor")
        self.assertContains(response, "300")
        self.assertNotContains(response, "700")

    def test_usuario_sem_membership_nao_acessa_dashboard_empresa(self):
        self.client.force_login(self.sem_empresa)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 403)

    def test_usuario_de_outra_empresa_nao_acessa_dashboard(self):
        self.client.force_login(self.vendedor_a)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_b.id]))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_anonimo_retorna_403(self):
        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 403)
