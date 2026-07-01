from decimal import Decimal
from urllib.parse import unquote, urlparse

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalogo.models import Produto
from crm.models import Cliente, Oportunidade
from empresas.models import Empresa, EmpresaMembership
from vendas.models import Pedido, PedidoItem
from whatsapp.models import WhatsAppTemplateConfig
from whatsapp.services import (
    gerar_link_catalogo,
    gerar_link_cliente,
    gerar_link_follow_up,
    gerar_link_pedido,
    gerar_link_produto,
    gerar_link_recomendacao_whatsapp,
    gerar_mensagem_recomendacao_whatsapp,
    gerar_wa_me_link,
    telefone_whatsapp_valido,
)


class WhatsAppLinkTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa = Empresa.objects.create(nome="Empresa A")
        self.outra_empresa = Empresa.objects.create(nome="Empresa B")
        self.usuario = User.objects.create_user("vendedor", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            papel=EmpresaMembership.Papel.VENDEDOR,
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nome="Cliente A",
            telefone="(11) 99999-0000",
        )
        self.produto = Produto.objects.create(
            empresa=self.empresa,
            nome="Produto A",
            preco=Decimal("19.90"),
        )
        self.pedido = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total=Decimal("39.80"),
        )
        self.pedido_pendente = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.PENDENTE,
            valor_total=Decimal("59.70"),
        )
        self.oportunidade = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            titulo="Oportunidade A",
            valor_estimado=Decimal("1200.00"),
        )
        PedidoItem.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=2,
            preco_unitario=Decimal("19.90"),
        )
        self.config = WhatsAppTemplateConfig.objects.create(
            empresa=self.empresa,
            catalogo="Catalogo da {empresa_nome}: {catalogo_url}",
            produto="Produto {produto_nome} custa {produto_preco}: {produto_url}",
            pedido="Pedido {pedido_id} de {cliente_nome}: {pedido_total}",
            cliente="Ola {cliente_nome}, tudo bem?",
            follow_up="Follow-up com {cliente_nome}",
        )

    def test_gerar_wa_me_link_sanitiza_telefone_e_codifica_texto(self):
        link = gerar_wa_me_link("Ola Cliente A!", "+55 (11) 99999-0000")

        self.assertTrue(link.startswith("https://wa.me/5511999990000?text="))
        self.assertIn("Ola Cliente A!", unquote(link))

    def test_recomendacao_whatsapp_nao_gera_link_para_telefone_invalido(self):
        link = gerar_link_recomendacao_whatsapp(
            {
                "tipo": "cliente_sem_recompra",
                "cliente": self.cliente,
                "motivo": "cliente sem recompra",
            },
            telefone="abc",
        )

        self.assertFalse(telefone_whatsapp_valido("abc"))
        self.assertEqual(link, "")

    def test_recomendacao_whatsapp_gera_link_wa_me_codificado(self):
        link = gerar_link_recomendacao_whatsapp(
            {
                "tipo": "cliente_sem_recompra",
                "cliente": self.cliente,
                "motivo": "cliente sem pedido confirmado nos ultimos 45 dias",
            }
        )

        self.assertTrue(link.startswith("https://wa.me/11999990000?text="))
        self.assertIn("Cliente A", unquote(urlparse(link).query))
        self.assertIn("45 dias", unquote(urlparse(link).query))

    def test_mensagens_por_tipo_de_recomendacao(self):
        cenarios = [
            (
                {
                    "tipo": "cliente_sem_recompra",
                    "cliente": self.cliente,
                    "motivo": "sem compra recente",
                },
                "Sentimos sua falta",
            ),
            (
                {
                    "tipo": "follow_up",
                    "cliente": self.cliente,
                    "oportunidade": self.oportunidade,
                    "motivo": "oportunidade parada",
                },
                "dar continuidade",
            ),
            (
                {
                    "tipo": "pedido_pendente",
                    "cliente": self.cliente,
                    "pedido": self.pedido_pendente,
                    "motivo": "pedido ainda pendente",
                },
                "esta pendente",
            ),
            (
                {
                    "tipo": "produto_recomendado",
                    "cliente": self.cliente,
                    "produto_nome": self.produto.nome,
                    "motivo": "produto recomendado para recompra",
                },
                "recomendacao comercial",
            ),
            (
                {
                    "tipo": "alerta_oportunidade_quente",
                    "cliente": self.cliente,
                    "oportunidade": self.oportunidade,
                    "motivo": "score alto",
                },
                "boa oportunidade",
            ),
        ]

        for recomendacao, trecho in cenarios:
            with self.subTest(tipo=recomendacao["tipo"]):
                mensagem = gerar_mensagem_recomendacao_whatsapp(recomendacao)
                self.assertIn("Cliente A", mensagem)
                self.assertIn(trecho, mensagem)

    def test_recomendacao_whatsapp_usa_apenas_cliente_da_recomendacao(self):
        cliente_outra_empresa = Cliente.objects.create(
            empresa=self.outra_empresa,
            nome="Cliente B",
            telefone="(21) 97777-0000",
        )

        link = gerar_link_recomendacao_whatsapp(
            {
                "tipo": "cliente_sem_recompra",
                "cliente": self.cliente,
                "motivo": "sem recompra",
            }
        )

        mensagem = unquote(urlparse(link).query)
        self.assertIn("Cliente A", mensagem)
        self.assertNotIn(cliente_outra_empresa.nome, mensagem)
        self.assertIn("wa.me/11999990000", link)

    def test_gerar_link_catalogo_usa_template_da_empresa(self):
        request = self.factory.get("/")

        link = gerar_link_catalogo(request, self.empresa)

        mensagem = unquote(urlparse(link).query)
        self.assertIn("Catalogo da Empresa A", mensagem)
        self.assertIn(reverse("catalogo:produto-list-create", args=[self.empresa.id]), mensagem)

    def test_gerar_link_produto_usa_template_da_empresa(self):
        request = self.factory.get("/")

        link = gerar_link_produto(request, self.produto)

        mensagem = unquote(urlparse(link).query)
        self.assertIn("Produto Produto A custa 19.90", mensagem)
        self.assertIn(reverse("catalogo:produto-detail", args=[self.empresa.id, self.produto.id]), mensagem)

    def test_gerar_link_pedido_usa_cliente_e_total(self):
        link = gerar_link_pedido(self.pedido)

        self.assertIn("wa.me/11999990000", link)
        mensagem = unquote(urlparse(link).query)
        self.assertIn(f"Pedido {self.pedido.id} de Cliente A: 39.80", mensagem)

    def test_gerar_links_cliente_e_follow_up(self):
        cliente_link = gerar_link_cliente(self.cliente)
        follow_up_link = gerar_link_follow_up(self.cliente)

        self.assertIn("wa.me/11999990000", cliente_link)
        self.assertIn("Ola Cliente A", unquote(urlparse(cliente_link).query))
        self.assertIn("Follow-up com Cliente A", unquote(urlparse(follow_up_link).query))

    def test_catalogo_renderiza_botao_de_compartilhamento(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("catalogo:produto-list-create", args=[self.empresa.id]),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compartilhar catalogo")
        self.assertContains(response, "Compartilhar produto")
        self.assertContains(response, reverse("catalogo:catalogo-compartilhar", args=[self.empresa.id]))

    def test_compartilhar_catalogo_registra_evento_apenas_por_post(self):
        self.client.force_login(self.usuario)
        url = reverse("catalogo:catalogo-compartilhar", args=[self.empresa.id])

        get_response = self.client.get(url)
        post_response = self.client.post(url)

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(post_response.status_code, 302)
        self.assertIn("wa.me", post_response["Location"])

    def test_produto_renderiza_botao_de_compartilhamento(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("catalogo:produto-detail", args=[self.empresa.id, self.produto.id]),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compartilhar produto")
        self.assertContains(response, "wa.me")

    def test_cliente_renderiza_mensagens_prontas(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("crm:cliente-detail", args=[self.empresa.id, self.cliente.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mensagem para cliente")
        self.assertContains(response, "Mensagem de follow-up")
        self.assertContains(response, "wa.me")

    def test_pedido_renderiza_botao_de_compartilhamento(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("vendas:pedido-detail", args=[self.empresa.id, self.pedido.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compartilhar pedido")
        self.assertContains(response, "wa.me")

    def test_pedido_de_outra_empresa_retorna_403_no_tenant_sem_membership(self):
        pedido_outra_empresa = Pedido.objects.create(
            empresa=self.outra_empresa,
            cliente=Cliente.objects.create(empresa=self.outra_empresa, nome="Cliente B"),
            vendedor=User.objects.create_user("outro", password="senha-segura"),
            status=Pedido.Status.CONFIRMADO,
            valor_total=Decimal("10.00"),
        )
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse("vendas:pedido-detail", args=[self.outra_empresa.id, pedido_outra_empresa.id])
        )

        self.assertEqual(response.status_code, 403)
