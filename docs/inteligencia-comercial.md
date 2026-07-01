# Inteligencia comercial deterministica

Data: 2026-06-30

## Objetivo

Adicionar recomendacoes comerciais auditaveis antes de qualquer IA generativa. Todas as recomendacoes sao calculadas por regras explicitas e incluem motivo.

## Fora do escopo

- API de IA.
- Modelo generativo.
- Prompt engineering.
- Treinamento de modelo.
- Automacao de envio.
- Decisao automatica sem revisao humana.

## Implementacao

Servico principal:

`services/inteligencia_comercial.py`

Dashboard:

`/empresas/<empresa_id>/dashboard/recomendacoes/`

View:

`dashboard.views.RecomendacoesComerciaisView`

Template:

`templates/dashboard/recomendacoes.html`

## Regras implementadas

### Score de oportunidade

Fonte:

- `crm.Oportunidade`
- `crm.ProximaAcao`
- `crm.HistoricoContato`

Pontuacao:

- +30 quando `valor_estimado >= 1000`;
- +15 quando `valor_estimado > 0`;
- +25 quando a oportunidade esta aberta;
- +25 quando existe proxima acao pendente;
- +20 quando o cliente possui historico comercial.

O score maximo e limitado a 100.

Motivo gerado:

- explica valor estimado;
- informa se esta aberta;
- informa se ha proxima acao pendente;
- informa se ha historico comercial.

### Produtos com alta saida

Fonte:

- `vendas.Pedido`
- `vendas.PedidoItem`

Regra:

- produto aparece quando vendeu pelo menos 5 unidades em pedidos confirmados no mes atual.

Motivo gerado:

- quantidade vendida no mes.

### Produtos em risco de ruptura

Fonte:

- `vendas.Pedido`
- `vendas.PedidoItem`
- `catalogo.Produto`

Regra:

- produto ativo aparece quando vendeu pelo menos 10 unidades em pedidos confirmados no mes atual.

Observacao:

- ainda nao existe model de estoque;
- por isso o motivo deixa claro que o risco vem de alta saida sem controle de estoque implementado.

### Clientes sem recompra

Fonte:

- `crm.Cliente`
- `vendas.Pedido`

Regra:

- cliente ativo com historico de pedido confirmado aparece quando nao tem pedido confirmado nos ultimos 45 dias.

Motivo gerado:

- informa a janela de 45 dias sem recompra.

### Sugestoes de follow-up

Fonte:

- `crm.Oportunidade`
- `crm.ProximaAcao`

Regra:

- oportunidade aberta ha mais de 7 dias e sem proxima acao pendente gera sugestao.

Motivo gerado:

- informa que a oportunidade esta aberta ha mais de 7 dias sem proxima acao pendente.

### Alertas comerciais

Fonte:

- resultados das regras anteriores.

Alertas gerados:

- risco de ruptura: severidade alta;
- follow-up pendente: severidade media;
- oportunidade quente com score >= 80: severidade alta;
- clientes sem recompra: severidade media;
- produtos com alta saida: severidade baixa.

Cada alerta inclui motivo textual.

## Recomendacoes acionaveis

As recomendacoes passaram a ser expostas no fluxo operacional diario sem alterar as regras deterministicas existentes.

Locais:

- dashboard principal da empresa: `/empresas/<empresa_id>/dashboard/`;
- dashboard completo de recomendacoes: `/empresas/<empresa_id>/dashboard/recomendacoes/`.

O bloco resumido do dashboard principal exibe apenas os alertas comerciais acionaveis. Quando nao houver alerta, a tela mostra:

`Nenhuma recomendação crítica no momento`

Cada recomendacao acionavel mantem:

- `tipo`;
- `titulo`;
- `motivo` auditavel;
- `prioridade`;
- `entidade_relacionada`;
- `acao_recomendada`;
- `link_acao`;
- `acoes`, lista com todos os links operacionais disponiveis.

Links gerados:

- abrir cliente via `crm:cliente-detail`;
- abrir oportunidade via `crm:oportunidade-detail`;
- abrir produto via `catalogo:produto-detail`;
- abrir pedido anterior quando a recomendacao de recompra possui ultimo pedido confirmado;
- criar proxima acao via `crm:proxima-acao-create` quando a recomendacao e de follow-up.

A camada acionavel nao cria novas regras de IA, nao chama API externa e nao altera os limiares de score, recompra, follow-up, ruptura ou alta saida. Ela apenas adiciona metadados de acao aos resultados ja calculados pelo service.

## Ações via WhatsApp

As recomendacoes acionaveis podem incluir o botao `Enviar WhatsApp` quando houver cliente ou pedido relacionado com telefone valido.

Implementacao:

- gerador principal: `whatsapp.services.gerar_link_recomendacao_whatsapp`;
- mensagens: `whatsapp.services.gerar_mensagem_recomendacao_whatsapp`;
- sanitizacao: `whatsapp.services.sanitizar_telefone_whatsapp`;
- validacao: `whatsapp.services.telefone_whatsapp_valido`;
- link final: `wa.me` com mensagem codificada.

Regras:

- nao usa API oficial do WhatsApp;
- nao envia mensagem automaticamente;
- nao exibe botao quando o telefone nao possui quantidade valida de digitos;
- mantem o vendedor no controle, pois o link apenas abre a conversa no WhatsApp;
- usa apenas dados ja presentes na recomendacao escopada por empresa.

Mensagens cobertas:

- cliente sem recompra;
- oportunidade parada ou follow-up pendente;
- pedido pendente;
- produto recomendado;
- oportunidade quente ou follow-up comercial.

O botao e adicionado como uma acao operacional da recomendacao, sem alterar score, severidade, limites ou qualquer regra de decisao.

## Multiempresa

Todas as consultas filtram por empresa antes de calcular recomendacoes.

Regras:

- dashboard usa `EmpresaRequiredMixin`;
- usuario sem membership ativa recebe `403`;
- objetos de outra empresa nao entram nos resultados;
- nao ha bypass por `is_staff` ou `is_superuser`.

## Testes

Arquivo:

`dashboard/test_inteligencia_comercial.py`

Cobertura:

- score de oportunidade com motivo;
- produto de alta saida;
- produto em risco de ruptura;
- cliente sem recompra;
- sugestao de follow-up;
- isolamento entre empresas;
- renderizacao do dashboard de recomendacoes;
- renderizacao de recomendacoes acionaveis no dashboard principal;
- links operacionais de cliente, oportunidade, pedido, produto e proxima acao;
- geracao de link `wa.me` para recomendacoes com telefone valido;
- bloqueio de link WhatsApp quando o telefone e invalido;
- mensagens por tipo de recomendacao comercial;
- estado vazio sem recomendacoes criticas;
- bloqueio de empresa sem membership.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
