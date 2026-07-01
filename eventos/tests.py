from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade, ProximaAcao
from empresas.models import Empresa, EmpresaMembership
from eventos.automation import AutomationRunner
from eventos.dispatcher import dispatch_event, register_event_handler
from eventos.events import DomainEvent, EventType
from eventos.models import AutomationExecutionLog, AutomationRule, EventLog
from vendas.models import Pedido


class EventosComerciaisTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A")
        self.empresa_b = Empresa.objects.create(nome="Empresa B")
        self.usuario_a = User.objects.create_user("admin_a", password="senha-segura")
        self.usuario_b = User.objects.create_user("admin_b", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa_a,
            usuario=self.usuario_a,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.empresa_b,
            usuario=self.usuario_b,
            papel=EmpresaMembership.Papel.ADMIN,
        )

    def test_registra_eventos_base_de_negocio(self):
        cliente = Cliente.objects.create(empresa=self.empresa_a, nome="Cliente A")
        lead = Lead.objects.create(empresa=self.empresa_a, nome="Lead A")
        produto = Produto.objects.create(
            empresa=self.empresa_a,
            nome="Produto A",
            preco="10.00",
        )
        oportunidade = Oportunidade.objects.create(
            empresa=self.empresa_a,
            cliente=cliente,
            vendedor=self.usuario_a,
            titulo="Oportunidade A",
            valor_estimado="100.00",
        )
        pedido = Pedido.objects.create(
            empresa=self.empresa_a,
            cliente=cliente,
            oportunidade=oportunidade,
            vendedor=self.usuario_a,
            valor_total="100.00",
        )
        acao = ProximaAcao.objects.create(
            empresa=self.empresa_a,
            cliente=cliente,
            oportunidade=oportunidade,
            vendedor=self.usuario_a,
            descricao="Ligar",
            data_prevista="2026-07-01",
        )

        pedido.status = Pedido.Status.CONFIRMADO
        pedido.save(update_fields=["status", "atualizado_em"])
        oportunidade.status = Oportunidade.Status.GANHA
        oportunidade.save(update_fields=["status", "atualizado_em"])
        acao.status = ProximaAcao.Status.CONCLUIDA
        acao.save(update_fields=["status", "atualizada_em"])

        tipos = set(EventLog.objects.da_empresa(self.empresa_a).values_list("tipo", flat=True))
        self.assertTrue(
            {
                EventType.CLIENTE_CRIADO,
                EventType.LEAD_CRIADO,
                EventType.PRODUTO_CRIADO,
                EventType.PEDIDO_CRIADO,
                EventType.PEDIDO_CONFIRMADO,
                EventType.OPORTUNIDADE_CRIADA,
                EventType.OPORTUNIDADE_ATUALIZADA,
                EventType.PROXIMA_ACAO_CRIADA,
                EventType.PROXIMA_ACAO_CONCLUIDA,
            }.issubset(tipos)
        )
        self.assertTrue(EventLog.objects.filter(tipo=EventType.LEAD_CRIADO, lead_id=lead.id).exists())
        self.assertTrue(
            EventLog.objects.filter(tipo=EventType.PRODUTO_CRIADO, produto_id=produto.id).exists()
        )

    def test_dispatcher_persiste_evento_e_executa_hook_sincrono(self):
        chamadas = []

        def handler(event):
            chamadas.append(event.tipo)

        register_event_handler("evento_teste", handler)

        dispatch_event(
            DomainEvent(
                tipo="evento_teste",
                empresa=self.empresa_a,
                descricao="Evento de teste",
                entidade_tipo="empresa",
                entidade_id=self.empresa_a.id,
            )
        )

        self.assertEqual(chamadas, ["evento_teste"])
        self.assertTrue(EventLog.objects.filter(tipo="evento_teste").exists())

    def test_dispatcher_nao_registra_handler_duplicado(self):
        chamadas = []

        def handler(event):
            chamadas.append(event.tipo)

        register_event_handler("evento_sem_duplicidade", handler)
        register_event_handler("evento_sem_duplicidade", handler)

        dispatch_event(
            DomainEvent(
                tipo="evento_sem_duplicidade",
                empresa=self.empresa_a,
                descricao="Evento sem duplicidade",
                entidade_tipo="empresa",
                entidade_id=self.empresa_a.id,
            )
        )

        self.assertEqual(chamadas, ["evento_sem_duplicidade"])

    def test_catalogo_compartilhado_registra_evento_e_redireciona_para_whatsapp(self):
        self.client.force_login(self.usuario_a)

        response = self.client.post(
            reverse("catalogo:catalogo-compartilhar", args=[self.empresa_a.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("https://wa.me/", response["Location"])
        evento = EventLog.objects.get(tipo=EventType.CATALOGO_COMPARTILHADO)
        self.assertEqual(evento.empresa, self.empresa_a)
        self.assertEqual(evento.ator, self.usuario_a)

    def test_event_log_e_timeline_respeitam_isolamento_por_empresa(self):
        cliente_a = Cliente.objects.create(empresa=self.empresa_a, nome="Cliente A")
        Cliente.objects.create(empresa=self.empresa_b, nome="Cliente B")

        eventos_a = EventLog.objects.da_empresa(self.empresa_a)
        self.assertTrue(eventos_a.filter(cliente_id=cliente_a.id).exists())
        self.assertFalse(eventos_a.filter(empresa=self.empresa_b).exists())

    def test_workspace_timeline_usa_event_log(self):
        cliente = Cliente.objects.create(empresa=self.empresa_a, nome="Cliente A")
        oportunidade = Oportunidade.objects.create(
            empresa=self.empresa_a,
            cliente=cliente,
            vendedor=self.usuario_a,
            titulo="Oportunidade A",
        )
        self.client.force_login(self.usuario_a)

        response = self.client.get(reverse("crm:workspace-oportunidade", args=[oportunidade.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Oportunidade criada")
        self.assertContains(response, "Oportunidade A")


class AutomacoesComerciaisTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa A")
        self.outra_empresa = Empresa.objects.create(nome="Empresa B")
        self.usuario = User.objects.create_user("admin_auto", password="senha-segura")
        self.outro_usuario = User.objects.create_user("admin_auto_b", password="senha-segura")
        EmpresaMembership.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        EmpresaMembership.objects.create(
            empresa=self.outra_empresa,
            usuario=self.outro_usuario,
            papel=EmpresaMembership.Papel.ADMIN,
        )
        self.cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente A")
        self.oportunidade = Oportunidade.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            titulo="Oportunidade A",
        )

    def test_automation_runner_cria_acao_e_registra_execucao(self):
        regra = AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Follow-up apos pedido confirmado",
            evento_disparador=EventType.PEDIDO_CONFIRMADO,
            conditions=[{"type": "pedido_confirmado"}],
            actions=[
                {
                    "type": "criar_proxima_acao",
                    "descricao": "Acompanhar pedido confirmado",
                    "dias": 1,
                },
                {
                    "type": "registrar_timeline",
                    "titulo": "Automacao registrada",
                    "descricao": "Pedido confirmado gerou acompanhamento.",
                },
            ],
        )
        pedido = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            oportunidade=self.oportunidade,
            vendedor=self.usuario,
            valor_total="100.00",
        )

        pedido.status = Pedido.Status.CONFIRMADO
        pedido.save(update_fields=["status", "atualizado_em"])

        execucao = AutomationExecutionLog.objects.get(regra=regra)
        self.assertEqual(execucao.resultado, AutomationExecutionLog.Resultado.SUCESSO)
        self.assertTrue(
            ProximaAcao.objects.filter(
                empresa=self.empresa,
                cliente=self.cliente,
                pedido=pedido,
                descricao="Acompanhar pedido confirmado",
            ).exists()
        )
        self.assertTrue(
            EventLog.objects.filter(
                empresa=self.empresa,
                tipo="automation_timeline",
                descricao="Pedido confirmado gerou acompanhamento.",
            ).exists()
        )

    def test_automation_runner_nao_duplica_acao_por_evento_e_regra(self):
        regra = AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Sem duplicidade",
            evento_disparador=EventType.PEDIDO_CONFIRMADO,
            actions=[{"type": "criar_tarefa", "descricao": "Tarefa unica"}],
        )
        pedido = Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total="10.00",
        )
        evento = EventLog.objects.get(tipo=EventType.PEDIDO_CONFIRMADO, pedido_id=pedido.id)

        AutomationRunner().run(
            DomainEvent(
                tipo=EventType.PEDIDO_CONFIRMADO,
                empresa=self.empresa,
                entidade_tipo="pedido",
                entidade_id=pedido.id,
                cliente_id=self.cliente.id,
                pedido_id=pedido.id,
            )
        )

        self.assertEqual(AutomationExecutionLog.objects.filter(evento=evento, regra=regra).count(), 1)
        self.assertEqual(ProximaAcao.objects.filter(descricao="Tarefa unica").count(), 1)

    def test_condicao_nao_atendida_registra_execucao_ignorada(self):
        regra = AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Cliente sem compra",
            evento_disparador=EventType.CLIENTE_CRIADO,
            conditions=[{"type": "cliente_sem_compra"}],
            actions=[{"type": "criar_notificacao", "descricao": "Cliente sem compra"}],
        )
        Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total="10.00",
        )
        evento = EventLog.objects.get(tipo=EventType.CLIENTE_CRIADO, cliente_id=self.cliente.id)

        AutomationRunner().run(
            DomainEvent(
                tipo=EventType.CLIENTE_CRIADO,
                empresa=self.empresa,
                entidade_tipo="cliente",
                entidade_id=self.cliente.id,
                cliente_id=self.cliente.id,
            )
        )

        execucao = AutomationExecutionLog.objects.get(evento=evento, regra=regra)
        self.assertEqual(execucao.resultado, AutomationExecutionLog.Resultado.IGNORADA)

    def test_falha_de_condicao_e_auditada(self):
        regra = AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Estoque invalido",
            evento_disparador=EventType.PRODUTO_CRIADO,
            conditions=[{"type": "produto_sem_estoque", "estoque": "invalido"}],
            actions=[{"type": "criar_notificacao"}],
        )

        Produto.objects.create(empresa=self.empresa, nome="Produto A", preco="10.00")

        execucao = AutomationExecutionLog.objects.get(regra=regra)
        self.assertEqual(execucao.resultado, AutomationExecutionLog.Resultado.FALHA)
        self.assertIn("invalid", execucao.erro.lower())

    def test_automacao_respeita_empresa_da_regra(self):
        AutomationRule.objects.create(
            empresa=self.outra_empresa,
            nome="Regra externa",
            evento_disparador=EventType.PEDIDO_CONFIRMADO,
            actions=[{"type": "criar_notificacao", "descricao": "Nao deve executar"}],
        )

        Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total="10.00",
        )

        self.assertFalse(AutomationExecutionLog.objects.filter(empresa=self.outra_empresa).exists())
        self.assertFalse(EventLog.objects.filter(descricao="Nao deve executar").exists())

    def test_dashboard_renderiza_metricas_de_automacao(self):
        AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Notificar pedido",
            evento_disparador=EventType.PEDIDO_CONFIRMADO,
            actions=[{"type": "criar_notificacao", "descricao": "Pedido confirmado"}],
        )
        Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total="10.00",
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("dashboard:empresa", args=[self.empresa.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Automacoes comerciais")
        self.assertContains(response, "Automacoes executadas hoje: 1")
        self.assertContains(response, "Sucesso: 1")
        self.assertContains(response, "Falhas: 0")

    def test_workspace_exibe_automacoes_do_cliente(self):
        AutomationRule.objects.create(
            empresa=self.empresa,
            nome="Timeline do pedido",
            evento_disparador=EventType.PEDIDO_CONFIRMADO,
            actions=[{"type": "registrar_timeline", "descricao": "Automacao visivel"}],
        )
        Pedido.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            oportunidade=self.oportunidade,
            vendedor=self.usuario,
            status=Pedido.Status.CONFIRMADO,
            valor_total="10.00",
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("crm:workspace-cliente", args=[self.cliente.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Automacoes executadas")
        self.assertContains(response, "Timeline do pedido")
        self.assertContains(response, "Sucesso")
