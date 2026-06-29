# LexMind AI - Enterprise Agentic Decision Intelligence Platform

A production-grade, domain-agnostic Agentic Decision Intelligence Platform designed to transform enterprise decision-making processes. Built with modularity and extensibility at its core, LexMind AI currently supports Legal Case Management and is architected to seamlessly extend to Healthcare, Insurance, Finance, HR, and Compliance domains.

## 🏗️ Architecture Overview

LexMind AI follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│  [Routers] [Middleware] [Exception Handlers]            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
│  [Business Logic] [Orchestration]                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                Repository Layer                          │
│  [Data Access] [CRUD Operations]                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Database Layer (MySQL)                      │
│  [SQLAlchemy Models] [Alembic Migrations]               │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Agent Registry**
Dynamic agent discovery and management system that allows runtime registration of specialized agents without code changes.

#### 2. **Tool Registry**
Centralized tool catalog enabling agents to discover and execute external capabilities (APIs, databases, computational functions).

#### 3. **Memory Interfaces**
Abstract memory providers for:
- Short-term memory (execution context)
- Long-term memory (historical data)
- Conversation memory (dialogue tracking)
- Case memory (domain-specific context)

#### 4. **Repository Pattern**
Generic CRUD operations with:
- Async support
- Pagination
- Filtering
- Type safety

#### 5. **Service Layer**
Business logic abstraction providing clean interfaces for domain operations.

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── middleware/          # CORS, logging, error handling
│   │   └── routers/             # API endpoints
│   │       ├── cases.py         # Case management
│   │       ├── recommendations.py
│   │       ├── agents.py        # Agent registry API
│   │       ├── tools.py         # Tool registry API
│   │       ├── planner.py       # Planner endpoints (Phase 2)
│   │       ├── memory.py        # Memory endpoints (Phase 2)
│   │       └── health.py        # Health checks
│   ├── core/
│   │   ├── config.py            # Application configuration
│   │   ├── security.py          # JWT & password hashing
│   │   └── enums.py             # Shared enumerations
│   ├── database/
│   │   ├── session.py           # Async SQLAlchemy session
│   │   └── base.py              # Base models with mixins
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── case.py
│   │   ├── case_document.py
│   │   ├── recommendation.py
│   │   ├── planner_execution.py
│   │   ├── memory.py
│   │   ├── feedback.py
│   │   └── audit_log.py
│   ├── schemas/                 # Pydantic validation schemas
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── case.py
│   │   ├── recommendation.py
│   │   └── feedback.py
│   ├── repositories/            # Data access layer
│   │   ├── base.py              # Generic repository
│   │   ├── case.py
│   │   ├── recommendation.py
│   │   └── user.py
│   ├── services/                # Business logic layer
│   │   ├── base.py
│   │   ├── case.py
│   │   ├── recommendation.py
│   │   ├── planner.py           # Interface (Phase 2)
│   │   └── memory.py            # Interface (Phase 2)
│   ├── registry/
│   │   ├── agent_registry.py    # Dynamic agent registration
│   │   └── tool_registry.py     # Dynamic tool registration
│   ├── memory/
│   │   └── providers.py         # Memory provider interfaces
│   ├── utils/
│   │   └── logging/
│   │       └── logger.py        # Structured logging
│   └── main.py                  # FastAPI application
├── alembic/                     # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/                       # Test suite
│   ├── conftest.py
│   └── test_health.py
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
├── pyproject.toml               # Poetry dependencies
├── alembic.ini                  # Alembic configuration
├── .env.example                 # Environment template
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- MySQL 8.0+
- Docker & Docker Compose (optional)
- Poetry (Python package manager)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd PS_2

# Copy environment file
cp .env.example .env

# Start services with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

The API will be available at `http://localhost:8000`

#### Option 2: Local Development

```bash
# Install dependencies with Poetry
poetry install

# Copy environment file
cp .env.example .env

# Update DATABASE_URL in .env to point to your local MySQL
# DATABASE_URL=mysql+aiomysql://lexmind:lexmind_password@localhost:3306/lexmind_db

# Create database
mysql -u root -p
CREATE DATABASE lexmind_db;
CREATE USER 'lexmind'@'localhost' IDENTIFIED BY 'lexmind_password';
GRANT ALL PRIVILEGES ON lexmind_db.* TO 'lexmind'@'localhost';
FLUSH PRIVILEGES;

# Run migrations
poetry run alembic upgrade head

# Start the application
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (includes DB connection)
curl http://localhost:8000/ready

# Interactive API documentation
open http://localhost:8000/docs
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
ENVIRONMENT=development          # development, staging, production
DEBUG=True
APP_NAME=LexMind AI
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=mysql+aiomysql://user:password@host:3306/database

# Security
SECRET_KEY=<generate-secure-key>  # Minimum 32 characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                   # json or console

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📊 Database Schema

### Core Tables

- **users** - User authentication and authorization
- **cases** - Legal case management
- **case_documents** - Document metadata and references
- **recommendations** - AI-generated next best actions
- **planner_executions** - Agent orchestration tracking
- **memories** - Agent memory storage
- **feedbacks** - Human-in-the-loop feedback
- **audit_logs** - Complete audit trail

### Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# Show current version
poetry run alembic current

# Show migration history
poetry run alembic history
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_health.py

# View coverage report
open htmlcov/index.html
```

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

#### Health & Monitoring
```
GET  /health        - Basic health check
GET  /ready         - Readiness check with DB verification
GET  /live          - Liveness probe
```

#### Cases
```
POST   /api/v1/cases              - Create new case
GET    /api/v1/cases              - List all cases (paginated)
GET    /api/v1/cases/{id}         - Get case by ID
PATCH  /api/v1/cases/{id}         - Update case
DELETE /api/v1/cases/{id}         - Delete case
```

#### Recommendations
```
POST   /api/v1/recommendations     - Create recommendation
GET    /api/v1/recommendations     - List recommendations
GET    /api/v1/recommendations/{id} - Get recommendation
PATCH  /api/v1/recommendations/{id} - Update recommendation
```

#### Agent Registry
```
GET /api/v1/agents              - List all agents
GET /api/v1/agents/discover     - Discover agents by capabilities
GET /api/v1/agents/{id}         - Get agent metadata
GET /api/v1/agents/stats        - Registry statistics
```

#### Tool Registry
```
GET /api/v1/tools               - List all tools
GET /api/v1/tools/discover      - Discover tools by type
GET /api/v1/tools/{id}          - Get tool metadata
GET /api/v1/tools/stats         - Registry statistics
```

#### Planner & Orchestration (Phase 2)
```
POST /api/v1/planner/execute    - Execute workflow with dynamic planning
POST /api/v1/planner/plan       - Create execution plan without executing
GET  /api/v1/planner/executions/{id} - Get execution status
```

## 🏛️ Design Patterns

### Repository Pattern
Abstracts data access logic from business logic.

### Service Layer
Encapsulates business logic and coordinates between repositories.

### Dependency Injection
All dependencies injected via FastAPI's dependency system.

### Registry Pattern
Dynamic registration and discovery of agents and tools.

### Provider Pattern
Abstract interfaces for memory implementations.

## 🔐 Security

- **JWT Authentication**: Token-based authentication ready for implementation
- **Password Hashing**: BCrypt for secure password storage
- **Role-Based Access**: User roles with permission enums
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS Configuration**: Configurable CORS policies
- **Request Validation**: Pydantic ensures type safety

## 📈 Monitoring & Logging

### Structured Logging

All logs output in JSON format for easy parsing:

```json
{
  "event": "Request completed",
  "request_id": "uuid",
  "method": "GET",
  "path": "/api/v1/cases",
  "status_code": 200,
  "duration_ms": 45.23,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## 🚢 Deployment

### Docker Production Build

```bash
# Build production image
docker build -t lexmind-ai:latest .

# Run container
docker run -d \
  --name lexmind-api \
  -p 8000:8000 \
  -e DATABASE_URL=mysql+aiomysql://... \
  -e SECRET_KEY=... \
  lexmind-ai:latest
```

### Health Checks

Kubernetes-compatible health endpoints:

```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## 🛠️ Development Workflow

```bash
# Format code
poetry run black app/

# Lint code
poetry run ruff app/

# Type checking
poetry run mypy app/

# Run development server with auto-reload
poetry run uvicorn app.main:app --reload
```

## 🔮 Future Phases

### Phase 2: AI Agent Implementation
- Planner Agent with dynamic orchestration
- Legal Research Agent
- Evidence Analysis Agent
- Risk Assessment Agent
- Next Best Action Engine
- Evaluation & Reflection Agents

### Phase 3: RAG & Knowledge
- Vector database integration (ChromaDB)
- Document ingestion pipeline
- Semantic search
- Multi-modal retrieval

### Phase 4: LLM Integration
- Anthropic Claude integration
- LangGraph workflow orchestration
- Prompt management
- Token optimization

### Phase 5: Multi-Domain Support
- Healthcare domain agents
- Insurance domain agents
- Finance domain agents
- Compliance domain agents

## 📄 License

[Your License Here]

## 👥 Contributors

[Your Team Here]

## 📧 Contact

For questions or support, contact [Your Contact Info]

---

**Built with ❤️ for Enterprise AI**
