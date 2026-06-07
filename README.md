# DevBoard API (MVP)

O DevBoard é uma plataforma de gerenciamento de projetos e tarefas desenhada com um escopo objetivo para pequenas equipes de desenvolvimento de software e profissionais autônomos. 

Esta API fornece o motor centralizado focado na resolução dos relacionamentos entre Tenants (usuários donos) de forma robusta e perfomática.

## Stack Tecnológico 🚀

- **Python 3.13**: Versão moderna focada em performance.
- **FastAPI**: Framework web moderno, construído sob ASGI com serialização e tipagem explícita via Pydantic.
- **SQLAlchemy 2.0**: O padrão ouro em Object Relational Mapper no Python.
- **PostgreSQL**: Banco de dados relacional oficial de produção.
- **Alembic**: Gerenciador versionado de banco de dados e migrações.
- **Pytest**: Arquitetura automatizada de testes isolados.
- **Ruff**: Linter e Formatter feito em Rust para ultra-velocidade na padronização de código.
- **Docker & Docker Compose**: Setup local isolado que mimetiza o ambiente final.

## Principais Endpoints 🔗

A API é rigorosamente segmentada em rotas versionadas (`/api/v1`). Exceto pela criação de usuário e login, **todos os outros endpoints exigem cabeçalho JWT de autenticação**.

- **Auth**: `POST /api/v1/auth/login` - Validação das credenciais e entrega do token.
- **Users**: 
  - `POST /api/v1/users/` - Cadastro.
  - `GET /api/v1/users/me` - Consulta de dados sensíveis da própria conta.
- **Projects**: CRUD protegido (`/api/v1/projects`). Listagens e buscas sempre retornam formato envelopado e isolamento estrito via Token.
- **Tasks**: Hierarquia sob o Projeto. Apenas usuários que detenham um projeto válido podem registrar e gerenciar as respectivas tarefas.

> **Dica**: Confira nossa especificação interativa acessando `http://localhost:8000/docs` com o serviço rodando!

## Como Iniciar (Setup) ⚙️

O ambiente de desenvolvimento está envelopado. Você só precisa ter o Docker e Docker Compose instalados em sua máquina host.

1. Clone o repositório e acesse a pasta raiz.
2. Prepare as variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
3. Suba toda a infraestrutura através do Compose:
   ```bash
   docker compose up -d
   ```
4. A API estará operacional sob `http://localhost:8000`.

## Scripts Úteis 🛠️

Para agilizar o desenvolvimento, os seguintes comandos devem ser rodados através de interação com o contêiner de backend:

**Rodar Testes Automatizados (Pytest)**:
A aplicação roda sua suíte dentro de um SQLite in-memory gerando resíduo nulo sobre o banco Postgres real de desenvolvimento:
```bash
docker compose exec web python -m pytest -v
```

**Formatação de Código (Ruff Formatter)**:
Aplica automaticamente o estilo e re-organiza a estrutura visual do Python:
```bash
docker compose exec web ruff format .
```

**Checagem e Correção (Ruff Linter)**:
Detecta problemas técnicos em importações não-utilizadas, complexidade ciclomática e falhas de tipagem:
```bash
docker compose exec web ruff check . --fix
```
