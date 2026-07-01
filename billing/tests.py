import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from billing.middleware import BillingLimitMiddleware
from billing.models import Assinatura, Plano
from billing.services import (
    assinatura_bloqueada,
    avaliar_limites,
    avaliar_limites_leve,
    get_assinatura_empresa,
    pode_criar_recurso,
)
from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade
from empresas.models import Empresa, EmpresaMembership
from vendas.models import Pedido


class BillingTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa A")
        self.outra_empresa = Empresa.objects.create(nome="Empresa B")
        self.usuario = User.objects.create_user("admin_a", password="senha-segura")
        self.vendedor = User.objects.create_user("vendedor_a", password="senha-segura")
        self.outro_usuario = User.objects.create_user("admin_b", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.vendedor,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        EmpresaMembership.objects.create(
            empresa=self.outra_empresa,
            usuario=self.outro_usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )

    def test_planos_iniciais_existem(self):
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.START).exists())
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.GROWTH).exists())
        self.assertTrue(Plano.objects.filter(codigo=Plano.Codigo.PRO).exists())

    def test_get_assinatura_empresa_cria_trial_start(self):
        assinatura = get_assinatura_empresa(self.empresa)

        self.assertEqual(assinatura.empresa, self.empresa)
        self.assertEqual(assinatura.plano.codigo, Plano.Codigo.START)
        self.assertEqual(assinatura.status, Assinatura.Status.TRIAL)

    def test_assinatura_suspensa_bloqueia_uso(self):
        assinatura = get_assinatura_empresa(self.empresa)
        assinatura.status = Assinatura.Status.SUSPENSA
        assinatura.save(update_fields=["status"])

        bloqueada, assinatura_resultado = assinatura_bloqueada(self.empresa)

        self.assertTrue(bloqueada)
        self.assertEqual(assinatura_resultado, assinatura)

    def test_assinatura_expirada_suspensa_exibe_bloqueio_suave(self):
        assinatura = get_assinatura_empresa(self.empresa)
        assinatura.status = Assinatura.Status.SUSPENSA
        assinatura.save(update_fields=["status"])
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("billing:plano-admin", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Assinatura Suspensa")
        self.assertContains(response, "Fazer upgrade do plano")

    def test_avaliar_limites_calcula_uso_por_empresa(self):
        plano = Plano.objects.create(
            codigo="teste-limites",
            nome="Teste Limites",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=1,
            limite_vendedores=1,
            limite_clientes=1,
            limite_produtos=2,
            limite_pedidos_mes=10,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        Produto.objects.create(empresa=self.empresa, nome="Produto A", preco="10.00")
        Produto.objects.create(empresa=self.outra_empresa, nome="Produto B", preco="20.00")

        limites = avaliar_limites(self.empresa)

        self.assertTrue(limites["usuarios"].atingido)
        self.assertTrue(limites["vendedores"].atingido)
        self.assertTrue(limites["clientes"].atingido)
        self.assertFalse(limites["produtos"].atingido)
        self.assertEqual(limites["produtos"].usado, 1)

    def test_avaliar_limites_inclui_recursos_saas(self):
        plano = Plano.objects.create(
            codigo="teste-saas",
            nome="Teste SaaS",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_vendedores=5,
            limite_clientes=5,
            limite_leads=1,
            limite_produtos=5,
            limite_oportunidades=1,
            limite_pedidos_mes=5,
            limite_recomendacoes_comerciais=1,
            permite_workspace_comercial=True,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        Lead.objects.create(empresa=self.empresa, nome="Lead A")
        Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            vendedor=self.usuario,
            titulo="Oportunidade A",
        )

        limites = avaliar_limites(self.empresa)

        self.assertIn("leads", limites)
        self.assertIn("oportunidades", limites)
        self.assertIn("recomendacoes_comerciais", limites)
        self.assertIn("workspace_comercial", limites)
        self.assertTrue(limites["leads"].atingido)
        self.assertTrue(limites["oportunidades"].atingido)

    def test_pode_criar_recurso_retorna_false_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-clientes",
            nome="Teste Clientes",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=1,
            limite_produtos=5,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")

        permitido, limite = pode_criar_recurso(self.empresa, "clientes")

        self.assertFalse(permitido)
        self.assertIn("Limite de clientes atingido", limite.aviso)

    def test_aviso_antes_do_limite_e_cta_upgrade(self):
        plano = Plano.objects.create(
            codigo="teste-aviso",
            nome="Teste Aviso",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_vendedores=5,
            limite_clientes=5,
            limite_leads=5,
            limite_produtos=5,
            limite_oportunidades=5,
            limite_pedidos_mes=5,
            limite_recomendacoes_comerciais=10,
            permite_workspace_comercial=True,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        for indice in range(4):
            Cliente.objects.create(empresa=self.empresa, nome=f"Cliente {indice}")

        limite = avaliar_limites(self.empresa)["clientes"]

        self.assertFalse(limite.atingido)
        self.assertTrue(limite.proximo_limite)
        self.assertIn("proximo", limite.aviso)
        self.assertEqual(limite.cta_upgrade, "Fazer upgrade do plano")

    def test_bloqueia_criacao_de_produto_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-produtos",
            nome="Teste Produtos",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=5,
            limite_produtos=1,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Produto.objects.create(empresa=self.empresa, nome="Produto A", preco="10.00")
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("catalogo:produto-list-create", args=[self.empresa.id]),
            data=json.dumps({"nome": "Produto Novo", "preco": "20.00"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Produto.objects.filter(nome="Produto Novo").exists())

    def test_bloqueia_criacao_de_cliente_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-clientes-view",
            nome="Teste Clientes View",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_clientes=1,
            limite_produtos=5,
            limite_pedidos_mes=5,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("crm:cliente-create", args=[self.empresa.id]),
            data={
                "nome": "Cliente Novo",
                "email": "",
                "telefone": "",
                "documento": "",
                "observacoes": "",
                "ativo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Limite de clientes atingido")
        self.assertContains(response, "Faça upgrade do plano")
        self.assertFalse(Cliente.objects.filter(nome="Cliente Novo").exists())

    def test_bloqueia_criacao_de_lead_e_oportunidade_quando_limite_atingido(self):
        plano = Plano.objects.create(
            codigo="teste-leads-oportunidades",
            nome="Teste Leads Oportunidades",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_vendedores=5,
            limite_clientes=5,
            limite_leads=1,
            limite_produtos=5,
            limite_oportunidades=1,
            limite_pedidos_mes=5,
            limite_recomendacoes_comerciais=10,
            permite_workspace_comercial=True,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        Lead.objects.create(empresa=self.empresa, nome="Lead A")
        Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=cliente,
            vendedor=self.usuario,
            titulo="Oportunidade A",
        )
        self.client.force_login(self.usuario)

        lead_response = self.client.post(
            reverse("crm:lead-create", args=[self.empresa.id]),
            data={"nome": "Lead Novo", "email": "", "telefone": "", "origem": "", "status": Lead.Status.NOVO},
        )
        oportunidade_response = self.client.post(
            reverse("crm:oportunidade-create", args=[self.empresa.id]),
            data={
                "cliente": cliente.id,
                "vendedor": self.usuario.id,
                "titulo": "Oportunidade Nova",
                "valor_estimado": "100.00",
                "status": Oportunidade.Status.ABERTA,
            },
        )

        self.assertEqual(lead_response.status_code, 200)
        self.assertContains(lead_response, "Limite de leads atingido")
        self.assertEqual(oportunidade_response.status_code, 200)
        self.assertContains(oportunidade_response, "Limite de oportunidades atingido")

    def test_middleware_anexa_limites_para_empresa_autorizada(self):
        request = RequestFactory().get(reverse("billing:plano-admin", args=[self.empresa.id]))
        request.user = self.usuario
        middleware = BillingLimitMiddleware(lambda req: None)

        middleware(request)
        middleware.process_view(request, None, (), {"empresa_id": self.empresa.id})

        self.assertIn("clientes", request.billing_limites)
        self.assertIsNone(request.billing_bloqueio)

    def test_middleware_usa_limites_leves_sem_recalcular_recomendacoes(self):
        limites = avaliar_limites_leve(self.empresa)

        self.assertIn("recomendacoes_comerciais", limites)
        self.assertEqual(limites["recomendacoes_comerciais"].usado, 0)

    def test_middleware_nao_cria_assinatura_para_empresa_sem_acesso(self):
        request = RequestFactory().get(reverse("billing:plano-admin", args=[self.outra_empresa.id]))
        request.user = self.usuario
        middleware = BillingLimitMiddleware(lambda req: None)

        middleware(request)
        middleware.process_view(request, None, (), {"empresa_id": self.outra_empresa.id})

        self.assertEqual(request.billing_limites, {})
        self.assertFalse(Assinatura.objects.filter(empresa=self.outra_empresa).exists())

    def test_workspace_comercial_indisponivel_no_plano_retorna_404(self):
        plano = Plano.objects.create(
            codigo="teste-sem-workspace",
            nome="Teste Sem Workspace",
            preco_mensal=Decimal("1.00"),
            limite_usuarios=5,
            limite_vendedores=5,
            limite_clientes=5,
            limite_leads=5,
            limite_produtos=5,
            limite_oportunidades=5,
            limite_pedidos_mes=5,
            limite_recomendacoes_comerciais=10,
            permite_workspace_comercial=False,
        )
        Assinatura.objects.create(empresa=self.empresa, plano=plano, status=Assinatura.Status.ATIVA)
        cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("crm:workspace-cliente", args=[cliente.id]))

        self.assertEqual(response.status_code, 404)

    def test_tela_admin_de_plano_renderiza_e_atualiza_assinatura(self):
        growth = Plano.objects.get(codigo=Plano.Codigo.GROWTH)
        get_assinatura_empresa(self.empresa)
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("billing:plano-admin", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plano da empresa")
        self.assertContains(response, "Start")

        response = self.client.post(
            reverse("billing:plano-admin", args=[self.empresa.id]),
            data={
                "plano": growth.id,
                "status": Assinatura.Status.ATIVA,
                "fim_trial_em": "",
                "gateway_preferido": "asaas",
            },
        )

        self.assertEqual(response.status_code, 302)
        assinatura = Assinatura.objects.get(empresa=self.empresa)
        self.assertEqual(assinatura.plano, growth)
        self.assertEqual(assinatura.status, Assinatura.Status.ATIVA)
        self.assertEqual(assinatura.gateway_preferido, "asaas")

    def test_vendedor_nao_acessa_admin_de_plano(self):
        self.client.force_login(self.vendedor)

        get_response = self.client.get(reverse("billing:plano-admin", args=[self.empresa.id]))
        post_response = self.client.post(
            reverse("billing:plano-admin", args=[self.empresa.id]),
            data={
                "plano": Plano.objects.get(codigo=Plano.Codigo.PRO).id,
                "status": Assinatura.Status.ATIVA,
                "fim_trial_em": "",
                "gateway_preferido": "",
            },
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)

    def test_upgrade_e_downgrade_logico_sem_gateway(self):
        start = Plano.objects.get(codigo=Plano.Codigo.START)
        pro = Plano.objects.get(codigo=Plano.Codigo.PRO)
        assinatura = get_assinatura_empresa(self.empresa)
        self.assertEqual(assinatura.plano, start)
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse("billing:plano-admin", args=[self.empresa.id]),
            data={
                "plano": pro.id,
                "status": Assinatura.Status.ATIVA,
                "fim_trial_em": "",
                "gateway_preferido": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.plano, pro)

        response = self.client.post(
            reverse("billing:plano-admin", args=[self.empresa.id]),
            data={
                "plano": start.id,
                "status": Assinatura.Status.ATIVA,
                "fim_trial_em": "",
                "gateway_preferido": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        assinatura.refresh_from_db()
        self.assertEqual(assinatura.plano, start)
