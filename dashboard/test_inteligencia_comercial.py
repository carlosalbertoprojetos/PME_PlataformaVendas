from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Produto
from crm.models import Cliente, HistoricoContato, Oportunidade, ProximaAcao
from empresas.models import Empresa, EmpresaMembership
from services.inteligencia_comercial import gerar_recomendacoes_comerciais
from vendas.models import Pedido, PedidoItem


class InteligenciaComercialTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa A")
        self.outra_empresa = Empresa.objects.create(nome="Empresa B")
        self.usuario = User.objects.create_user("vendedor_a", password="senha-segura")
        self.outro_usuario = User.objects.create_user("vendedor_b", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        EmpresaMembership.objects.create(
            empresa=self.outra_empresa,
            usuario=self.outro_usuario,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente A",
            telefone="(11) 99999-0000",
        )
        self.cliente_antigo = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente Antigo",
            telefone="(11) 98888-0000",
        )
        self.cliente_outra_empresa = Cliente.objects.create(
            empresa=self.outra_empresa,
            nome="Cliente B",
        )
        self.produto = Produto.objects.create(
            empresa=self.empresa,
            nome="Produto Forte",
            preco=Decimal("10.00"),
        )
        self.produto_outra_empresa = Produto.objects.create(
            empresa=self.outra_empresa,
            nome="Produto Externo",
            preco=Decimal("99.00"),
        )
        self.oportunidade = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            titulo="Oportunidade Quente",
            valor_estimado=Decimal("1500.00"),
        )
        self.oportunidade.criado_em = timezone.now() - timedelta(days=10)
        self.oportunidade.save(update_fields=["criado_em"])
        HistoricoContato.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            resumo="Cliente pediu retorno.",
        )
        ProximaAcao.objects.create(
            empresa=self.empresa,
            oportunidade=self.oportunidade,
            vendedor=self.usuario,
            descricao="Enviar proposta",
            data_prevista=timezone.localdate() + timedelta(days=1),
        )
        self.oportunidade_sem_acao = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=self.cliente_antigo,
            vendedor=self.usuario,
            titulo="Oportunidade sem acao",
            valor_estimado=Decimal("300.00"),
        )
        self.oportunidade_sem_acao.criado_em = timezone.now() - timedelta(days=10)
        self.oportunidade_sem_acao.save(update_fields=["criado_em"])
        self.pedido = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total=Decimal("120.00"),
            criado_em=timezone.now(),
        )
        PedidoItem.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=12,
            preco_unitario=Decimal("10.00"),
        )
        self.pedido_antigo = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente_antigo,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total=Decimal("80.00"),
            criado_em=timezone.now() - timedelta(days=60),
        )
        PedidoItem.objects.create(
            pedido=self.pedido_antigo,
            produto=self.produto,
            quantidade=1,
            preco_unitario=Decimal("10.00"),
        )
        pedido_externo = Pedido.objects.create(
            empresa=self.outra_empresa,
            cliente=self.cliente_outra_empresa,
            vendedor=self.outro_usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total=Decimal("999.00"),
            criado_em=timezone.now(),
        )
        PedidoItem.objects.create(
            pedido=pedido_externo,
            produto=self.produto_outra_empresa,
            quantidade=50,
            preco_unitario=Decimal("99.00"),
        )

    def test_gera_score_de_oportunidade_com_motivo(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)

        score = next(
            item for item in recomendacoes["scores_oportunidade"]
            if item["titulo"] == "Oportunidade Quente"
        )
        self.assertGreaterEqual(score["score"], 80)
        self.assertIn("valor estimado acima de 1000", score["motivo"])
        self.assertIn("possui proxima acao pendente", score["motivo"])

    def test_identifica_produtos_alta_saida_e_risco_ruptura(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)

        self.assertEqual(recomendacoes["produtos_alta_saida"][0]["titulo"], "Produto Forte")
        self.assertIn("vendeu 12 unidades", recomendacoes["produtos_alta_saida"][0]["motivo"])
        self.assertEqual(recomendacoes["produtos_risco_ruptura"][0]["titulo"], "Produto Forte")
        self.assertIn("estoque ainda nao e controlado", recomendacoes["produtos_risco_ruptura"][0]["motivo"])

    def test_identifica_cliente_sem_recompra(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)

        clientes = [item["titulo"] for item in recomendacoes["clientes_sem_recompra"]]
        self.assertIn("Cliente Antigo", clientes)
        self.assertNotIn("Cliente A", clientes)

    def test_sugere_follow_up_sem_proxima_acao(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)

        sugestoes = [item["titulo"] for item in recomendacoes["sugestoes_follow_up"]]
        self.assertIn("Oportunidade sem acao", sugestoes)
        self.assertNotIn("Oportunidade Quente", sugestoes)

    def test_recomendacoes_nao_vazam_outro_tenant(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)
        texto = str(recomendacoes)

        self.assertNotIn("Produto Externo", texto)
        self.assertNotIn("Cliente B", texto)

    def test_recomendacoes_possuem_campos_acionaveis(self):
        recomendacoes = gerar_recomendacoes_comerciais(self.empresa)

        alerta = recomendacoes["alertas_comerciais"][0]

        self.assertIn("motivo", alerta)
        self.assertIn("prioridade", alerta)
        self.assertIn("entidade_relacionada", alerta)
        self.assertIn("acao_recomendada", alerta)
        self.assertIn("link_acao", alerta)
        self.assertTrue(alerta["link_acao"])
        self.assertTrue(alerta["acoes"])

    def test_dashboard_recomendacoes_renderiza_alertas(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:recomendacoes", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recomendacoes comerciais")
        self.assertContains(response, "Oportunidade Quente")
        self.assertContains(response, "Produto Forte")
        self.assertContains(response, "Cliente Antigo")
        self.assertContains(response, "Oportunidade sem acao")
        self.assertNotContains(response, "Produto Externo")

    def test_dashboard_empresa_renderiza_recomendacoes_acionaveis(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recomendacoes acionaveis")
        self.assertContains(response, "Oportunidade Quente")
        self.assertContains(response, "Motivo:")
        self.assertContains(response, "Prioridade:")
        self.assertContains(response, "Entidade relacionada:")
        self.assertContains(response, "Acao recomendada:")
        self.assertContains(response, "Abrir oportunidade")
        self.assertContains(response, "Enviar WhatsApp")
        self.assertContains(response, "https://wa.me/11999990000?text=")
        self.assertContains(
            response,
            reverse("crm:oportunidade-detail", args=[self.empresa.id, self.oportunidade.id]),
        )
        self.assertNotContains(response, "Produto Externo")

    def test_links_de_acao_incluem_cliente_pedido_produto_oportunidade_e_proxima_acao(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:recomendacoes", args=[self.empresa.id]))

        self.assertContains(
            response,
            reverse("crm:cliente-detail", args=[self.empresa.id, self.cliente_antigo.id]),
        )
        self.assertContains(
            response,
            reverse("vendas:pedido-detail", args=[self.empresa.id, self.pedido_antigo.id]),
        )
        self.assertContains(
            response,
            reverse("catalogo:produto-detail", args=[self.empresa.id, self.produto.id]),
        )
        self.assertContains(
            response,
            reverse("crm:oportunidade-detail", args=[self.empresa.id, self.oportunidade.id]),
        )
        self.assertContains(
            response,
            reverse("crm:proxima-acao-create", args=[self.empresa.id])
            + f"?cliente={self.cliente_antigo.id}&amp;oportunidade={self.oportunidade_sem_acao.id}",
        )

    def test_dashboard_empresa_nao_renderiza_recomendacoes_de_outra_empresa(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Produto Externo")
        self.assertNotContains(response, "Cliente B")

    def test_dashboard_nao_renderiza_whatsapp_com_telefone_invalido(self):
        Cliente.objects.da_empresa(self.empresa).update(telefone="sem telefone")
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recomendacoes acionaveis")
        self.assertNotContains(response, "Enviar WhatsApp")

    def test_dashboard_empresa_sem_recomendacoes_exibe_estado_vazio(self):
        empresa_vazia = Empresa.objects.create(nome="Empresa sem alertas")
        usuario_vazio = User.objects.create_user("vazio", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=empresa_vazia,
            usuario=usuario_vazio,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        self.client.force_login(usuario_vazio)

        response = self.client.get(reverse("dashboard:empresa", args=[empresa_vazia.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhuma recomendação crítica no momento")

    def test_dashboard_recomendacoes_bloqueia_empresa_sem_membership(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:recomendacoes", args=[self.outra_empresa.id]))

        self.assertEqual(response.status_code, 403)
