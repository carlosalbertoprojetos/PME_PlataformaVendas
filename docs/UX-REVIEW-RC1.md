# UX Review RC1

Data: 2026-06-30

## Escopo

Esta review simula um empresario usando o sistema pela primeira vez, partindo do RC1 com frontend executivo.

O objetivo e identificar friccao de uso, nao alterar backend, regras de negocio ou arquitetura.

## Premissas de simulacao

- Perfil simulado: dono/gestor de PME, com pouca paciencia para configuracao tecnica.
- Dispositivo principal: desktop/notebook.
- Dispositivo secundario: celular para acompanhamento rapido.
- Usuario disponivel para teste local: `carlosalberto`.
- Empresa demo: `Empresa Demonstração`.
- Produto ainda nao possui producao real, piloto ativo ou gateway de pagamento real.
- A UI atual usa Django templates, sidebar executiva, dashboard, CRM, catalogo, workspace, WhatsApp via `wa.me`, onboarding e billing interno.

## Resumo executivo

O sistema ja transmite uma proposta de SaaS comercial e possui boa estrutura operacional no dashboard executivo. O maior problema de UX nao e visual isolado: e a quebra de continuidade do primeiro valor.

O empresario entende que existe dashboard, CRM, catalogo, recomendacoes e plano, mas encontra friccao quando tenta executar o fluxo completo:

1. nao ha fluxo publico de cadastro/self-service;
2. login ainda parece tecnico;
3. cadastro de produto pela tela HTML nao tem formulario tradicional;
4. oportunidade e proxima acao usam formulario generico;
5. pedido existe como detalhe, mas nao existe criacao real pela UI;
6. workspace mostra "Criar pedido indisponivel nesta fase";
7. navegacao "Pedidos" e "Automacoes" usa ancoras no dashboard, nao telas dedicadas;
8. WhatsApp existe, mas falta orientacao sobre quando usar cada mensagem;
9. billing e interno/admin, sem clareza comercial de plano real.

Veredito: **Regular para primeira experiencia completa**, com partes **Boas** no dashboard executivo e isolamento de permissao. Para piloto assistido, e utilizavel. Para self-service comercial, ainda nao.

## Jornada obrigatoria simulada

### 1. Cadastro

Estado atual: nao foi encontrada tela publica de cadastro de empresa/usuario. O acesso depende de usuario criado previamente ou comando demo/local.

Quantidade de cliques: 0 no produto, pois o fluxo nao existe.

Quantidade de telas: 0 telas de cadastro.

Tempo estimado: indefinido para usuario final; 2 a 5 minutos com intervencao tecnica/admin.

Duvidas do usuario:

- "Como crio minha empresa?"
- "Quem cria meu usuario?"
- "Isso e um sistema para contratar sozinho ou preciso falar com alguem?"
- "Qual plano estou testando?"

Melhorias:

- Criar tela de convite/cadastro assistido para piloto.
- Exibir mensagem clara quando o produto ainda for acesso controlado.
- Criar fluxo minimo: empresa, admin, senha, aceitar termos.
- Separar cadastro comercial futuro de seed local/staging.

Classificacao da etapa: **Ruim**.

### 2. Primeiro login

Estado atual: tela `registration/login.html` usa form padrao e mensagem simples de erro. Layout herda o shell executivo, mas sem contexto de boas-vindas ou ajuda.

Quantidade de cliques: 2 a 3.

Quantidade de telas: 1.

Tempo estimado: 30 segundos a 1 minuto.

Duvidas do usuario:

- "Qual e meu usuario?"
- "Esqueci minha senha, como recupero?"
- "Estou entrando na empresa correta?"
- "O que acontece depois do login?"

Melhorias:

- Melhorar tela de login com titulo de produto, texto curto e estado de erro mais visivel.
- Adicionar link/fluxo de recuperacao de senha quando estiver pronto para piloto real.
- Redirecionar sempre para dashboard da empresa quando houver uma unica empresa.
- Se usuario tiver mais de uma empresa, criar seletor de empresa.

Classificacao da etapa: **Regular**.

### 3. Onboarding

Estado atual: dashboard exibe checklist de onboarding com progresso, etapas, status e CTAs.

Quantidade de cliques: 1 por etapa pendente.

Quantidade de telas: 1 dashboard + tela da etapa.

Tempo estimado: 5 a 15 minutos para entender; 20 a 40 minutos para preencher dados reais.

Duvidas do usuario:

- "Qual etapa devo fazer primeiro?"
- "Cadastrar vendedor e usuarios do plano sao a mesma coisa?"
- "Compartilhar catalogo esta concluido quando tenho produto ou quando compartilhei de fato?"
- "O que significa empresa ativada?"

Melhorias:

- Destacar uma unica proxima melhor acao.
- Diferenciar etapa concluida por dado existente de etapa concluida por acao real.
- Adicionar microcopy curta em cada etapa.
- Criar estado de celebracao/confirmacao ao ativar empresa.

Classificacao da etapa: **Boa**.

### 4. Cadastro produto

Estado atual: rota de produtos lista catalogo e aceita POST JSON; a tela HTML mostra produtos e botao de compartilhar catalogo, mas nao apresenta formulario tradicional para novo produto.

Quantidade de cliques: indefinido pela UI atual; via API seria tecnico.

Quantidade de telas: 1 lista/catalogo, mas sem tela clara de criacao.

Tempo estimado: 1 a 3 minutos para procurar; criacao real nao e obvia para usuario nao tecnico.

Duvidas do usuario:

- "Onde cadastro produto?"
- "Por que vejo catalogo, mas nao vejo Novo produto?"
- "Preciso usar API?"
- "Como adiciono descricao, preco e ativo?"

Melhorias:

- Criar formulario HTML simples de produto na propria tela ou tela "Novo produto".
- Separar visualmente "Produtos" de "Catalogo compartilhavel".
- Adicionar estado vazio com CTA "Cadastrar primeiro produto".
- Confirmar sucesso apos cadastro.

Classificacao da etapa: **Ruim**.

### 5. Cadastro cliente

Estado atual: lista de clientes tem CTA "Novo cliente"; formulario e generico, mas funcional.

Quantidade de cliques: 3 a 5.

Quantidade de telas: 2.

Tempo estimado: 2 a 4 minutos.

Duvidas do usuario:

- "Quais campos sao obrigatorios?"
- "Documento e CPF/CNPJ?"
- "Lead e cliente sao diferentes aqui?"
- "Depois de salvar, qual o proximo passo?"

Melhorias:

- Trocar titulo generico "Formulario" por "Novo cliente".
- Organizar campos por prioridade: nome, telefone, email, documento, observacoes.
- Exibir dica de WhatsApp no campo telefone.
- Apos salvar, sugerir "Criar oportunidade" ou "Abrir workspace".

Classificacao da etapa: **Regular**.

### 6. Criar oportunidade

Estado atual: lista de oportunidades tem CTA "Nova oportunidade"; formulario generico permite selecionar cliente, vendedor, titulo, valor e status.

Quantidade de cliques: 4 a 7.

Quantidade de telas: 2 a 3, dependendo se usuario vem do cliente ou da lista.

Tempo estimado: 2 a 5 minutos.

Duvidas do usuario:

- "O que e oportunidade?"
- "Valor estimado e obrigatorio?"
- "Status deve ficar Aberta?"
- "Por que preciso escolher vendedor se sou eu?"
- "Qual a diferenca entre oportunidade e pedido?"

Melhorias:

- Criar CTA "Criar oportunidade" no detalhe do cliente.
- Pre-preencher vendedor com usuario atual e ocultar quando nao houver escolha real.
- Trocar titulo generico por "Nova oportunidade".
- Adicionar texto curto: "Use oportunidade para acompanhar uma venda em negociacao".

Classificacao da etapa: **Regular**.

### 7. Compartilhar catalogo

Estado atual: tela de catalogo tem botao "Compartilhar catalogo" via POST e links de compartilhar produto.

Quantidade de cliques: 2 a 3.

Quantidade de telas: 1 + redirecionamento externo para WhatsApp.

Tempo estimado: 30 segundos a 1 minuto.

Duvidas do usuario:

- "Para quem estou enviando?"
- "A mensagem sera enviada automaticamente?"
- "O cliente vai ver quais produtos?"
- "Posso editar a mensagem antes?"

Melhorias:

- Explicar que o WhatsApp abre com mensagem pronta e envio manual.
- Exibir preview da mensagem antes do clique.
- Se nao houver produtos, mostrar CTA de cadastro em vez de botao de compartilhar.
- Criar feedback/evento visivel apos retorno do usuario.

Classificacao da etapa: **Boa**.

### 8. Receber pedido

Estado atual: existe detalhe de pedido e pedidos anteriores no workspace, mas nao existe fluxo de criacao/recebimento de pedido pela UI. O workspace informa "Criar pedido indisponivel nesta fase".

Quantidade de cliques: nao aplicavel para criar/receber; 1 a 2 para abrir pedido existente.

Quantidade de telas: detalhe de pedido existe; criacao nao existe.

Tempo estimado: indefinido para pedido novo.

Duvidas do usuario:

- "Como o cliente faz pedido?"
- "Como eu crio pedido a partir da oportunidade?"
- "O catalogo recebe pedido sozinho?"
- "Preciso cadastrar manualmente em outro lugar?"

Melhorias:

- Criar fluxo minimo de pedido como prioridade UX/produto.
- No workspace, trocar texto morto por CTA planejado ou explicacao honesta de fase.
- Adicionar "Criar pedido" quando a feature existir.
- Diferenciar "pedido recebido" de "pedido criado pelo vendedor".

Classificacao da etapa: **Ruim**.

### 9. Abrir Workspace

Estado atual: workspace existe por cliente e oportunidade, reunindo cliente, oportunidade, proxima acao, pedidos, produtos, inteligencia, automacoes e timeline.

Quantidade de cliques: 2 a 4, partindo do dashboard ou CRM.

Quantidade de telas: 1 a 2.

Tempo estimado: 1 a 3 minutos para encontrar; 30 segundos apos aprender o caminho.

Duvidas do usuario:

- "Por que o menu Workspace abre a lista de clientes?"
- "Como sei qual cliente devo abrir?"
- "Workspace e cliente sao a mesma coisa?"
- "Posso abrir workspace direto da oportunidade?"

Melhorias:

- Renomear item de menu para "Clientes / Workspace" ou criar tela intermediaria "Escolha um cliente".
- Adicionar botao "Abrir workspace" em cliente, oportunidade e recomendacoes.
- Aplicar componentes executivos ao workspace para melhorar hierarquia.
- Colocar cliente, proxima acao e pedido no topo.

Classificacao da etapa: **Boa** funcionalmente, **Regular** na descoberta.

### 10. Executar recomendacao

Estado atual: dashboard mostra recomendacoes acionaveis com motivo, prioridade, entidade, acao recomendada e botoes.

Quantidade de cliques: 1 a 3.

Quantidade de telas: 1 dashboard + tela de destino.

Tempo estimado: 30 segundos a 2 minutos.

Duvidas do usuario:

- "Esta recomendacao e urgente?"
- "O que acontece quando clico?"
- "Depois de agir, ela some?"
- "Como marco como resolvida?"

Melhorias:

- Padronizar severidade visual com labels mais claros: Alta, Media, Baixa.
- Adicionar "Por que estou vendo isso?" colapsavel ou texto curto.
- Criar estado de recomendacao acionada/resolvida no futuro.
- Ordenar recomendacoes por prioridade e impacto.

Classificacao da etapa: **Boa**.

### 11. Enviar WhatsApp

Estado atual: links `wa.me` existem para catalogo, produto, pedido, cliente, follow-up e recomendacoes quando ha telefone valido.

Quantidade de cliques: 1 a 2.

Quantidade de telas: 1 tela interna + WhatsApp externo.

Tempo estimado: 30 segundos a 1 minuto.

Duvidas do usuario:

- "A mensagem ja foi enviada?"
- "Posso editar antes de enviar?"
- "Qual telefone sera usado?"
- "Por que o botao nao aparece em alguns clientes?"

Melhorias:

- Exibir telefone de destino junto ao botao.
- Exibir preview da mensagem.
- Quando nao houver telefone valido, mostrar aviso "Adicione telefone para WhatsApp".
- Registrar no historico quando usuario decide criar contato manualmente apos envio.

Classificacao da etapa: **Boa**.

### 12. Criar proxima acao

Estado atual: proxima acao pode ser criada por formulario e pre-preenchida por query params em alguns fluxos. A agenda agrupa hoje, atrasadas, proximas e concluidas.

Quantidade de cliques: 3 a 6.

Quantidade de telas: 1 a 2.

Tempo estimado: 1 a 3 minutos.

Duvidas do usuario:

- "Cliente, oportunidade e pedido sao todos obrigatorios?"
- "Quem e o vendedor?"
- "O que acontece ao concluir?"
- "Receberei lembrete?"

Melhorias:

- Trocar formulario generico por tela "Nova proxima acao".
- Preencher vendedor automaticamente.
- Quando vier de cliente/oportunidade/pedido, ocultar campos ja definidos ou destacar que foram preenchidos.
- Adicionar CTA de concluir mais evidente na agenda.

Classificacao da etapa: **Regular**.

### 13. Dashboard

Estado atual: frontend executivo melhora bastante a leitura de KPIs, onboarding, recomendacoes, proximas acoes, automacoes e limites.

Quantidade de cliques: 1 apos login, se redirecionado corretamente.

Quantidade de telas: 1.

Tempo estimado: 30 segundos a 2 minutos para leitura executiva.

Duvidas do usuario:

- "Qual numero devo olhar primeiro?"
- "Receita do mes considera pedido confirmado?"
- "Por que Pedidos no menu nao abre uma lista?"
- "Automacoes sao configuraveis?"

Melhorias:

- Destacar "o que fazer agora" acima das metricas.
- Explicar discretamente origem dos KPIs.
- Transformar ancoras de Pedidos/Automacoes em telas reais quando o produto exigir.
- Criar versao mobile mais compacta de cards.

Classificacao da etapa: **Boa**.

### 14. Billing

Estado atual: tela de plano exibe assinatura, limites e formulario administrativo. Ainda nao ha gateway real.

Quantidade de cliques: 1 pelo menu para admin.

Quantidade de telas: 1.

Tempo estimado: 1 a 3 minutos.

Duvidas do usuario:

- "Isso altera minha cobranca real?"
- "O que significa trial/ativa/suspensa?"
- "Qual diferenca entre Start, Growth e Pro?"
- "O que acontece quando atingo limite?"

Melhorias:

- Separar tela de leitura do cliente da tela administrativa interna.
- Exibir tabela comparativa simples de planos.
- Explicar que nao ha cobranca automatica nesta fase.
- Destacar limites proximos/atingidos com acao clara.

Classificacao da etapa: **Regular**.

## Classificacao UX por dimensao

| Dimensao | Classificacao | Evidencia | Principal ajuste |
| --- | --- | --- | --- |
| Fluxo | Regular | Jornada existe em partes, mas quebra em cadastro, produto e pedido. | Criar caminho guiado ate primeiro pedido. |
| Legibilidade | Boa | Dashboard executivo e cards melhoraram a leitura. | Melhorar formulários genericos e listas antigas. |
| Layout | Boa | Sidebar, header e cards dao estrutura profissional. | Aplicar padrao visual tambem em CRM, catalogo e workspace. |
| Hierarquia | Regular | Dashboard tem hierarquia; telas operacionais ainda usam listas simples. | Padronizar header, CTA primario e estado vazio por tela. |
| Cores | Boa | Paleta sobria, adequada a SaaS B2B. | Garantir contraste dos badges e avisos em mobile. |
| Componentes | Regular | Componentes existem, mas ainda nao foram aplicados em todo o sistema. | Migrar CRM/catalogo/workspace para componentes existentes. |
| Feedback visual | Regular | Mensagens existem, mas sucesso/erro nem sempre orientam proxima acao. | Adicionar feedback apos salvar, compartilhar e concluir. |
| Estados vazios | Regular | Dashboard tem bons estados; outras telas ainda usam texto cru. | Transformar vazios em CTA orientado. |
| Loading | Ruim | Nao ha estados de carregamento perceptiveis. | Adicionar feedback em botoes/formularios e acoes externas. |
| Mensagens | Regular | Erros basicos existem; copy ainda tecnica/generica. | Melhorar microcopy, erros de permissao e limites. |
| Erros | Regular | Backend protege; UX de erro e pouco contextual. | Criar paginas 403/404 amigaveis e erros de formulario claros. |
| Permissoes | Boa | Links admin sao ocultados e mixins protegem acesso. | Explicar indisponibilidade por papel/plano quando necessario. |
| Mobile | Regular | Layout responde, mas cards/listas podem ficar longos. | Compactar dashboard e priorizar agenda/recomendacoes no mobile. |
| Desktop | Boa | Experiencia executiva funciona melhor em desktop. | Melhorar densidade das telas CRUD. |
| Acessibilidade | Regular | HTML semântico basico e aria em progresso; falta foco/labels/contraste auditado. | Revisar labels, foco visivel, botoes, contraste e headings. |

## Matriz de friccao por etapa

| Etapa | Friccao | Severidade | Motivo |
| --- | --- | --- | --- |
| Cadastro | Alta | P0 UX | Sem fluxo self-service ou assistido visivel. |
| Primeiro login | Media | P1 UX | Tela simples demais para primeira impressao comercial. |
| Onboarding | Media | P1 UX | Bom checklist, mas falta proxima melhor acao. |
| Cadastro produto | Alta | P0 UX | Nao ha formulario HTML evidente. |
| Cadastro cliente | Media | P1 UX | Funciona, mas formulario generico. |
| Criar oportunidade | Media | P1 UX | Conceito exige orientacao e pre-preenchimento. |
| Compartilhar catalogo | Baixa | P2 UX | Funciona, mas falta preview/explicacao. |
| Receber pedido | Alta | P0 UX | Criacao/recebimento real indisponivel na UI. |
| Abrir Workspace | Media | P1 UX | Funciona, mas descoberta pelo menu e confusa. |
| Executar recomendacao | Baixa | P2 UX | Boa base; falta estado de resolucao. |
| Enviar WhatsApp | Baixa | P2 UX | Link funciona; falta preview/telefone/estado sem telefone. |
| Criar proxima acao | Media | P1 UX | Formulario generico com campos demais. |
| Dashboard | Baixa | P2 UX | Boa tela executiva; precisa orientar a acao principal. |
| Billing | Media | P1 UX | Tela ainda mistura admin interno e leitura comercial. |

## Plano priorizado de melhorias UX

### P0 UX - bloquear friccao de primeiro valor

1. Criar fluxo visivel de cadastro assistido ou convite para piloto.
   - Objetivo: eliminar dependencia invisivel de seed/comando.
   - Entrega UX: tela inicial de acesso controlado ou cadastro de empresa/admin.

2. Criar formulario HTML de produto.
   - Objetivo: permitir que o empresario cumpra a primeira etapa central do onboarding.
   - Entrega UX: "Novo produto" com nome, descricao, preco e ativo.

3. Criar fluxo minimo de pedido pela UI.
   - Objetivo: fechar ciclo catalogo -> cliente -> oportunidade -> pedido.
   - Entrega UX: "Criar pedido" no workspace e/ou oportunidade.

4. Trocar textos mortos por orientacao.
   - Exemplo atual: "Criar pedido indisponivel nesta fase".
   - Entrega UX: explicar estado, proxima acao possivel e expectativa.

### P1 UX - reduzir duvida operacional

5. Substituir `crm/form.html` generico por titulos/contextos por entidade.
   - "Novo cliente", "Nova oportunidade", "Nova proxima acao".

6. Pre-preencher e simplificar campos.
   - Vendedor atual por padrao.
   - Cliente/oportunidade quando vier do workspace.
   - Ocultar campos que ja estao definidos no contexto.

7. Melhorar login e primeiro acesso.
   - Texto curto de boas-vindas.
   - Mensagem de erro em card/alerta.
   - Recuperacao de senha quando apropriado.

8. Reorganizar menu Workspace.
   - Trocar "Workspace" apontando para clientes por "Clientes / Workspace" ou criar tela seletora.

9. Criar estados vazios com CTA em CRM, catalogo, oportunidades e agenda.
   - Estado vazio deve sempre responder: o que e isso, por que importa, qual acao agora.

10. Separar billing de cliente versus billing administrativo.
   - Cliente ve plano, limites e upgrade.
   - Admin interno altera status/plano em ambiente seguro.

### P2 UX - polimento e confianca

11. Preview de mensagens WhatsApp.
   - Mostrar telefone, texto e aviso de envio manual.

12. Melhorar recomendacoes acionaveis.
   - Ordenar por prioridade.
   - Mostrar "por que isso importa".
   - Preparar estado futuro "acionada/resolvida".

13. Aplicar componentes executivos ao workspace.
   - Cards para cliente, oportunidade, pedido e proxima acao.
   - Timeline visual mais legivel.

14. Melhorar feedback pos-acao.
   - Salvou cliente: sugerir criar oportunidade.
   - Salvou oportunidade: sugerir criar proxima acao.
   - Compartilhou catalogo: sugerir acompanhar cliente.

15. Melhorar mobile.
   - Priorizar dashboard: alertas, proximas acoes, WhatsApp.
   - Reduzir grids longos.

### P3 UX - evolucao apos piloto

16. Loading states e desabilitar botoes durante submit.
17. Tour curto de primeira visita.
18. Ajuda contextual por tela.
19. Biblioteca visual extraida do CSS inline para static.
20. Teste de usabilidade com 3 empresarios reais.

## Recomendacao de sequencia

Sequencia sugerida antes de piloto:

1. Produto: formulario HTML simples.
2. Pedido: fluxo minimo de criacao.
3. Formularios: titulos e contexto por entidade.
4. Workspace: CTA claro para criar pedido/proxima acao.
5. Login/onboarding: primeira acao recomendada.
6. Billing: leitura clara de plano/limites sem confundir com cobranca real.

## Checklist de validacao UX para proxima fase

- [ ] Um empresario consegue entrar sem ajuda tecnica.
- [ ] Um empresario entende a primeira acao em ate 30 segundos.
- [ ] Primeiro produto cadastrado em menos de 2 minutos.
- [ ] Primeiro cliente cadastrado em menos de 2 minutos.
- [ ] Primeira oportunidade criada em menos de 3 minutos.
- [ ] Primeiro pedido criado em menos de 5 minutos.
- [ ] WhatsApp abre com mensagem compreensivel e telefone claro.
- [ ] Dashboard mostra o que fazer hoje.
- [ ] Mobile permite consultar agenda e recomendacoes.
- [ ] Erro de permissao ou limite explica o motivo e proxima acao.

## Conclusao

O frontend executivo elevou a percepcao de produto, mas a UX do RC1 ainda depende de usuario assistido. O melhor investimento agora nao e mais visual decorativo: e reduzir friccao nas acoes que geram primeiro valor.

Prioridade real: **produto, pedido e formularios contextuais**.

Proxima acao de maior impacto: **criar formulario HTML de produto e fluxo minimo de pedido**, porque essas duas lacunas quebram a promessa central do SaaS comercial.
