## Project Overview

This is the Python implementation of InKCre. 
InKCre aims to build an information management application that provides automatic information collection, organization and powerful use of information. 

## Tech Stack

- API Framework: FastAPI
- Background Task: Apscheduler
- Database management: SQLModel as ORM, Alembic as migration tool
- Database: PostgreSQL
- Configuration management: pydantic-settings + env file

## Architecture Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                           (run.py)                               │
└────────────┬──────────────────────────────────────┬──────────────┘
             │                                      │
     ┌───────▼────────┐                    ┌───────▼────────┐
     │  Middleware    │                    │    Routes      │
     │  - Logging     │                    │  - REST API    │
     │  - JWT Auth    │                    │  - /blocks     │
     │  - CORS        │                    │  - /sources    │
     └────────────────┘                    │  - /sink/rag   │
                                           └───────┬────────┘
                                                   │
                                           ┌───────▼────────┐
                                           │   Business     │
                                           └───────┬────────┘
                         ┌─────────────────────────┼─────────────────────────┐
                         │                         │                         │
                 ┌───────▼────────┐       ┌───────▼────────┐       ┌───────▼────────┐
                 │    Source      │  ──►  │   Info-Base    │  ──►  │     Sink       │
                 │  (数据输入)     │       │  (核心图存储)   │       │  (数据输出)     │
                 │  - SourceBase  │       │  - Block       │       │  - RAG         │
                 │  - CollectJob  │       │  - Relation    │       │  - Embedding   │
                 └────────────────┘       │  - Storage     │       └────────────────┘
                         ▲                │  - Resolver    │                │
                         │                └────────────────┘                │
                 ┌───────┴────────┐               │                         │
                 │   Extension    │◄──────────────┴─────────────────────────┘
                 │  (扩展系统)     │
                 │  - rss         │
                 │  - mail        │
                 │  - github      │
                 └────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐   ┌──────▼──────┐  ┌────▼────┐
    │  Engine │   │  Scheduler  │  │  Libs   │
    │  (DB)   │   │  (Jobs)     │  │  - AI   │
    └─────────┘   └─────────────┘  │  - obsrv│
                                    └─────────┘
```

## Business Domains

- **source**: Data collectors, the input of info-base
- **info-base**: Core information management
  - block: Content units
  - relation: Links between blocks
  - storage: Store block content somewhere else than database
  - resolver: resolves block content
- **sink**: Interface to use information base, the output of info-base
- **extension**: extends info-base, source and sink abilities
- **client**: manages distributed client instances

## Project Structure (Only Crucial)

- `pyproject.toml`
- `requirements.txt`: the prod requirements generated from `pyproject.toml` using PDM.
- `run.py`: include routes and launch the app
- `app/`
  - `business/`: service layer, by domains
  - `schemas/`: tables and data models
  - `routes/`: register/wrap/expose business methods to FastAPI
  - `engine.py`: db session
  - `settings.py`: centeralized application settings based on pydantic-settings
  - `scheduler.py`: apscheduler
- `extensions/`: built-in extensions (also where installed extensions stored)
- `utils/`
- `libs/`
  - `obsrv`: observability
  - `ai`: embedding, LLM completion
- `tests/`: unit tests
- `migrations/`: db migrations
- `scripts/`
- `docs/`

> Read each folder's AGENTS.md for their details and coding guideline.

## Architecture Navigation

快速查找各模块文档：

### Core Modules
- [app/](app/AGENTS.md) - 应用核心（settings, engine, scheduler, middleware）
- [app/business/](app/business/AGENTS.md) - 业务逻辑层总览
- [app/routes/](app/routes/AGENTS.md) - REST API 路由
- [app/schemas/](app/schemas/AGENTS.md) - 数据模型和表定义

### Business Domains
- [app/business/info_base/](app/business/info_base/AGENTS.md) - 核心信息管理（Block + Relation）
- [app/business/source/](app/business/source/AGENTS.md) - 数据源和采集
- [app/business/sink/](app/business/sink/AGENTS.md) - RAG 和信息输出
- [app/business/extension/](app/business/extension/AGENTS.md) - 扩展系统
- [app/business/client/](app/business/client/AGENTS.md) - 客户端管理

### Infrastructure
- [libs/](libs/AGENTS.md) - 共享库（AI, 日志）
- [utils/](utils/AGENTS.md) - 工具函数
- [migrations/](migrations/AGENTS.md) - 数据库迁移
- [extensions/](extensions/AGENTS.md) - 内置扩展包

## Development Workflow

- Package management: PDM (`pdm install`, `pdm add`)
- Python environemnt: PDM (`pdm run` for scripts/executables)
- Database Migrations: `pdm run alembic-gengrade "message"` (autogenerates + upgrades)
- Run dev server to validate your changes: `uvicorn run:api_app --reload` (sets up extensions, scheduler)
- `DATABASE_URL` is prepared for you even in cloud (Github Action) environment.

## Coding Guideline

- Do not repeat yourself.
  - If the same code is used at over two places, extract it.
- Export the frequently used items in each packages's `__init__.py`

## Deployment

This project supports following deployments:

- Heroku App
- Docker Compose / Docker