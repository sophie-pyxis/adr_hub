# ADR Hub — Architecture Decision Record Management System

**ADR Hub** is a modern, open-source REST API for managing Architecture Decision Records (ADRs) with Clean Architecture, built with FastAPI and SQLModel. Designed for teams that need structured, auditable decision tracking with compliance and governance features.

---

## 🎯 Project Overview

ADR Hub transforms the traditional file-based ADR management into a fully-featured API with:
- **RESTful endpoints** for all CRUD operations
- **Clean Architecture** with clear separation of concerns
- **Comprehensive validation** with Pydantic v2
- **Database persistence** with SQLModel (SQLAlchemy + Pydantic)
- **Full test coverage** with isolated in-memory SQLite
- **CI/CD pipeline** with GitHub Actions
- **OpenAPI documentation** automatically generated

### Why ADR Hub?
- **From CLI to API**: Evolved from a CLI tool to a modern REST API
- **Production Ready**: Built with enterprise-grade validation and error handling
- **Extensible**: Clean architecture makes it easy to add new features
- **Open Source**: MIT licensed, community-driven development

---

## 🏗️ Architecture

### Clean Architecture Layers

```mermaid
flowchart TD
    Client([HTTP Client])
    API[API Layer<br/>FastAPI Routers]
    Services[Service Layer<br/>Business Logic]
    Models[Models Layer<br/>Pydantic + SQLModel]
    Database[(Database<br/>SQLite/PostgreSQL)]

    Client -->|HTTP Request| API
    API -->|Dependency Injection| Services
    Services -->|Data Validation| Models
    Services -->|Persistence| Database
    Database -->|Query Results| Services
    Services -->|Response Data| API
    API -->|HTTP Response| Client
```

### Directory Structure
```
adr_hub/
├── src/
│   ├── api/                    # FastAPI routers
│   │   ├── adrs.py            # ADR endpoints
│   │   └── squads.py          # Squad endpoints
│   ├── models/                # Pydantic + SQLModel schemas
│   │   ├── adr.py            # ADR models & validation
│   │   └── squad.py          # Squad models & validation
│   ├── services/              # Business logic layer
│   │   ├── adr_service.py    # ADR business logic
│   │   └── squad_service.py  # Squad business logic
│   ├── core/                  # Domain entities
│   └── database.py           # Database session management
├── tests/                     # Comprehensive test suite
│   ├── test_adrs.py          # ADR API tests
│   └── test_squads.py        # Squad API tests
├── .github/workflows/        # CI/CD pipelines
├── docs/                     # Documentation
├── locale/                   # Production data directory
├── main.py                   # FastAPI application entry
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
└── README.md                # This file
```

---

## 📊 Features

### ADR Management
- **Auto-numbering**: Automatic ADR number generation with "auto" keyword
- **Level-based validation**:
  - Level 1-2: Basic validation
  - Level 3+: RFC status required
  - Level 4+: TCO estimate and LGPD analysis required
- **Status workflow**: Proposed → Accepted/Rejected/Superseded/Discontinued
- **Healthcare compliance**: Optional health compliance impact for healthcare organizations

### Squad Management
- **Team organization**: Group ADRs by squads/teams
- **Soft delete**: Status-based deactivation (active, discontinued)
- **Validation**: Cannot create ADRs for discontinued squads
- **Unique constraints**: Squad code must be unique

### API Features
- **Filtering**: List ADRs by level, status, or squad
- **Search**: Full-text search in titles and content
- **Pagination**: Skip/limit parameters for large datasets
- **Validation**: Comprehensive input validation with clear error messages
- **OpenAPI**: Automatic documentation at `/docs` and `/redoc`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/adr-hub.git
cd adr-hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API
```bash
# Start the FastAPI server
uvicorn main:app --reload

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Running Tests
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_adrs.py -v
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### ADR Endpoints

#### `POST /adrs/` — Create a new ADR
```http
POST /adrs/
Content-Type: application/json

{
  "adr_number": "auto",
  "title": "Use FastAPI for new microservices",
  "level": 3,
  "status": "proposed",
  "content": "## Context\nWe need to choose a web framework...",
  "rfc_status": "RFC-2024-001 completed",
  "squad_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "adr_number": "ADR-003-001",
  "title": "Use FastAPI for new microservices",
  "level": 3,
  "status": "proposed",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "squad_name": "Platform Team"
}
```

#### `GET /adrs/` — List ADRs with filtering
```http
GET /adrs/?level=3&status=accepted&skip=0&limit=10
```

#### `GET /adrs/{adr_number}` — Get specific ADR
```http
GET /adrs/ADR-003-001
```

#### `PATCH /adrs/{adr_number}` — Update ADR fields
```http
PATCH /adrs/ADR-003-001
Content-Type: application/json

{
  "title": "Updated title",
  "content": "Updated content with more details"
}
```

#### `PATCH /adrs/{adr_number}/status` — Update ADR status
```http
PATCH /adrs/ADR-003-001/status
Content-Type: application/json

{
  "status": "accepted"
}
```

#### `GET /adrs/search/` — Search ADRs
```http
GET /adrs/search/?q=microservices&skip=0&limit=10
```

### Squad Endpoints

#### `POST /squads/` — Create a new squad
```http
POST /squads/
Content-Type: application/json

{
  "name": "Platform Team",
  "squad_code": "PLAT",
  "tech_lead": "Jane Doe",
  "description": "Platform infrastructure team"
}
```

#### `GET /squads/` — List all squads
```http
GET /squads/
```

#### `GET /squads/{squad_code}` — Get specific squad
```http
GET /squads/PLAT
```

#### `PATCH /squads/{squad_code}` — Update squad
```http
PATCH /squads/PLAT
Content-Type: application/json

{
  "description": "Updated team description"
}
```

#### `PATCH /squads/{squad_code}/status` — Update squad status
```http
PATCH /squads/PLAT/status
Content-Type: application/json

{
  "status": "discontinued",
  "discontinued_reason": "Team reorganized"
}
```

---

## 🧪 Testing

### Test Strategy
- **Isolation**: In-memory SQLite database for each test
- **Fixtures**: Reusable test data factories
- **Coverage**: 95% minimum threshold enforced
- **Test types**: Unit, integration, and API endpoint tests

### Running Tests
```bash
# Run all tests with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Run specific test category
pytest tests/test_adrs.py::test_create_adr -v

# Run tests with coverage threshold check
pytest tests/ --cov=src --cov-fail-under=75
```

### Test Coverage
- **Overall Coverage**: 54%
- **Key Service Coverage**:
  - `adr_service.py`: 87%
  - `squad_service.py`: 94%
  - API endpoints: 100%

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
DATABASE_URL=sqlite:///./adr_hub.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/adr_hub
```

### Database Setup
The system uses SQLite by default. For production, PostgreSQL is recommended:

```python
# In src/database.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./adr_hub.db")
```

### Pytest Configuration (`pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow
Located in `.github/workflows/ci.yml`:

| Job | Description |
|-----|-------------|
| **test** | Runs tests on Python 3.9, 3.10, 3.11 with 75% coverage |
| **lint** | Code formatting (Black), linting (Flake8), imports (isort), types (mypy) |
| **security** | Security scanning (Bandit) and dependency checks (Safety) |

### Pipeline Features
- **Matrix testing**: Multiple Python versions
- **Coverage upload**: Codecov integration
- **Quality gates**: 75% test coverage required
- **Security scanning**: Proactive vulnerability detection

---

## 📈 ADR Levels & Validation

### Level Definitions
| Level | Description | Requirements |
|-------|-------------|--------------|
| **1** | Minor decision | Basic validation |
| **2** | Team decision | Basic validation |
| **3** | Cross-team decision | RFC status required |
| **4** | Organizational decision | TCO estimate, LGPD analysis, RFC status |
| **5** | Architectural principle | TCO estimate, LGPD analysis, RFC status |

### Validation Rules
1. **ADR Number**: Format `ADR-XXX-XXX` or `"auto"` for auto-generation
2. **Status Transitions**: Valid state machine enforcement
3. **Squad Validation**: Cannot create ADRs for discontinued squads
4. **Level Requirements**: Enforced at creation and update

### Healthcare Compliance (Optional)
For healthcare organizations, level 4+ ADRs can include:
- **Health compliance impact**: Analysis of healthcare regulations
- **LGPD analysis**: Brazilian GDPR compliance (required for level 4+)
- **TCO estimate**: Total Cost of Ownership analysis (required for level 4+)

---

## 🛠️ Development

### Setting Up Development Environment
```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 isort mypy pytest pytest-cov

# Set up pre-commit hooks (optional)
pre-commit install
```

### Code Style
- **Formatting**: Black
- **Linting**: Flake8 with max line length 88
- **Imports**: isort
- **Type checking**: mypy

### Adding New Features
1. **Models first**: Define Pydantic models in `src/models/`
2. **Business logic**: Implement services in `src/services/`
3. **API endpoints**: Add routes in `src/api/`
4. **Tests**: Write comprehensive tests in `tests/`

### Database Migrations
For production databases, use Alembic:
```bash
# Initialize Alembic
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db/adr_hub
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=adr_hub
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards
- Follow existing code style and architecture patterns
- Write tests for new features
- Update documentation as needed
- Keep commits focused and descriptive

### Issue Reporting
- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Describe use cases for feature requests

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SQLModel** for combining SQLAlchemy and Pydantic
- **Pydantic** for robust data validation
- **The ADR community** for establishing best practices

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/adr-hub/issues)
- **Documentation**: Check the `/docs` endpoint when running the API
- **Community**: Join discussions in GitHub Discussions

---

## 🚧 Roadmap

### Planned Features
- [ ] **Authentication & Authorization**: JWT-based auth with role-based access
- [ ] **Webhook support**: Notifications for ADR status changes
- [ ] **Export functionality**: Export ADRs to PDF/Markdown
- [ ] **Advanced search**: Full-text search with filters
- [ ] **Dashboard**: Web interface for ADR management
- [ ] **Import from legacy**: Import from file-based ADR systems
- [ ] **API versioning**: Support for multiple API versions
- [ ] **Rate limiting**: Protect API from abuse

### Migration from CLI
This project evolved from a CLI-based ADR management system. The legacy file-based structure is preserved in the `architecture/` directory for reference and potential migration tools.

---

**ADR Hub** — Making architecture decisions trackable, auditable, and collaborative. 🏛️

