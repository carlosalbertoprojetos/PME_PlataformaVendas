from dataclasses import dataclass

from django.urls import reverse

from catalogo.models import Produto
from crm.models import Cliente, Lead, Oportunidade, ProximaAcao
from empresas.models import EmpresaMembership


@dataclass(frozen=True)
class OnboardingEtapa:
    chave: str
    titulo: str
    concluida: bool
    cta_label: str
    cta_url: str


def gerar_onboarding_empresa(empresa):
    etapas = [
        _etapa_dados_empresa(empresa),
        _etapa_vendedor(empresa),
        _etapa_produto(empresa),
        _etapa_cliente_ou_lead(empresa),
        _etapa_oportunidade(empresa),
        _etapa_proxima_acao(empresa),
        _etapa_compartilhar_catalogo(empresa),
    ]
    total = len(etapas)
    concluidas = sum(1 for etapa in etapas if etapa.concluida)
    progresso = int((concluidas / total) * 100) if total else 0
    return {
        "etapas": etapas,
        "total": total,
        "concluidas": concluidas,
        "progresso": progresso,
        "empresa_ativada": concluidas == total,
    }


def _etapa_dados_empresa(empresa):
    return OnboardingEtapa(
        chave="dados_empresa",
        titulo="Completar dados da empresa",
        concluida=bool(empresa.nome and empresa.ativa),
        cta_label="Revisar empresa",
        cta_url=reverse("billing:plano-admin", args=[empresa.id]),
    )


def _etapa_vendedor(empresa):
    return OnboardingEtapa(
        chave="primeiro_vendedor",
        titulo="Cadastrar primeiro vendedor",
        concluida=EmpresaMembership.objects.filter(
            empresa=empresa,
            papel=EmpresaMembership.Papel.VENDEDOR,
            ativo=True,
        ).exists(),
        cta_label="Revisar usuarios do plano",
        cta_url=reverse("billing:plano-admin", args=[empresa.id]),
    )


def _etapa_produto(empresa):
    return OnboardingEtapa(
        chave="primeiro_produto",
        titulo="Cadastrar primeiro produto",
        concluida=Produto.objects.da_empresa(empresa).filter(ativo=True).exists(),
        cta_label="Cadastrar produto",
        cta_url=reverse("catalogo:produto-list-create", args=[empresa.id]),
    )


def _etapa_cliente_ou_lead(empresa):
    concluida = (
        Cliente.objects.da_empresa(empresa).filter(ativo=True).exists()
        or Lead.objects.da_empresa(empresa).exists()
    )
    return OnboardingEtapa(
        chave="primeiro_cliente_ou_lead",
        titulo="Cadastrar primeiro cliente ou lead",
        concluida=concluida,
        cta_label="Cadastrar cliente",
        cta_url=reverse("crm:cliente-create", args=[empresa.id]),
    )


def _etapa_oportunidade(empresa):
    return OnboardingEtapa(
        chave="primeira_oportunidade",
        titulo="Criar primeira oportunidade",
        concluida=Oportunidade.objects.da_empresa(empresa).exists(),
        cta_label="Criar oportunidade",
        cta_url=reverse("crm:oportunidade-create", args=[empresa.id]),
    )


def _etapa_proxima_acao(empresa):
    return OnboardingEtapa(
        chave="primeira_proxima_acao",
        titulo="Criar primeira proxima acao",
        concluida=ProximaAcao.objects.da_empresa(empresa).exists(),
        cta_label="Criar proxima acao",
        cta_url=reverse("crm:proxima-acao-create", args=[empresa.id]),
    )


def _etapa_compartilhar_catalogo(empresa):
    catalogo_pronto = Produto.objects.da_empresa(empresa).filter(ativo=True).exists()
    return OnboardingEtapa(
        chave="compartilhar_catalogo",
        titulo="Compartilhar catalogo",
        concluida=catalogo_pronto,
        cta_label="Compartilhar catalogo",
        cta_url=reverse("catalogo:produto-list-create", args=[empresa.id]),
    )
