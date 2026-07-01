# Usuario demo

## Objetivo

O comando `criar_usuario_demo` cria um usuario local ou de staging para validacao executiva da plataforma, sem depender de cadastro manual.

Credenciais:

- Usuario: `carlosalberto`
- Senha: `@Testando123`
- Empresa: `Empresa Demonstração`
- Papel: `admin`

## Como executar

```powershell
python manage.py criar_usuario_demo
```

O comando imprime as credenciais apenas no console de execucao.

## Ambiente permitido

O comando e permitido quando `DJANGO_ENV` nao for `production`.

Em producao, a execucao e bloqueada com `CommandError`.

## Comportamento idempotente

O comando:

- cria ou recupera o usuario `carlosalberto`;
- redefine a senha para `@Testando123`;
- cria ou recupera a empresa `Empresa Demonstração`;
- cria ou recupera o membership entre usuario e empresa;
- garante papel `admin`;
- garante membership ativo;
- nao duplica usuario, empresa ou membership em execucoes repetidas.

## Uso recomendado

Usar somente para:

- ambiente local;
- ambiente de staging;
- demonstracoes internas;
- validacao visual do dashboard executivo;
- testes manuais de onboarding, billing, CRM e workspace.

Nao usar para:

- producao;
- pilotos reais com dados de cliente;
- credenciais compartilhadas publicamente;
- substituicao de fluxo real de criacao de usuarios.

## Testes relacionados

Cobertura adicionada:

- cria usuario, empresa e membership admin;
- comando e idempotente;
- comando bloqueia producao.

Comando de validacao focada:

```powershell
python manage.py test empresas.tests
```
