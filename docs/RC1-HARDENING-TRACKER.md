# RC1 Hardening Tracker

Data: 2026-06-30

Fonte de verdade: `docs/RC1-AUDITORIA.md`

## Checklist P0

| Item | Prioridade | Responsavel | Status | Evidencias | Testes executados |
| --- | --- | --- | --- | --- | --- |
| Criar settings por ambiente e mover segredo/config para variaveis de ambiente | P0 | Codex | Concluido | `DJANGO_ENV` e `DJANGO_SECRET_KEY` adicionados em `pme_saas/settings.py`; segredo fixo removido do codigo. Motivo: remover segredo versionado. Impacto: ambientes podem injetar segredo por variavel. Risco: sem segredo fixo, sessoes locais podem variar se env nao for configurada. Rollback: restaurar constantes anteriores no settings. | `python manage.py check` OK; `python manage.py test` OK, 100 testes |
| Definir `DEBUG=False` e `ALLOWED_HOSTS` restrito em producao | P0 | Codex | Concluido | `DEBUG` agora usa `DJANGO_DEBUG` com padrao `False`; `ALLOWED_HOSTS` usa `DJANGO_ALLOWED_HOSTS` com `localhost`, `127.0.0.1` e `testserver`. Motivo: remover wildcard e debug ativo por padrao. Impacto: producao exige hosts explicitos. Risco: ambientes locais com host customizado precisam configurar env. Rollback: restaurar `DEBUG=True` e `ALLOWED_HOSTS=["*"]`. | `python manage.py check` OK; `python manage.py test` OK, 100 testes |
| Criar manifesto de dependencias | P0 | Codex | Concluido | `requirements.txt` criado com `Django==5.0.14`, versao atualmente instalada e registrada nas migrations. Motivo: build reprodutivel. Impacto: onboarding e CI podem instalar a dependencia base. Risco: se houver dependencias transitivas nao capturadas manualmente, precisam ser adicionadas depois. Rollback: remover `requirements.txt`. | `python manage.py check` OK; `python manage.py test` OK, 100 testes |
| Restringir `PlanoAdminView` a admin da empresa | P0 | Codex | Concluido | `PlanoAdminView` passou a usar `EmpresaRoleRequiredMixin` com papel `ADMIN`; teste cobre vendedor bloqueado no GET e POST. Motivo: impedir alteracao de assinatura por vendedor. Impacto: apenas admins da empresa acessam plano. Risco: usuarios vendedores que usavam a tela perdem acesso, como esperado. Rollback: voltar para `EmpresaRequiredMixin`. | `python manage.py check` OK; `python manage.py test` OK, 101 testes |
| Remover recomendacoes comerciais do caminho quente do middleware de billing | P0 | Codex | Concluido | Criado `avaliar_limites_leve` e middleware passou a usa-lo sem recalcular recomendacoes comerciais; `avaliar_limites` completo foi preservado. Motivo: reduzir custo por request. Impacto: avisos do middleware continuam, mas contagem de recomendacoes no request usa zero ate uma avaliacao completa explicita. Risco: barra global pode nao refletir recomendacoes em tempo real. Rollback: middleware voltar a chamar `avaliar_limites`. | `python manage.py check` OK; `python manage.py test` OK, 102 testes |

## Checklist P1

| Item | Prioridade | Responsavel | Status | Evidencias | Testes executados |
| --- | --- | --- | --- | --- | --- |
| Adicionar cache ou precomputacao para inteligencia comercial | P1 | Codex | Concluido | `gerar_recomendacoes_comerciais` passou a usar cache Django com TTL de 60s e chave por empresa/assinatura hash dos dados comerciais. Motivo: reduzir recomputacao no dashboard/workspace. Impacto: chamadas repetidas reaproveitam resultados enquanto dados nao mudam. Risco: cache local por processo e TTL curto; nao substitui precomputacao distribuida futura. Rollback: remover cache do service. | `python manage.py check` OK; `python manage.py test` OK, 102 testes |
| Otimizar N+1 em clientes sem recompra e score de oportunidade | P1 | Codex | Concluido | Inteligencia comercial passou a usar `Exists` para historico/proxima acao e `Subquery` para ultimo pedido, removendo consultas por item nos pontos auditados. Motivo: reduzir N+1 sem alterar regras. Impacto: mesmos resultados com menos queries por volume. Risco: consultas SQL ficam mais sofisticadas. Rollback: restaurar loops anteriores. | `python manage.py check` OK; `python manage.py test` OK, 102 testes |
| Adicionar protecao contra registro duplicado de handlers no dispatcher | P1 | Codex | Concluido | `EventDispatcher.subscribe` e `subscribe_all` agora ignoram handler ja registrado; teste cobre registro duplicado por tipo. Motivo: evitar efeitos duplicados em autoreload/imports repetidos. Impacto: idempotencia no registro de handlers. Risco: se algum fluxo dependesse de registrar o mesmo handler duas vezes, deixara de repetir, que e o esperado. Rollback: remover verificacao de duplicidade nas listas. | `python manage.py check` OK; `python manage.py test` OK, 103 testes |
| Trocar registro de compartilhamento de catalogo para POST ou confirmar explicitamente a acao | P1 | Codex | Concluido | `CatalogoCompartilharView` passou a aceitar apenas POST; template renderiza formulario com CSRF; testes cobrem GET 405 e POST com redirect `wa.me`. Motivo: evitar mutacao/auditoria por GET. Impacto: compartilhamento exige acao explicita de formulario. Risco: links antigos GET deixam de registrar e passam a 405. Rollback: reabilitar GET na view. | `python manage.py check` OK; `python manage.py test` OK, 104 testes |
| Criar paginacao/limites claros para workspace e timeline | P1 | Codex | Concluido | Criadas constantes `WORKSPACE_LIMITE_*` para pedidos, timeline, eventos por tipo e automacoes; teste garante timeline limitada a 20 itens. Motivo: previsibilidade de carga no workspace. Impacto: tela passa a ter teto operacional explicito. Risco: itens antigos podem nao aparecer sem futura paginacao. Rollback: remover constantes e slices. | `python manage.py check` OK; `python manage.py test` OK, 105 testes |

## Registro de correcoes

- P0 settings/segredo: concluido.
- P0 debug/hosts: concluido.
- P0 manifesto de dependencias: concluido.
- P0 permissao billing admin: concluido.
- P0 middleware billing leve: concluido.
- P1 cache inteligencia comercial: concluido.
- P1 otimizacao N+1: concluido.
- P1 dispatcher sem duplicidade: concluido.
- P1 compartilhamento por POST: concluido.
- P1 limites workspace/timeline: concluido.

## Resumo executivo

Hardening RC1 concluido para o escopo solicitado: 5/5 P0 e 5/5 P1 concluidos, com testes verdes apos cada correcao.
