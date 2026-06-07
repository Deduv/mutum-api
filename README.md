# DevBoard API (MVP)

O DevBoard é uma plataforma de gerenciamento de projetos e tarefas desenhada com um escopo objetivo para pequenas equipes de desenvolvimento de software e profissionais autônomos. 

Esta API fornece o motor centralizado, focado na resolução dos relacionamentos e no isolamento de informações entre usuários (Tenant isolation) de forma robusta e performática.

## 🚀 Features

- **Cadastro de Usuários**: Registro seguro e criptografado.
- **Autenticação JWT**: Login e geração de Tokens.
- **Perfil Autenticado**: Endpoint seguro para consulta dos dados do próprio usuário (`/me`).
- **CRUD de Projetos**: Gerenciamento completo de projetos sob a propriedade exclusiva do usuário.
- **CRUD de Tarefas**: Gerenciamento completo de tarefas atreladas a um projeto válido.
- **Isolamento por Usuário (Tenant Isolation)**: Um usuário jamais consegue acessar, editar ou excluir projetos e tarefas de terceiros.
- **Migrações Automatizadas**: Versionamento estruturado do banco de dados utilizando Alembic.
- **Testes Automatizados**: Suíte com cobertura ponta a ponta utilizando Pytest e banco in-memory isolado.
- **Integração Contínua (CI)**: Pipeline no GitHub Actions validando os testes e estilo do código a cada push/pull request.
- **Ambiente Dockerizado**: Contêineres configurados para garantir a reprodutibilidade 100% fiel.

## 🏗️ Arquitetura

O sistema segue uma separação limpa de responsabilidades dividida em camadas, garantindo manutenibilidade e flexibilidade:

```text
FastAPI
   ↓
Services
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

- **FastAPI**: Atua como a camada HTTP/API, sendo responsável pelos roteadores (endpoints), injeção de dependências e validação tipada estrita via Pydantic.
- **Services**: Camada responsável por isolar as regras de negócio. Todo o controle de permissão (tenant isolation) fica encapsulado aqui, impedindo que a API acesse o banco de dados diretamente e acople a lógica de negócio à rota web.
- **SQLAlchemy**: O ORM (Object Relational Mapper) em sua versão mais moderna (2.0), abstraindo as interações entre o Python e as tabelas SQL.
- **PostgreSQL**: O banco de dados relacional oficial utilizado, garantindo a integridade transacional profunda.
- **Alembic**: O motor de versionamento responsável por rastrear, gerar e aplicar alterações estruturais (DDLs) no banco de dados, sincronizado de forma inteligente ao modelo.

## 🛡️ Qualidade e CI

O ciclo de vida do código é validado e padronizado automaticamente por um Pipeline de Integração Contínua (CI) operado via GitHub Actions.

- **Ruff**: Ferramenta linter e formatter de alta-performance instalada para bloquear anti-patterns no Python e garantir a homogeneidade do estilo visual em toda a equipe.
- **Pytest**: Arquitetura automatizada responsável por executar instâncias dinâmicas e isoladas no SQLite. Ele roda agressivas rotinas de regressão garantindo que falhas de regras de isolamento sejam pegas automaticamente antes do Deploy.

> A cada PR ou Commit enviado para a plataforma, o GitHub Actions engatilha e executa tanto o Ruff quanto o Pytest.

## 💻 Como Executar Localmente

O ambiente de desenvolvimento está completamente envelopado. Você só precisa ter o Docker e Docker Compose na sua máquina.

1. Clone o repositório e acesse a pasta raiz:
   ```bash
   git clone ...
   cd devboard
   ```
2. Prepare as variáveis de ambiente baseando-se no arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```
3. Suba a infraestrutura pesada (API e Database) em plano de fundo:
   ```bash
   docker compose up -d
   ```

A API estará plenamente acessível em `http://localhost:8000`.
Explore a documentação via Swagger iterativo acessando `http://localhost:8000/docs`.

## 🛠️ Scripts Úteis (Manutenção)

Para a rotina interna de desenvolvimento e manutenção, acione a estrutura a partir de chamadas ao contêiner web:

**Rodar a Suíte de Testes (Pytest):**
```bash
docker compose exec web python -m pytest -v
```

**Formatação Rápida de Código:**
```bash
docker compose exec web ruff format .
```

**Validação de Complexidade/Linter:**
```bash
docker compose exec web ruff check . --fix
```

## 🌐 Deploy

*Em breve, a API estará disponível publicamente.*

Após o deploy automatizado para a nuvem ser realizado, adicionaremos aqui:
- A URL Base da API hospedada.
- O link de navegação direta para o Swagger na nuvem.
- Instruções para experimentação interativa.
