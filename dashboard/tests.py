from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from billing.models import Assinatura, Plano
from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade, ProximaAcao
from dashboard.services import calcular_kpis_comerciais
from empresas.models import Empresa, EmpresaMembership
from services.onboarding import gerar_onboarding_empresa
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
        self.assertContains(response, "Onboarding operacional")
        self.assertContains(response, "Pedidos do dia")
        self.assertContains(response, "Receita do mes")
        self.assertContains(response, "Produto A - 3")
        self.assertContains(response, "vendedor_a")
        self.assertNotContains(response, "Produto B")
        self.assertNotContains(response, "999")

    def test_dashboard_executivo_renderiza_blocos_principais(self):
        ProximaAcao.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            oportunidade=self.oportunidade_a,
            vendedor=self.vendedor_a,
            descricao="Revisar proposta executiva",
            data_prevista=timezone.localdate(),
        )
        self.client.force_login(self.vendedor_a)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visao executiva da operacao comercial")
        self.assertContains(response, "Plano atual")
        self.assertContains(response, "Limites de uso")
        self.assertContains(response, "Proximas acoes")
        self.assertContains(response, "Revisar proposta executiva")
        self.assertContains(response, "Automacoes comerciais")

    def test_dashboard_executivo_exibe_cta_upgrade_quando_limite_atingido(self):
        admin = User.objects.create_user("admin_dashboard", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=admin,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        plano = Plano.objects.create(
            codigo="dashboard-limite",
            nome="Dashboard Limite",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_vendedores=5,
            limite_clientes=5,
            limite_leads=5,
            limite_produtos=1,
            limite_oportunidades=5,
            limite_pedidos_mes=5,
            limite_recomendacoes_comerciais=10,
            permite_workspace_comercial=True,
        )
        Assinatura.objects.create(
            empresa=self.empresa_a,
            plano=plano,
            status=Assinatura.Status.ATIVA,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Limite atingido")
        self.assertContains(response, "Administrar")
        self.assertContains(response, reverse("billing:plano-admin", args=[self.empresa_a.id]))

    def test_dashboard_vendedor_nao_exibe_link_admin_de_plano(self):
        self.client.force_login(self.vendedor_a)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Pedidos")
        self.assertContains(response, "Automacoes")
        self.assertNotContains(response, reverse("billing:plano-admin", args=[self.empresa_a.id]))

    def test_dashboard_executivo_sem_dados_renderiza_empty_states(self):
        empresa_vazia = Empresa.objects.create(nome="Empresa Sem Dados")
        usuario_vazio = User.objects.create_user("admin_sem_dados", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=empresa_vazia,
            usuario=usuario_vazio,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        self.client.force_login(usuario_vazio)

        response = self.client.get(reverse("dashboard:empresa", args=[empresa_vazia.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum produto vendido no mes")
        self.assertContains(response, "Nenhuma receita confirmada no mes")
        self.assertContains(response, "Nenhuma proxima acao pendente")
        self.assertContains(response, "Nenhuma recomendação crítica no momento")

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


class OnboardingOperacionalTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Nova")
        self.outra_empresa = Empresa.objects.create(nome="Empresa Externa")
        self.admin = User.objects.create_user("admin_onboarding", password="senha-segura")
        self.vendedor = User.objects.create_user("vendedor_onboarding", password="senha-segura")
        self.outro_usuario = User.objects.create_user("outro_onboarding", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.outra_empresa,
            usuario=self.outro_usuario,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )

    def test_empresa_nova_sem_dados_tem_apenas_dados_empresa_concluido(self):
        onboarding = gerar_onboarding_empresa(self.empresa)

        self.assertEqual(onboarding["concluidas"], 1)
        self.assertEqual(onboarding["progresso"], 14)
        self.assertFalse(onboarding["empresa_ativada"])
        pendentes = [etapa.titulo for etapa in onboarding["etapas"] if not etapa.concluida]
        self.assertIn("Cadastrar primeiro vendedor", pendentes)
        self.assertIn("Cadastrar primeiro produto", pendentes)

    def test_progresso_parcial(self):
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.vendedor,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        Produto.objects.create(empresa=self.empresa, nome="Produto Inicial", preco="10.00")
        Lead.objects.create(empresa=self.empresa, nome="Lead Inicial")

        onboarding = gerar_onboarding_empresa(self.empresa)

        self.assertEqual(onboarding["concluidas"], 5)
        self.assertEqual(onboarding["progresso"], 71)
        self.assertFalse(onboarding["empresa_ativada"])

    def test_empresa_ativada(self):
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.vendedor,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        produto = Produto.objects.create(empresa=self.empresa, nome="Produto Inicial", preco="10.00")
        cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente Inicial")
        oportunidade = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            vendedor=self.vendedor,
            titulo="Primeira oportunidade",
        )
        ProximaAcao.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            oportunidade=oportunidade,
            vendedor=self.vendedor,
            descricao="Ligar para cliente",
            data_prevista=timezone.localdate(),
        )

        onboarding = gerar_onboarding_empresa(self.empresa)

        self.assertEqual(onboarding["concluidas"], onboarding["total"])
        self.assertEqual(onboarding["progresso"], 100)
        self.assertTrue(onboarding["empresa_ativada"])
        self.assertEqual(str(produto), "Produto Inicial")

    def test_isolamento_por_empresa(self):
        outro_cliente = Cliente.objects.create(empresa=self.outra_empresa, nome="Cliente Externo")
        outro_produto = Produto.objects.create(
            empresa=self.outra_empresa,
            nome="Produto Externo",
            preco="20.00",
        )
        Oportunidade.objects.create(
            empresa=self.outra_empresa,
            cliente=outro_cliente,
            vendedor=self.outro_usuario,
            titulo="Oportunidade externa",
        )

        onboarding = gerar_onboarding_empresa(self.empresa)
        texto = str(onboarding)

        self.assertEqual(onboarding["concluidas"], 1)
        self.assertNotIn("Produto Externo", texto)
        self.assertEqual(str(outro_produto), "Produto Externo")

    def test_dashboard_renderiza_ctas_e_estado_ativado(self):
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.vendedor,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        produto = Produto.objects.create(empresa=self.empresa, nome="Produto Inicial", preco="10.00")
        cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente Inicial")
        oportunidade = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            vendedor=self.vendedor,
            titulo="Primeira oportunidade",
        )
        ProximaAcao.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            oportunidade=oportunidade,
            vendedor=self.vendedor,
            descricao="Ligar para cliente",
            data_prevista=timezone.localdate(),
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Onboarding operacional")
        self.assertContains(response, "Progresso: 100%")
        self.assertContains(response, "Empresa ativada")
        self.assertContains(response, "Concluida")
        self.assertContains(response, "Compartilhar catalogo")
        self.assertNotContains(response, "Produto Externo")
        self.assertEqual(str(produto), "Produto Inicial")

    def test_dashboard_empresa_nova_renderiza_links_de_cta(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("catalogo:produto-list-create", args=[self.empresa.id]))
        self.assertContains(response, reverse("crm:cliente-create", args=[self.empresa.id]))
        self.assertContains(response, reverse("crm:oportunidade-create", args=[self.empresa.id]))
        self.assertContains(response, reverse("crm:proxima-acao-create", args=[self.empresa.id]))
        self.assertContains(response, reverse("billing:plano-admin", args=[self.empresa.id]))
