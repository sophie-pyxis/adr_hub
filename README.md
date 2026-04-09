# ADR Hub — Architecture Decision Record Management System

**REST API for managing Architecture Decision Records — FastAPI · SQLModel · Clean Architecture**

ADR Hub transforms architecture governance from scattered markdown files into a queryable, auditable system with 7 artifact types, automatic numbering, trigger rules, cross-references, healthcare compliance fields, and proactive health analysis.

---

## Contents

- [Architecture Overview](#architecture-overview)
- [Core Concepts](#core-concepts)
- [System Architecture](#system-architecture)
- [Data Model](#data-model)
- [Artifact Types](#artifact-types)
- [ADR Level System](#adr-level-system)
- [Status Management](#status-management)
- [Trigger System](#trigger-system)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [License](#license)
- [Solutions Architect Handbook](#solutions-architect-handbook)

---

## Architecture Overview

ADR Hub follows Clean Architecture principles with clear separation of concerns:

```mermaid
flowchart LR
    Client[HTTP Client] --> API[API Layer]
    API --> Services[Service Layer]
    Services --> Models[Models Layer]
    Services --> Persistence[(Persistence)]
```

### Key Architectural Principles

1. **Separation of Concerns**: Clear boundaries between API, business logic, and data access
2. **Dependency Inversion**: High-level modules don't depend on low-level implementations
3. **Testability**: All components are independently testable with dependency injection
4. **Maintainability**: Modular design with single responsibility per component

---

## Core Concepts

### 1. Artifacts
Seven distinct artifact types for comprehensive architecture governance:
- **ADR**: Architecture Decision Records (levels 1-5)
- **RFC**: Request for Comments
- **Evidence**: Supporting evidence for decisions
- **Governance**: Policy and compliance documents
- **Implementation**: Technical implementation details
- **Visibility**: System observability decisions
- **Uncommon**: Edge cases and special scenarios

### 2. Squads
Development teams that own artifacts, with lifecycle management:
- Active, inactive, or discontinued status
- Tech lead assignment
- Artifact ownership tracking

### 3. Trigger Rules
Automated relationships between artifacts:
- Condition-based evaluation
- Auto-creation of related artifacts
- Required vs. suggested triggers

### 4. Health Analysis
Proactive system monitoring:
- Compliance gap detection
- Missing artifact identification
- Ecosystem health scoring

---

## System Architecture

### 1. Clean Architecture Layers

**API Layer** (`src/api/`):
```mermaid
flowchart TB
    subgraph API["API Layer"]
        A1[artifacts.py]
        A2[squads.py]
        A3[trigger_rules.py]
        A4[health.py]
    end
    
    API -->|HTTP| Client[HTTP Client]
    API -->|Depends| Services[Service Layer]
```

**Service Layer** (`src/services/`):
```mermaid
flowchart TB
    subgraph Services["Service Layer"]
        S1[ArtifactService]
        S2[SquadService]
        S3[TriggerService]
        S4[TemplateService]
        S5[HealthService]
    end
    
    Services -->|Business Logic| API[API Layer]
    Services -->|Data Access| Models[Models Layer]
```

**Models Layer** (`src/models/`):
```mermaid
flowchart TB
    subgraph Models["Models Layer"]
        M1[Artifact]
        M2[Squad]
        M3[TriggerRule]
        M4[ArtifactReference]
    end
    
    Models -->|Validation| Services[Service Layer]
    Models -->|ORM| DB[(Database)]
```

### 2. Request Flow

**Create Artifact Sequence**:
```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Router
    participant AS as ArtifactService
    participant DB as Database
    
    C->>API: POST /api/artifacts
    API->>AS: create_artifact(data)
    AS->>DB: Validate squad
    AS->>AS: Generate artifact number
    AS->>DB: Create artifact record
    AS->>FS: Write markdown file
    AS-->>API: ArtifactRead
    API-->>C: 201 Created
```

**Trigger Evaluation Flow**:
```mermaid
sequenceDiagram
    participant AS as ArtifactService
    participant TS as TriggerService
    participant DB as Database
    
    AS->>TS: process_artifact_triggers(artifact)
    TS->>DB: Load trigger rules
    TS->>TS: Evaluate conditions
    alt Condition Met
        TS->>DB: Create related artifact
        TS->>DB: Create references
    end
    TS-->>AS: Trigger results
```

### 3. Deployment Architecture

```mermaid
flowchart TB
    subgraph Cloud["Cloud Environment"]
        LB[Load Balancer]
        subgraph App["Application Tier"]
            A1[API Instance 1]
            A2[API Instance 2]
        end
        subgraph Data["Data Tier"]
            DB[(PostgreSQL)]
            FS[File Storage]
        end
    end
    
    User[End User] --> LB
    LB --> A1
    LB --> A2
    A1 --> DB
    A2 --> DB
    A1 --> FS
    A2 --> FS
```

---

## Data Model

### Entity Relationships

```mermaid
erDiagram
    SQUAD ||--o{ ARTIFACT : owns
    ARTIFACT ||--o{ ARTIFACT_REFERENCE : references
    TRIGGER_RULE }o--o{ ARTIFACT : triggers
```

### Core Entities

**Squad**:
```yaml
id: int (PK)
squad_code: string (UK)
name: string
tech_lead: string
status: string
created_at: datetime
updated_at: datetime
deleted_at: datetime (soft delete)
```

**Artifact**:
```yaml
id: int (PK)
artifact_type: string
artifact_number: string (UK)
title: string
status: string
level: int (1-5, ADR only)
content: text
squad_id: int (FK)
triggered_by_id: int (FK, self-reference)
```

**TriggerRule**:
```yaml
id: int (PK)
source_type: string
source_condition: string
target_type: string
auto_create: boolean
required: boolean
description: string
```

---

## Artifact Types

| Type | Folder | Number Pattern | Example |
|------|--------|----------------|---------|
| `adr` | `architecture/decisions/` | `ADR-{level:03d}-{seq:03d}` | `ADR-003-001` |
| `rfc` | `architecture/rfcs/` | `RFC-{year}-{seq:03d}` | `RFC-2026-001` |
| `evidence` | `architecture/evidence/` | `EVI-{year}-{seq:03d}` | `EVI-2026-001` |
| `governance` | `architecture/governance/` | `GOV-{year}-{seq:03d}` | `GOV-2026-001` |
| `implementation` | `architecture/implementation/` | `IMP-{seq:03d}` | `IMP-001` |
| `visibility` | `architecture/visibility/` | `VIS-{seq:03d}` | `VIS-001` |
| `uncommon` | `architecture/uncommon/` | `UNC-{year}-{seq:03d}` | `UNC-2026-001` |

### Number Generation Logic

```mermaid
flowchart TD
    Start["Create Artifact"] --> Type{"Artifact Type?"}
    
    Type -->|ADR| ADR["Generate ADR Number"]
    ADR --> Level["Get level-specific sequence"]
    ADR --> Format["Format: ADR-{level}-{seq}"]
    
    Type -->|RFC| RFC["Generate RFC Number"]
    RFC --> Year["Use current year"]
    RFC --> RSeq["Get year-specific sequence"]
    RFC --> RFormat["Format: RFC-{year}-{seq}"]
    
    Type -->|Other| Other["Generate Generic Number"]
    Other --> OSeq["Get type-specific sequence"]
    Other --> OFormat["Format: {PREFIX}-{seq}"]
    
    Format --> Done["Return Number"]
    RFormat --> Done
    OFormat --> Done
```

---

## ADR Level System

### Level Definitions

```mermaid
flowchart LR
    L1["Level 1<br/>Operational<br/>Tech Lead approves"]
    L2["Level 2<br/>Component<br/>Tech Lead approves"]
    L3["Level 3<br/>Platform<br/>Architect approves"]
    L4["Level 4<br/>Strategic<br/>Architect + Business Manager"]
    L5["Level 5<br/>Principle<br/>Organization-wide"]
    
    L1 --> L2 --> L3 --> L4 --> L5
```

### Validation Requirements

| Level | Approver Role | Required Fields |
|-------|--------------|-----------------|
| 1–2 | Tech Lead | — |
| 3 | Architect | `rfc_status` |
| 4–5 | Architect + Business Manager | `rfc_status`, `tco_estimate`, `lgpd_analysis` |

### Compliance Fields
- **TCO Estimate**: Total Cost of Ownership (levels 4-5)
- **LGPD Analysis**: Brazilian GDPR compliance (levels 4-5)
- **Health Compliance Impact**: Healthcare regulations (level 5 optional)

---

## Status Management

### State Machine

```mermaid
stateDiagram-v2
    [*] --> proposed
    
    proposed --> accepted   : approve
    proposed --> rejected   : reject
    
    accepted --> superseded  : replace
    accepted --> discontinued : retire
    
    rejected --> reopened   : reconsider
    
    reopened --> accepted   : approve
    reopened --> rejected   : reject again
    
    superseded  --> [*]
    discontinued --> [*]
```

### Status Rules
- **superseded**: Requires `superseded_by` field
- **rejected**: Requires `rejection_reason`
- **discontinued**: File moves to `architecture/discontinued/`
- Terminal states (`superseded`, `discontinued`) cannot transition

---

## Trigger System

### Rule Types

```mermaid
flowchart LR
    ADR3["ADR Level ≥ 3"] -->|required| RFC
    ADR4["ADR Level ≥ 4"] -->|suggested| Evidence
    ADR5["ADR Level = 5"] -->|auto-create| Governance
    RFCA["RFC Accepted"] -->|notify| ADRUpdate
```

### Evaluation Engine

```mermaid
flowchart TD
    Start[Status Update] --> Load[Load Rules]
    Load --> Eval[Evaluate Condition]
    Eval --> Met{Condition Met?}
    
    Met -->|No| Required{Required?}
    Required -->|Yes| Block[Block Update]
    Required -->|No| OK[Allow Update]
    
    Met -->|Yes| Auto{Auto-create?}
    Auto -->|Yes| Create[Create Artifact]
    Create --> Ref[Create Reference]
    Ref --> OK
    
    Auto -->|No| OK
```

### Safe Condition Evaluation
- **AST-based parsing**: No `eval()` on user input
- **Whitelisted operators**: `==`, `!=`, `>=`, `<=`, `>`, `<`, `and`, `or`, `not`
- **Allowed attributes**: `level`, `status`, `artifact_type`, `title`, `content`
- **Security**: Rejects dangerous patterns during AST validation

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
*Currently none (planned: JWT + role-based access)*

### Artifacts (`/api/artifacts`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/artifacts/` | List artifacts (filter by type, status, squad, level) |
| `POST` | `/api/artifacts/` | Create artifact |
| `GET` | `/api/artifacts/search` | Full-text search |
| `GET` | `/api/artifacts/{id}` | Get by ID |
| `PUT` | `/api/artifacts/{id}` | Update artifact |
| `DELETE` | `/api/artifacts/{id}` | Delete artifact |
| `PATCH` | `/api/artifacts/{id}/status` | Update status (triggers evaluation) |
| `GET` | `/api/artifacts/{id}/file` | Download markdown file |

### Squads (`/api/squads`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/squads/` | Create squad |
| `GET` | `/api/squads/` | List squads |
| `GET` | `/api/squads/{code}` | Get by code |
| `PATCH` | `/api/squads/{code}` | Update squad |
| `DELETE` | `/api/squads/{code}` | Soft delete |
| `GET` | `/api/squads/{code}/artifacts` | Squad artifacts |

### Triggers (`/api/triggers`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/triggers/` | List rules (filter by source/target type) |
| `POST` | `/api/triggers/` | Create rule |
| `GET` | `/api/triggers/{id}` | Get rule |
| `PUT` | `/api/triggers/{id}` | Update rule |
| `DELETE` | `/api/triggers/{id}` | Delete rule |
| `POST` | `/api/triggers/test-evaluate` | Test condition evaluation |
| `GET` | `/api/triggers/suggestions/{id}` | Get suggestions for artifact |

### Health (`/api/health`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health/` | Full ecosystem analysis |
| `GET` | `/api/health/readiness` | Database + filesystem check |
| `GET` | `/api/health/liveness` | Process alive check |
| `GET` | `/api/health/metrics` | Counts by type and status |

### Example: Create ADR

```http
POST /api/artifacts/
Content-Type: application/json

{
  "artifact_type": "adr",
  "artifact_number": "auto",
  "title": "Adopt Azure OpenAI as default LLM provider",
  "level": 3,
  "status": "proposed",
  "content": "## Context\nWe need a managed LLM provider...",
  "rfc_status": "RFC-2026-001 in review",
  "squad_id": 1
}
```

Response:
```json
{
  "id": 7,
  "artifact_type": "adr",
  "artifact_number": "ADR-003-001",
  "title": "Adopt Azure OpenAI as default LLM provider",
  "level": 3,
  "status": "proposed",
  "file_path": "architecture/decisions/ADR-003-001.md",
  "squad_name": "Platform Team",
  "created_at": "2026-04-08T12:00:00Z"
}
```

---

## Project Structure

```
adr_hub/
├── src/
│   ├── api/                    # API Layer
│   │   ├── artifacts.py        # Artifact endpoints
│   │   ├── squads.py           # Squad endpoints
│   │   ├── trigger_rules.py    # Trigger endpoints
│   │   └── health.py           # Health endpoints
│   ├── models/                 # Models Layer
│   │   ├── artifact.py         # Artifact models
│   │   ├── artifact_reference.py
│   │   ├── squad.py           # Squad models
│   │   └── trigger_rule.py    # Trigger models
│   ├── services/              # Service Layer
│   │   ├── artifact_service.py # Artifact business logic
│   │   ├── squad_service.py   # Squad business logic
│   │   ├── trigger_service.py # Trigger evaluation
│   │   ├── template_service.py # Template rendering
│   │   └── health_service.py  # Health monitoring
│   ├── database/              # Data Access
│   │   └── engine.py          # Database engine
│   └── main.py                # FastAPI application
├── tests/                     # Test Suite
│   ├── conftest.py           # Test fixtures
│   ├── test_artifacts.py     # Artifact service tests
│   ├── test_api_artifacts.py # API integration tests
│   ├── test_squads.py        # Squad tests
│   ├── test_triggers.py      # Trigger tests
│   ├── test_templates.py     # Template tests
│   ├── test_health.py        # Health tests
│   ├── test_schema.py        # Model validation tests
│   └── test_with_subprocess.py # Import smoke tests
├── architecture/             # Generated Artifacts
│   ├── decisions/           # ADR markdown files
│   ├── rfcs/               # RFC markdown files
│   ├── evidence/           # Evidence markdown files
│   ├── governance/         # Governance markdown files
│   ├── implementation/     # Implementation markdown files
│   ├── visibility/        # Visibility markdown files
│   ├── uncommon/          # Uncommon markdown files
│   └── discontinued/      # Discontinued artifacts
├── templates/              # Markdown Templates
│   ├── decisions/         # ADR templates (levels 1-5)
│   ├── rfcs/             # RFC templates
│   ├── evidence/         # Evidence templates
│   ├── governance/       # Governance templates
│   ├── implementation/   # Implementation templates
│   ├── visibility/      # Visibility templates
│   └── uncommon/        # Uncommon templates
├── locale/
│   └── governance.db    # SQLite database
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── pytest.ini          # Test configuration
├── SOLUTIONS_ARCHITECT_HANDBOOK.md  # Solutions Architect Handbook
└── .github/workflows/   # CI/CD Pipeline
    └── ci.yml          # GitHub Actions workflow

---

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/sophie-pyxis/adr_hub.git
cd adr_hub

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn main:app --reload
```

### Access Points

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Root endpoint |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc documentation |

### Environment Configuration

```env
# SQLite (default)
DATABASE_URL=sqlite:///./locale/governance.db

# PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/adr_hub
```

---

## Testing

### Test Architecture

```mermaid
flowchart LR
    CF[conftest.py<br/>Fixtures] --> TA[test_artifacts.py<br/>Service Tests]
    CF --> TAA[test_api_artifacts.py<br/>API Tests]
    CF --> TS[test_squads.py<br/>Squad Tests]
    CF --> TT[test_triggers.py<br/>Trigger Tests]
    CF --> TH[test_health.py<br/>Health Tests]
```

### Running Tests

```bash
# Full test suite with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Single test file
pytest tests/test_artifacts.py -v

# Specific test
pytest tests/test_artifacts.py::test_create_artifact_with_auto_number -v
```

### Test Coverage
- **Overall Coverage**: 74% (minimum requirement)
- **Key Services**: ArtifactService (7%), SquadService (36%), TriggerService (17%)
- **API Endpoints**: 46-53% coverage

---

## CI/CD Pipeline

### Pipeline Flow

```mermaid
flowchart LR
    PR[Push/PR] --> Test[Test<br/>Python 3.9-3.11]
    Test --> Lint[Lint<br/>Black · Flake8 · isort · mypy]
    Lint --> Security[Security<br/>Bandit · Safety]
    Security --> Pass[✅ Pipeline Passes]
```

### GitHub Actions Jobs

| Job | Description | Tools |
|-----|-------------|-------|
| **test** | Run tests on Python 3.9, 3.10, 3.11 | pytest, coverage |
| **lint** | Code quality checks | Black, Flake8, isort, mypy |
| **security** | Security scanning | Bandit, Safety |

### Quality Gates
- **Test Coverage**: Minimum 74% required
- **Code Formatting**: Black compliance (88 char line length)
- **Import Sorting**: isort with Black profile
- **Type Checking**: mypy with strict settings
- **Security**: Bandit scanning for vulnerabilities

---

## Deployment

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://postgres:password@db/adr_hub
    depends_on: [db]
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: adr_hub
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes: [postgres_data:/var/lib/postgresql/data]

volumes:
  postgres_data:
```

### Production Considerations

1. **Database**: Use PostgreSQL for production workloads
2. **File Storage**: Cloud storage (S3, Azure Blob) for markdown files
3. **Caching**: Redis for frequently accessed data
4. **Monitoring**: Prometheus metrics, structured logging
5. **Security**: JWT authentication, rate limiting, CORS restrictions

---

## Roadmap

### Short-term (Q2 2026)
- [ ] JWT authentication with role-based access (Architect/TechLead/Viewer)
- [ ] Webhook notifications on status changes
- [ ] Export to PDF functionality
- [ ] Alembic migrations for PostgreSQL

### Medium-term (Q3 2026)
- [ ] Modern FastAPI patterns (`lifespan` instead of `on_event`)
- [ ] Pydantic v2 full migration (`model_config` pattern)
- [ ] Rate limiting and API throttling
- [ ] Advanced search with Elasticsearch integration

### Long-term (Q4 2026+)
- [ ] GraphQL API alongside REST
- [ ] Real-time collaboration features
- [ ] Machine learning for artifact suggestions
- [ ] Integration with project management tools (Jira, Linear)

---

## Solutions Architect Handbook

For comprehensive guidance on implementing, operating, and extending ADR Hub in enterprise environments, refer to the [Solutions Architect Handbook](SOLUTIONS_ARCHITECT_HANDBOOK.md).

The handbook provides detailed information for solution architects and enterprise architects, including:

- **Enterprise Architecture Patterns**: Detailed system architecture with Mermaid diagrams
- **Deployment Strategies**: Development, production, and high-availability configurations
- **Security Architecture**: Authentication, authorization, and compliance controls
- **Monitoring & Observability**: Health checks, metrics, logging, and alerting
- **Operational Procedures**: Deployment, backup, incident response, and capacity planning
- **Extension & Customization**: Plugin architecture and integration patterns

---

## License

MIT License — see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SQLModel** for combining SQLAlchemy and Pydantic
- **Pydantic** for robust data validation
- **The ADR community** for establishing best practices
- **Scarlet Rose** for insights on solutions architecture from her YouTube channel: [LinkedIn](https://www.linkedin.com/in/scarletrose/) | [GitHub](https://github.com/scarletquasar) | [YouTube](https://www.youtube.com/watch?v=MYq4v6S8BHE)

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/sophie-pyxis/adr_hub/issues)
- **Documentation**: Check the `/docs` endpoint when running the API
- **Community**: Join discussions in GitHub Discussions

---

**ADR Hub** — Making architecture decisions trackable, auditable, and collaborative. 🏛️

**Created by**: {{PRINCIPAL_ARCHITECT}} ([LinkedIn](https://www.linkedin.com/in/sophie-pyxis) | [GitHub](https://github.com/sophie-pyxis))  
**Repository**: https://github.com/sophie-pyxis/adr_hub