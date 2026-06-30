from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Produto
from crm.models import Cliente, HistoricoContato, Lead, Oportunidade, ProximaAcao
from empresas.models import Empresa, EmpresaMembership


class CrmLeveTests(TestCase):
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

        self.cliente_a = Cliente.objects.create(
            empresa=self.empresa_a,
            nome="Cliente A",
            email="cliente-a@example.com",
        )
        self.cliente_b = Cliente.objects.create(
            empresa=self.empresa_b,
            nome="Cliente B",
            email="cliente-b@example.com",
        )
        self.lead_a = Lead.objects.create(
            empresa=self.empresa_a,
            nome="Lead A",
            email="lead-a@example.com",
        )
        self.lead_b = Lead.objects.create(
            empresa=self.empresa_b,
            nome="Lead B",
            email="lead-b@example.com",
        )
        self.oportunidade_a = Oportunidade.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=self.vendedor_a,
            titulo="Oportunidade A",
            valor_estimado="1000.00",
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

    def test_lista_clientes_somente_da_empresa(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:cliente-list", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente A")
        self.assertNotContains(response, "Cliente B")

    def test_usuario_sem_membership_recebe_403(self):
        self.client.force_login(self.sem_empresa)

        response = self.client.get(reverse("crm:cliente-list", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 403)

    def test_admin_nao_acessa_empresa_de_outro_tenant(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:cliente-list", args=[self.empresa_b.id]))

        self.assertEqual(response.status_code, 403)

    def test_objeto_de_outra_empresa_retorna_404_no_tenant_atual(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("crm:cliente-detail", args=[self.empresa_a.id, self.cliente_b.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_cadastra_cliente_na_empresa_do_path(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:cliente-create", args=[self.empresa_a.id]),
            data={
                "nome": "Cliente Novo",
                "email": "novo@example.com",
                "telefone": "11999999999",
                "documento": "",
                "observacoes": "",
                "ativo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        cliente = Cliente.objects.get(nome="Cliente Novo")
        self.assertEqual(cliente.empresa, self.empresa_a)

    def test_cadastra_lead_na_empresa_do_path(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:lead-create", args=[self.empresa_a.id]),
            data={
                "nome": "Lead Novo",
                "email": "lead-novo@example.com",
                "telefone": "",
                "origem": "site",
                "status": Lead.Status.NOVO,
            },
        )

        self.assertEqual(response.status_code, 302)
        lead = Lead.objects.get(nome="Lead Novo")
        self.assertEqual(lead.empresa, self.empresa_a)

    def test_converte_lead_em_cliente_no_mesmo_tenant(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:lead-convert", args=[self.empresa_a.id, self.lead_a.id])
        )

        self.assertEqual(response.status_code, 302)
        self.lead_a.refresh_from_db()
        self.assertEqual(self.lead_a.status, Lead.Status.CONVERTIDO)
        self.assertIsNotNone(self.lead_a.cliente_convertido)
        self.assertEqual(self.lead_a.cliente_convertido.empresa, self.empresa_a)

    def test_lead_de_outra_empresa_nao_pode_ser_convertido(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:lead-convert", args=[self.empresa_a.id, self.lead_b.id])
        )

        self.assertEqual(response.status_code, 404)
        self.lead_b.refresh_from_db()
        self.assertNotEqual(self.lead_b.status, Lead.Status.CONVERTIDO)

    def test_cria_oportunidade_com_cliente_e_vendedor_da_empresa(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:oportunidade-create", args=[self.empresa_a.id]),
            data={
                "cliente": self.cliente_a.id,
                "vendedor": self.vendedor_a.id,
                "titulo": "Venda consultiva",
                "valor_estimado": "1500.00",
                "status": Oportunidade.Status.ABERTA,
            },
        )

        self.assertEqual(response.status_code, 302)
        oportunidade = Oportunidade.objects.get(titulo="Venda consultiva")
        self.assertEqual(oportunidade.empresa, self.empresa_a)
        self.assertEqual(oportunidade.cliente, self.cliente_a)
        self.assertEqual(oportunidade.vendedor, self.vendedor_a)

    def test_nao_cria_oportunidade_com_cliente_de_outra_empresa(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:oportunidade-create", args=[self.empresa_a.id]),
            data={
                "cliente": self.cliente_b.id,
                "vendedor": self.vendedor_a.id,
                "titulo": "Venda cruzada indevida",
                "valor_estimado": "1500.00",
                "status": Oportunidade.Status.ABERTA,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Oportunidade.objects.filter(titulo="Venda cruzada indevida").exists())

    def test_registra_historico_de_contato_para_cliente(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:historico-create", args=[self.empresa_a.id]),
            data={
                "cliente": self.cliente_a.id,
                "lead": "",
                "vendedor": self.vendedor_a.id,
                "tipo": HistoricoContato.Tipo.TELEFONE,
                "resumo": "Cliente pediu proposta.",
                "realizado_em": "2026-06-30 10:00:00",
            },
        )

        self.assertEqual(response.status_code, 302)
        historico = HistoricoContato.objects.get(resumo="Cliente pediu proposta.")
        self.assertEqual(historico.empresa, self.empresa_a)
        self.assertEqual(historico.cliente, self.cliente_a)

    def test_cria_proxima_acao_para_oportunidade(self):
        self.client.force_login(self.admin_a)

        response = self.client.post(
            reverse("crm:proxima-acao-create", args=[self.empresa_a.id]),
            data={
                "oportunidade": self.oportunidade_a.id,
                "vendedor": self.vendedor_a.id,
                "descricao": "Enviar proposta revisada",
                "data_prevista": "2026-07-01",
                "status": ProximaAcao.Status.PENDENTE,
            },
        )

        self.assertEqual(response.status_code, 302)
        acao = ProximaAcao.objects.get(descricao="Enviar proposta revisada")
        self.assertEqual(acao.empresa, self.empresa_a)
        self.assertEqual(acao.oportunidade, self.oportunidade_a)

    def test_lista_proximas_acoes_somente_da_empresa(self):
        ProximaAcao.objects.create(
            empresa=self.empresa_a,
            oportunidade=self.oportunidade_a,
            vendedor=self.vendedor_a,
            descricao="Acao A",
            data_prevista="2026-07-01",
        )
        oportunidade_b = Oportunidade.objects.create(
            empresa=self.empresa_b,
            cliente=self.cliente_b,
            vendedor=self.admin_b,
            titulo="Oportunidade B",
            valor_estimado="500.00",
        )
        ProximaAcao.objects.create(
            empresa=self.empresa_b,
            oportunidade=oportunidade_b,
            vendedor=self.admin_b,
            descricao="Acao B",
            data_prevista="2026-07-01",
        )
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:proxima-acao-list", args=[self.empresa_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acao A")
        self.assertNotContains(response, "Acao B")

    def test_workspace_cliente_renderiza_blocos_comerciais(self):
        HistoricoContato.objects.create(
            empresa=self.empresa_a,
            cliente=self.cliente_a,
            vendedor=self.vendedor_a,
            tipo=HistoricoContato.Tipo.EMAIL,
            resumo="Enviou catalogo.",
        )
        ProximaAcao.objects.create(
            empresa=self.empresa_a,
            oportunidade=self.oportunidade_a,
            vendedor=self.vendedor_a,
            descricao="Ligar para decisor",
            data_prevista="2026-07-02",
        )
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:workspace-cliente", args=[self.cliente_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workspace comercial")
        self.assertContains(response, "Cliente A")
        self.assertContains(response, "Produto A")
        self.assertContains(response, "Carrinho/pedido")
        self.assertContains(response, "Enviou catalogo.")
        self.assertContains(response, "Ligar para decisor")
        self.assertContains(response, "Pedidos anteriores")
        self.assertContains(response, "Oportunidade A - Aberta")
        self.assertNotContains(response, "Produto B")

    def test_workspace_oportunidade_renderiza_status_da_oportunidade(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(
            reverse("crm:workspace-oportunidade", args=[self.oportunidade_a.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Status da oportunidade")
        self.assertContains(response, "Oportunidade A - Aberta")
        self.assertContains(response, "Cliente A")

    def test_workspace_cliente_de_outra_empresa_retorna_404(self):
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:workspace-cliente", args=[self.cliente_b.id]))

        self.assertEqual(response.status_code, 404)

    def test_workspace_oportunidade_de_outra_empresa_retorna_404(self):
        oportunidade_b = Oportunidade.objects.create(
            empresa=self.empresa_b,
            cliente=self.cliente_b,
            vendedor=self.admin_b,
            titulo="Oportunidade B",
            valor_estimado="500.00",
        )
        self.client.force_login(self.admin_a)

        response = self.client.get(reverse("crm:workspace-oportunidade", args=[oportunidade_b.id]))

        self.assertEqual(response.status_code, 404)

    def test_workspace_anonima_retorna_403(self):
        response = self.client.get(reverse("crm:workspace-cliente", args=[self.cliente_a.id]))

        self.assertEqual(response.status_code, 403)
