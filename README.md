# ADR Hub — Architecture Decision Record Management System

**REST API for managing Architecture Decision Records — FastAPI · SQLModel · Clean Architecture**

ADR Hub turns architecture governance from a folder of markdown files into a queryable, auditable system: 7 artifact types with automatic numbering, trigger rules that fire on status changes, cross-artifact references, healthcare compliance fields (LGPD, TCO, health impact), and a health analysis endpoint that surfaces gaps before they become incidents.

---

## Contents

- [Architecture](#architecture)
- [Data Model](#data-model)
- [Artifact Types & Naming](#artifact-types--naming)
- [ADR Level System](#adr-level-system)
- [Status State Machine](#status-state-machine)
- [Trigger System](#trigger-system)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Docker Deployment](#docker-deployment)
- [Roadmap](#roadmap)
- [License](#license)

---

## Architecture

### Clean Architecture Layers

```mermaid
flowchart TB
    subgraph Client
        HTTP([HTTP Client])
    end

    subgraph API["API Layer — src/api/"]
        A1[artifacts.py]
        A2[squads.py]
        A3[trigger_rules.py]
        A4[health.py]
    end

    subgraph Services["Service Layer — src/services/"]
        S1[ArtifactService]
        S2[SquadService]
        S3[TriggerService]
        S4[TemplateService]
        S5[HealthService]
    end

    subgraph Models["Models Layer — src/models/"]
        M1[Artifact]
        M2[Squad]
        M3[TriggerRule]
        M4[ArtifactReference]
    end

    subgraph Persistence
        DB[(locale/governance.db<br/>SQLite)]
        FS[architecture/<br/>Markdown files]
    end

    HTTP -->|HTTP Request| API
    API -->|Depends injection| Services
    Services -->|Pydantic validation| Models
    Services -->|SQLModel ORM| DB
    Services -->|Path.write_text| FS
    DB -->|Query results| Services
    Services -->|Response models| API
    API -->|HTTP Response| HTTP
```

### Request Lifecycle — Create Artifact

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant AS as ArtifactService
    participant TS as TemplateService
    participant TRG as TriggerService
    participant DB as SQLite
    participant FS as FileSystem

    C->>R: POST /api/artifacts/ {type=adr, number=auto}
    R->>AS: create_artifact(data)
    AS->>DB: SELECT squad — validate exists & active
    AS->>AS: _generate_artifact_number(type, level, session)
    AS->>TS: generate_content_for_artifact(data)
    TS->>TS: load template + substitute placeholders
    TS-->>AS: rendered markdown
    AS->>DB: INSERT artifact
    AS->>FS: write architecture/decisions/ADR-003-001.md
    AS->>TRG: process_artifact_triggers(artifact)
    TRG->>DB: SELECT trigger_rules WHERE source_type=adr
    TRG->>TRG: evaluate_condition() — safe AST eval
    alt auto_create rule matched
        TRG->>DB: INSERT triggered artifact
        TRG->>DB: INSERT artifact_reference (both directions)
    end
    TRG-->>AS: triggered artifacts list
    AS-->>R: ArtifactRead
    R-->>C: 201 Created
```

---

## Data Model

```mermaid
erDiagram
    SQUAD {
        int     id              PK
        string  squad_code      UK
        string  name
        string  tech_lead
        string  status
        string  discontinued_reason
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    ARTIFACT {
        int     id              PK
        string  artifact_type
        string  artifact_number UK
        string  title
        string  status
        int     level
        text    content
        string  file_path
        string  template_used
        int     squad_id        FK
        int     triggered_by_id FK
        string  trigger_reason
        string  tco_estimate
        string  lgpd_analysis
        string  rfc_status
        string  health_compliance_impact
        string  created_by_ip
        datetime created_at
        datetime updated_at
    }

    TRIGGER_RULE {
        int     id              PK
        string  source_type
        string  source_condition
        string  target_type
        bool    auto_create
        bool    required
        string  description
        datetime created_at
    }

    ARTIFACT_REFERENCE {
        int     id              PK
        int     from_artifact_id FK
        int     to_artifact_id   FK
        string  reference_type
        datetime created_at
    }

    SQUAD            ||--o{  ARTIFACT           : "owns"
    ARTIFACT         ||--o{  ARTIFACT           : "triggered_by (self)"
    ARTIFACT         ||--o{  ARTIFACT_REFERENCE : "from"
    ARTIFACT         ||--o{  ARTIFACT_REFERENCE : "to"
```

---

## Artifact Types & Naming

Seven types, each persisted as a markdown file under `architecture/` and indexed in the database:

| Type | Folder | Auto-number pattern | Example |
|---|---|---|---|
| `adr` | `architecture/decisions/` | `ADR-{level:03d}-{seq:03d}` | `ADR-003-001` |
| `rfc` | `architecture/rfcs/` | `RFC-{year}-{seq:03d}` | `RFC-2026-001` |
| `evidence` | `architecture/evidence/` | `EVI-{year}-{seq:03d}` | `EVI-2026-001` |
| `governance` | `architecture/governance/` | `GOV-{year}-{seq:03d}` | `GOV-2026-001` |
| `implementation` | `architecture/implementation/` | `IMP-{seq:03d}` | `IMP-001` |
| `visibility` | `architecture/visibility/` | `VIS-{seq:03d}` | `VIS-001` |
| `uncommon` | `architecture/uncommon/` | `UNC-{year}-{seq:03d}` | `UNC-2026-001` |

Pass `"artifact_number": "auto"` to have it generated. Once assigned, `artifact_number` is **immutable**.

On `discontinued` status: file moves to `architecture/discontinued/` and `file_path` updates in DB.

Each type has a markdown template in its `templates/` subfolder. Supported placeholders: `{{ARTIFACT_NUMBER}}`, `{{TITLE}}`, `{{DATE}}`, `{{SQUAD}}`, `{{STATUS}}`, `{{TRIGGERED_BY}}`, `{{TRIGGERED_BY_TITLE}}`, `{{LEVEL}}`, `{{AUTHOR}}`.

---

## ADR Level System

`level` only applies to `artifact_type=adr`. Each level adds validation requirements:

```mermaid
flowchart LR
    L1["**Level 1**<br/>Operational<br/>Sophie decides"]
    L2["**Level 2**<br/>Component<br/>Sophie decides"]
    L3["**Level 3**<br/>Platform<br/>Thiago approves<br/>─────────────<br/>rfc_status required"]
    L4["**Level 4**<br/>Strategic<br/>Thiago + Silvana<br/>─────────────<br/>+ tco_estimate<br/>+ lgpd_analysis"]
    L5["**Level 5**<br/>Principle<br/>Org-wide<br/>Semestral review<br/>─────────────<br/>+ health_compliance<br/>_impact optional"]

    L1 --- L2 --- L3 --- L4 --- L5
```

| Level | Approver | Required fields |
|---|---|---|
| 1–2 | Sophie | — |
| 3 | Thiago | `rfc_status` |
| 4–5 | Thiago + Silvana | `rfc_status`, `tco_estimate`, `lgpd_analysis` |

---

## Status State Machine

```mermaid
stateDiagram-v2
    [*] --> proposed

    proposed --> accepted   : approve
    proposed --> rejected   : reject

    accepted --> superseded  : new artifact replaces it<br/>(requires superseded_by)
    accepted --> discontinued : retire

    rejected --> reopened   : reconsider

    reopened --> accepted   : approve
    reopened --> rejected   : reject again

    superseded  --> [*] : terminal
    discontinued --> [*] : terminal
```

- `superseded` requires `superseded_by` field (artifact number of the replacement)
- `rejected` requires `rejection_reason`
- Terminal states cannot transition to anything

---

## Trigger System

Rules define automatic relationships between artifact types, evaluated on every status change.

```mermaid
flowchart LR
    ADR3["ADR · level ≥ 3"]         -->|"required<br/>blocks accepted<br/>without linked RFC"| RFC
    ADR4["ADR · level ≥ 4"]         -->|suggested| EVI[Evidence]
    ADR5["ADR · level = 5"]         -->|"auto-creates<br/>Governance doc"| GOV[Governance]
    RFCA["RFC · status = accepted"] -->|notify| ADRUPD["ADR update<br/>suggested"]
```

| Source | Condition | Target | Auto-create | Required |
|---|---|---|---|---|
| `adr` | `level >= 3` | `rfc` | No | **Yes** — blocks `accepted` if no RFC linked |
| `adr` | `level >= 4` | `evidence` | No | No |
| `adr` | `level == 5` | `governance` | **Yes** | No |
| `rfc` | `status == 'accepted'` | `adr` | No | No |

### Evaluation Flow

```mermaid
flowchart TD
    PATCH["PATCH /status"]
    LOAD["Load trigger rules<br/>for source_type"]
    EVAL["evaluate_condition()<br/>safe AST — whitelist only"]
    MET{condition<br/>met?}
    REQ{required?}
    AUTO{auto_create?}
    BLOCK["ValueError:<br/>required trigger<br/>not satisfied"]
    CREATE["INSERT target artifact<br/>with triggered_by_id"]
    REF["INSERT artifact_reference<br/>both directions"]
    OK["Status updated ✓"]

    PATCH --> LOAD --> EVAL --> MET
    MET -->|No| REQ
    REQ -->|Yes| BLOCK
    REQ -->|No| OK
    MET -->|Yes| AUTO
    AUTO -->|Yes| CREATE --> REF --> OK
    AUTO -->|No| OK
```

Safe eval whitelist: `level`, `status`, `artifact_type` with operators `==`, `!=`, `>=`, `<=`, `>`, `<`, `and`, `or`, `not`. No `eval()` on user input — AST validation rejects any dangerous pattern.

---

## API Reference

### Artifacts — `/api/artifacts`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/artifacts/` | List all (filter: `artifact_type`, `status`, `squad_id`, `level`) |
| `POST` | `/api/artifacts/` | Create artifact |
| `GET` | `/api/artifacts/search` | Full-text search in title + content |
| `GET` | `/api/artifacts/types` | List valid artifact types |
| `GET` | `/api/artifacts/statuses` | List valid statuses |
| `GET` | `/api/artifacts/{id}` | Get by ID |
| `PUT` | `/api/artifacts/{id}` | Update fields |
| `DELETE` | `/api/artifacts/{id}` | Delete |
| `PATCH` | `/api/artifacts/{id}/status` | Update status + trigger evaluation |
| `GET` | `/api/artifacts/{id}/file` | Download markdown file |

### Squads — `/api/squads`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/squads/` | Create |
| `GET` | `/api/squads/` | List |
| `GET` | `/api/squads/{code}` | Get by code |
| `PATCH` | `/api/squads/{code}` | Update |
| `DELETE` | `/api/squads/{code}` | Soft delete |
| `GET` | `/api/squads/{code}/artifacts` | All artifacts for squad |

### Trigger Rules — `/api/triggers`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/triggers/` | List (filter: `source_type`, `target_type`) |
| `POST` | `/api/triggers/` | Create rule |
| `GET` | `/api/triggers/{id}` | Get rule |
| `PUT` | `/api/triggers/{id}` | Update rule |
| `DELETE` | `/api/triggers/{id}` | Delete rule |
| `POST` | `/api/triggers/test-evaluate` | Evaluate condition against a given artifact |
| `GET` | `/api/triggers/suggestions/{artifact_id}` | Suggestions for an artifact |

### Health — `/api/health`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health/` | Full ecosystem analysis |
| `GET` | `/api/health/readiness` | Database + filesystem ready check |
| `GET` | `/api/health/liveness` | Process alive check |
| `GET` | `/api/health/metrics` | Counts by type and status |

Health response:

```json
{
  "generated_at": "2026-04-08T12:00:00",
  "summary": {
    "total_artifacts": 42,
    "by_type": { "adr": 18, "rfc": 9, "evidence": 6 },
    "by_status": { "proposed": 12, "accepted": 24, "rejected": 6 }
  },
  "issues": [
    {
      "severity": "HIGH",
      "artifact_number": "ADR-003-001",
      "issue": "Level 3 ADR accepted without linked RFC",
      "recommendation": "Create RFC-2026-001 referencing ADR-003-001"
    }
  ]
}
```

### Create Artifact — Example

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
  "created_at": "2026-04-08T12:00:00",
  "updated_at": "2026-04-08T12:00:00"
}
```

---

## Project Structure

```
adr_hub/
├── src/
│   ├── api/
│   │   ├── artifacts.py        # Artifact CRUD + status + file download
│   │   ├── squads.py           # Squad CRUD + squad artifacts
│   │   ├── trigger_rules.py    # Trigger rule CRUD + test-evaluate
│   │   └── health.py           # Readiness · liveness · metrics · analysis
│   ├── models/
│   │   ├── artifact.py         # Artifact + Create/Update/StatusUpdate/Read
│   │   ├── artifact_reference.py
│   │   ├── squad.py
│   │   └── trigger_rule.py
│   ├── services/
│   │   ├── artifact_service.py # CRUD · auto-numbering · file generation
│   │   ├── squad_service.py
│   │   ├── trigger_service.py  # Safe AST condition eval · auto-create
│   │   ├── template_service.py # Template load · placeholder substitution
│   │   └── health_service.py   # Ecosystem analysis
│   ├── database/
│   │   └── engine.py           # Engine · session factory · create_all
│   └── main.py                 # App · routers · on_startup
├── tests/
│   ├── conftest.py             # session · client · test_squad_data · test_artifact_data
│   ├── test_artifacts.py       # ArtifactService unit tests (~36)
│   ├── test_api_artifacts.py   # API integration tests
│   ├── test_squads.py          # Squad tests
│   ├── test_triggers.py        # Trigger evaluation
│   ├── test_templates.py       # Template service
│   ├── test_health.py          # Health endpoints
│   ├── test_schema.py          # Model validation
│   └── test_with_subprocess.py # Import smoke tests (7)
├── architecture/
│   ├── decisions/templates/    # ADR templates level 1–5
│   ├── rfcs/templates/
│   ├── evidence/templates/
│   ├── governance/templates/
│   ├── implementation/templates/
│   ├── visibility/templates/
│   ├── uncommon/templates/
│   └── discontinued/           # Files land here on discontinued status
├── locale/
│   └── governance.db           # SQLite production database
├── main.py                     # Entry point
├── requirements.txt
├── pytest.ini
└── .github/workflows/ci.yml

---

## Quick Start

```bash
git clone https://github.com/sophie-pyxis/adr_hub.git
cd adr_hub

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload
```

| URL | Description |
|---|---|
| `http://localhost:8000` | Root |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |

**Environment variable** (optional):

```env
DATABASE_URL=sqlite:///./locale/governance.db
# PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/adr_hub
```

---

## Testing

Every test gets a fresh in-memory SQLite database. No real filesystem access in unit tests — template tests use `tmp_path`. No hardcoded paths anywhere.

```bash
# Full suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Single file
pytest tests/test_artifacts.py -v

# Single test
pytest tests/test_artifacts.py::test_create_artifact_with_auto_number -v
```

### Test Layout

```mermaid
flowchart LR
    CF["conftest.py<br/>session fixture<br/>client fixture<br/>test data factories"]

    CF --> TA["test_artifacts.py<br/>ArtifactService unit"]
    CF --> TAA["test_api_artifacts.py<br/>API integration"]
    CF --> TS["test_squads.py"]
    CF --> TT["test_triggers.py<br/>safe AST eval<br/>auto-create flow"]
    CF --> TTEM["test_templates.py<br/>tmp_path isolation"]
    CF --> TH["test_health.py"]
    CF --> TSC["test_schema.py<br/>model validation"]
    CF --> TWS["test_with_subprocess.py<br/>import smoke tests"]
```

### Test Coverage

- **Overall Coverage**: 74%
- **Key Service Coverage**:
  - `artifact_service.py`: 7%
  - `squad_service.py`: 36%
  - `template_service.py`: 16%
  - `trigger_service.py`: 17%
  - `health_service.py`: 25%
  - API endpoints: 46-53%

---

## CI/CD

```mermaid
flowchart LR
    PR["push / PR"] --> T
    T["test<br/>Python 3.9 · 3.10 · 3.11<br/>pytest + coverage"] --> L
    L["lint<br/>Black · Flake8<br/>isort · mypy"] --> S
    S["security<br/>Bandit · Safety"] --> OK["✅ green"]
```

### GitHub Actions Pipeline

Located in `.github/workflows/ci.yml`:

| Job | Description |
|---|---|
| **test** | Runs tests on Python 3.9, 3.10, 3.11 with 74% coverage |
| **lint** | Code formatting (Black), linting (Flake8), imports (isort), types (mypy) |
| **security** | Security scanning (Bandit) and dependency checks (Safety) |

### Pipeline Features
- **Matrix testing**: Multiple Python versions
- **Coverage upload**: Codecov integration
- **Quality gates**: 74% test coverage required
- **Security scanning**: Proactive vulnerability detection

---

## Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

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

---

## Roadmap

- [ ] JWT auth + role-based access (Architect / TechLead / Viewer)
- [ ] Webhook notifications on status changes
- [ ] Export to PDF
- [ ] Alembic migrations for PostgreSQL
- [ ] `@app.on_event` → `lifespan` (FastAPI modern pattern)
- [ ] `class Config` → `model_config = ConfigDict(...)` (Pydantic v2 full migration)
- [ ] Rate limiting

---

## License

MIT — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SQLModel** for combining SQLAlchemy and Pydantic
- **Pydantic** for robust data validation
- **The ADR community** for establishing best practices

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/sophie-pyxis/adr_hub/issues)
- **Documentation**: Check the `/docs` endpoint when running the API
- **Community**: Join discussions in GitHub Discussions

---

**ADR Hub** — Making architecture decisions trackable, auditable, and collaborative. 🏛️