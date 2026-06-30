# Auditoria tecnica - Catalogo de Produtos

Data: 2026-06-30

Escopo solicitado: auditar o projeto atual de catalogo de produtos em um SaaS Django, antes de qualquer alteracao funcional.

## Sumario executivo

O repositorio `PME_PlataformaVendas` nao contem, no estado atual, uma aplicacao Django implementada. A arvore versionada possui apenas `.gitignore`, alem da pasta `.git`. Nao existem `manage.py`, apps, models, views, urls, templates, forms, arquivos static, dependencias declaradas, migrations ou testes de catalogo para auditoria de codigo.

Conclusao: o sistema ainda nao esta tecnicamente preparado para operar catalogo de produtos nem multiempresa, porque a superficie de aplicacao nao existe nesta copia do projeto. Qualquer afirmacao sobre regras de negocio, permissoes, isolamento por empresa, escalabilidade ou seguranca seria especulativa sem codigo fonte.

## Mapeamento do projeto atual

### Estrutura encontrada

- `.git/`
- `.gitignore`
- `docs/auditoria-tecnica.md` criado por esta auditoria

### Apps Django

Nao encontrados.

Evidencia: `rg --files` nao retornou arquivos de aplicacao; `git ls-files` retornou apenas `.gitignore`.

### Models

Nao encontrados.

Impacto: nao ha entidade `Produto`, `Empresa`, relacionamento de posse por empresa, campos de auditoria, constraints, indexes, soft delete, precificacao, estoque ou catalogo publicado para avaliar.

### Views

Nao encontradas.

Impacto: nao ha handlers HTTP para avaliar autenticacao, autorizacao, validacao de entrada, CSRF, paginacao, filtros, cache, consultas ou exposicao indevida de dados.

### URLs

Nao encontradas.

Impacto: nao ha superficie de rotas de catalogo para revisar, nem namespace por app, rotas administrativas, APIs ou endpoints publicos.

### Templates

Nao encontrados.

Impacto: nao ha HTML para revisar quanto a XSS, formularios, mensagens de erro, exposicao de dados entre empresas, usabilidade ou consistencia visual.

### Forms

Nao encontrados.

Impacto: nao ha validacao server-side de cadastro/edicao de produto, normalizacao de campos, restricoes por empresa ou saneamento de entrada.

### Static files

Nao encontrados.

Impacto: nao ha CSS/JS/imagens de catalogo para avaliar duplicidade, acoplamento com templates, riscos de script inline, assets pesados ou manutencao.

### Dependencias

Nao foram encontrados arquivos como `requirements.txt`, `pyproject.toml`, `Pipfile`, `poetry.lock`, `package.json` ou `uv.lock`.

Observacao: o ambiente local possui Django instalavel via `python -m django --version`, retornando `5.0.14`, mas isso e dependencia do ambiente, nao do projeto. O projeto nao declara dependencias reprodutiveis.

## Diagnostico por tema

### Duplicidades

Nao ha codigo suficiente para identificar duplicidades de models, views, templates, forms ou static files.

Risco atual: se o desenvolvimento continuar sem estrutura definida, duplicidades tendem a surgir em cadastro de produto, filtros por empresa, validacoes e templates administrativos.

### Acoplamentos

Nao ha acoplamentos implementados para avaliar.

Risco atual: a ausencia de fronteiras de app e contratos claros pode levar a acoplamento precoce entre catalogo, pedidos, clientes, estoque e financeiro quando o sistema for criado.

### Seguranca

Nao ha endpoints ou templates para revisar vulnerabilidades concretas.

Riscos bloqueantes pela ausencia de implementacao:

- Autenticacao nao comprovada.
- Autorizacao por usuario/empresa nao comprovada.
- CSRF nao comprovado.
- Protecao contra XSS nao comprovada.
- Validacao server-side nao comprovada.
- Segredos/configuracao de ambiente nao definidos.
- Dependencias nao fixadas.

### Permissoes

Nao existe sistema de permissoes implementado nesta arvore.

Risco critico: nao ha evidencia de que usuarios comuns, administradores de empresa, operadores ou superusuarios tenham escopos separados.

### Escalabilidade

Nao ha consultas, modelos, indices, paginacao ou cache para avaliar.

Riscos a enderecar quando o catalogo for implementado:

- Listagens de produtos sem paginacao.
- Busca textual sem estrategia de indice.
- Falta de indice composto por empresa e status.
- Upload de imagens sem storage e limites definidos.
- Consultas sem isolamento por tenant em managers/querysets.

### Multiempresa

O sistema nao esta preparado para multiempresa no estado atual.

Motivo: nao existe modelagem de `Empresa`/tenant, nao existem chaves estrangeiras por empresa nos dados do catalogo, nao existem filtros obrigatorios por empresa nas consultas, nao ha middleware/contexto de tenant, nao ha testes de isolamento e nao ha regras de permissao por empresa.

## Lista priorizada de problemas

1. **Critico - ausencia de projeto Django versionado**
   - Nao ha `manage.py`, settings, apps ou dependencias declaradas.
   - Sem essa base, nao existe catalogo auditavel nem executavel.

2. **Critico - multiempresa inexistente**
   - Nao ha modelagem de tenant/empresa nem prova de isolamento de dados.
   - O SaaS nao deve ser considerado apto a receber dados reais de mais de uma empresa.

3. **Critico - ausencia de permissoes e autenticacao verificaveis**
   - Nao ha rotas, views ou decorators/mixins de permissao.
   - Nao e possivel provar que um usuario nao acessaria produtos de outra empresa.

4. **Alto - ausencia de testes**
   - `pytest` encontrou 0 testes.
   - `python manage.py test` nao roda porque `manage.py` nao existe.

5. **Alto - dependencias nao reprodutiveis**
   - Nao ha arquivo de dependencias no repositorio.
   - O Django instalado no ambiente nao garante reprodutibilidade para outro dev/CI/producao.

6. **Medio - ausencia de estrutura documental minima de arquitetura**
   - Antes deste arquivo, nao havia `docs/`.
   - Decisoes sobre catalogo, empresa, permissoes e dados ainda nao estao registradas no repositorio.

## Lista priorizada de melhorias

1. **Criar a fundacao Django do projeto**
   - Adicionar estrutura Django minima com `manage.py`, settings, app de catalogo, app/entidade de empresa e arquivo de dependencias.
   - Fazer isso em tarefa separada, pois esta auditoria nao altera regras nem implementa funcionalidade.

2. **Definir contrato multiempresa antes do catalogo**
   - Especificar como o tenant sera resolvido: usuario logado, empresa ativa, subdominio, middleware ou outro mecanismo.
   - Definir regras para superusuario, membros de empresa e acesso administrativo.

3. **Modelar catalogo com isolamento obrigatorio**
   - Todo produto deve pertencer a uma empresa.
   - Consultas de catalogo devem filtrar por empresa por padrao.
   - Constraints e indices devem refletir o escopo por empresa.

4. **Criar testes de isolamento entre empresas como primeira linha de defesa**
   - Usuario da Empresa A nao lista, ve, edita ou remove produtos da Empresa B.
   - APIs, templates e admin devem respeitar o mesmo escopo.

5. **Declarar dependencias e comandos de qualidade**
   - Versionar dependencias.
   - Definir comandos padrao para test, check, lint e migrate.

6. **Documentar arquitetura inicial**
   - Registrar decisoes de apps, models, permissoes, URLs e estrategia de multiempresa em `docs/`.

## Comandos executados e resultados

| Comando | Resultado |
| --- | --- |
| `Get-ChildItem -Force` na raiz pai | Encontrou a pasta `PME_PlataformaVendas`. |
| `Get-ChildItem -Force` em `PME_PlataformaVendas` | Encontrou apenas `.git` e `.gitignore` antes desta auditoria. |
| `rg --files` | Nao retornou arquivos. |
| `git status --short` | Sem alteracoes antes da criacao deste relatorio. |
| `git ls-files` | Retornou apenas `.gitignore`. |
| `git branch --show-current` | `main`. |
| `git log --oneline -5` | `5e135aa Initial commit`. |
| `Get-ChildItem -Force -Recurse -Depth 2` | Confirmou ausencia de codigo Django; apenas `.git` e `.gitignore`. |
| `git remote -v` | `origin` aponta para `https://github.com/carlosalbertoprojetos/PME_PlataformaVendas.git`. |
| `git branch -a` | `main`, `origin/main` e `origin/HEAD -> origin/main`. |
| `git show --stat --oneline HEAD` | Commit inicial contem apenas `.gitignore`. |
| `git show --name-only --pretty=format: HEAD` | Retornou apenas `.gitignore`. |
| `Get-Content .gitignore` | Arquivo padrao Python/Django e ferramentas relacionadas; nao define projeto. |
| `python --version` | `Python 3.10.0`. |
| `python manage.py test` | Falhou: `manage.py` nao existe. |
| `Get-ChildItem -Force docs` | Falhou antes desta auditoria: `docs` nao existia. |
| `python -m pytest` | Executou, mas coletou 0 testes: `no tests ran`. |
| `python -m django --version` | `5.0.14` instalado no ambiente local. |

## Estado final desta auditoria

Arquivo criado: `docs/auditoria-tecnica.md`.

Nenhuma regra de negocio foi alterada. Nenhuma dependencia foi criada ou instalada. Nenhuma refatoracao foi feita.

## Proximo passo recomendado

Antes de implementar funcionalidades de catalogo, criar uma tarefa especifica de fundacao do SaaS Django com escopo minimo:

- projeto Django executavel;
- dependencias versionadas;
- modelagem de empresa/tenant;
- app de catalogo;
- politica de permissao por empresa;
- testes de isolamento multiempresa.
