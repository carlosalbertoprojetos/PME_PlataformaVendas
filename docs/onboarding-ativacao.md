# Onboarding e ativacao

Data: 2026-06-30

## Objetivo

Guiar uma empresa recem-cadastrada ate o primeiro valor operacional no menor tempo possivel, usando um checklist simples, automatico e auditavel.

## Implementacao

Service:

`services/onboarding.py`

Funcao principal:

`gerar_onboarding_empresa(empresa)`

O service nao persiste estado. Ele calcula o checklist em tempo real a partir dos dados existentes da empresa.

## Etapas

### Completar dados da empresa

Concluida quando:

- empresa possui nome;
- empresa esta ativa.

CTA:

- revisar empresa na tela de plano existente.

### Cadastrar primeiro vendedor

Concluida quando:

- existe `EmpresaMembership` ativo com papel `vendedor`.

CTA:

- revisar usuarios do plano.

Observacao:

- ainda nao existe tela dedicada de convite/cadastro de vendedor nesta fase.

### Cadastrar primeiro produto

Concluida quando:

- existe produto ativo da empresa.

CTA:

- catalogo de produtos.

### Cadastrar primeiro cliente ou lead

Concluida quando:

- existe cliente ativo; ou
- existe lead.

CTA:

- cadastro de cliente.

### Criar primeira oportunidade

Concluida quando:

- existe oportunidade da empresa.

CTA:

- cadastro de oportunidade.

### Criar primeira proxima acao

Concluida quando:

- existe proxima acao da empresa.

CTA:

- cadastro de proxima acao.

### Compartilhar catalogo

Concluida quando:

- existe produto ativo da empresa, deixando o catalogo pronto para compartilhamento via `wa.me`.

CTA:

- tela do catalogo, onde ja existe o botao `Compartilhar catalogo`.

Observacao:

- nao ha rastreamento de clique/envio nesta fase, portanto a conclusao e inferida pela disponibilidade do catalogo compartilhavel.

## Progresso

O percentual e calculado por:

`etapas concluidas / total de etapas * 100`

Com 7 etapas:

- empresa nova apenas com dados basicos: 14%;
- empresa com 5 etapas concluidas: 71%;
- empresa ativada: 100%.

## Empresa ativada

`empresa_ativada` e verdadeiro quando todas as etapas estao concluidas.

Essa ativacao e operacional, nao financeira. Nao depende de pagamento, gateway ou assinatura externa.

## Dashboard

O checklist aparece no dashboard principal da empresa:

`/empresas/<empresa_id>/dashboard/`

Template:

`templates/dashboard/_onboarding.html`

Exibe:

- progresso em percentual;
- estado `Empresa ativada`;
- etapas concluidas e pendentes;
- CTA para cada etapa pendente.

## Multiempresa

Todas as consultas filtram por empresa:

- memberships por empresa;
- produtos por empresa;
- clientes e leads por empresa;
- oportunidades por empresa;
- proximas acoes por empresa.

Dados de outra empresa nao alteram progresso nem ativacao.

## Fora do escopo

- IA;
- gateway;
- envio automatico de WhatsApp;
- rastreamento de clique no catalogo;
- tela dedicada para convite de vendedor;
- persistencia de eventos de onboarding.

## Testes

Arquivo:

`dashboard/tests.py`

Cobertura:

- empresa nova sem dados;
- progresso parcial;
- empresa ativada;
- isolamento por empresa;
- links de CTA;
- renderizacao no dashboard principal.

## Validacao

Comandos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
