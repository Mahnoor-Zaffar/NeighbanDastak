# NigehbaanDastak

NigehbaanDastak is a clinic-management MVP built for portfolio and interview
presentation. It focuses on practical backend architecture, clear API behavior,
security-minded defaults, and a demo-ready frontend.

## What Is Implemented

- patient management (CRUD + archive)
- appointment management (CRUD + status transitions)
- visit/encounter management (linked to patient and optional appointment)
- role-based permissions via demo roles (`admin`, `doctor`, `receptionist`)
- audit logging for sensitive write actions
- standardized API errors with request IDs
- basic write-rate limiting
- **prescriptions management** with medication items and printing
- **queue management system** for clinic workflow optimization
- **follow-up tracking** for patient care coordination
- **analytics dashboard** with clinic metrics and insights
- **patient timeline** for comprehensive history tracking
- React demo UI for auth simulation + complete clinic workflows

Intentionally deferred:

- notifications
- billing
- attachments
- patient self-service portals

## Architecture Summary

- backend: FastAPI + SQLAlchemy + Alembic
- pattern: route -> service -> repository
- frontend: React + TypeScript + React Router
- testing: pytest API/integration/unit coverage for critical flows

Detailed module architecture:

- [`docs/architecture.md`](docs/architecture.md)

## API Module Summary

Base path: `/api/v1`

- system: `/health`
- patients: list/create/detail/update/archive/timeline
- appointments: list/create/detail/update/delete/queue management
- visits: create/detail/update
- prescriptions: create/detail/update/delete/print
- queue: clinic queue management with status tracking
- follow-ups: create/update/complete/cancel
- analytics: clinic summary and insights

Role behavior and response conventions:

- [`docs/api.md`](docs/api.md)

## Local Setup (Complete Working Guide)

### Prerequisites

- PostgreSQL installed and running locally
- Node.js (v18+) for frontend
- Python (v3.8+) for backend
- Docker (optional, for containerized setup)

### Option A: Docker Compose (Recommended for Production-like Setup)

```bash
cd infra
cp .env.example .env
docker compose up --build
docker compose exec backend alembic upgrade head
```

**Services:**
- Backend: `http://localhost:8000/api/v1`
- Frontend: `http://localhost:5173`
- Health Check: `http://localhost:8000/api/v1/health`

### Option B: Local Development Setup (Step-by-Step)

#### 1. Database Setup

```bash
# Start PostgreSQL service
brew services start postgres

# Create database
createdb nigehbaan_dastak

# Create postgres user (if doesn't exist)
psql postgres
CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';
\q
```

#### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Ensure .env contains:
# ND_POSTGRES_SERVER=localhost
# ND_POSTGRES_PORT=5432
# ND_POSTGRES_USER=postgres
# ND_POSTGRES_PASSWORD=postgres
# ND_POSTGRES_DB=nigehbaan_dastak
# ND_CORS_ORIGINS=["http://localhost:5173"]

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL (optional, defaults to localhost:8000/api/v1)
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# Start frontend development server
npm run dev
```

#### 4. Verify Connection

1. **Backend Health**: Open `http://localhost:8000/api/v1/health` in browser
2. **Frontend**: Open `http://localhost:5173` - should show "API Status: Connected"
3. **API Documentation**: Open `http://localhost:8000/api/v1/docs` for Swagger UI

### Troubleshooting Common Issues

#### Port 8000 Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
sudo lsof -ti :8000 | xargs kill -9
```

#### Database Connection Issues
```bash
# Check PostgreSQL is running
brew services list | grep postgres

# Verify database exists
psql -l

# Test connection
psql -h localhost -U postgres -d nigehbaan_dastak
```

#### Frontend "Failed to Fetch" API Error
1. Ensure backend is running on port 8000
2. Check CORS origins in backend `.env` includes `http://localhost:5173`
3. Verify API URL in frontend `.env` is correct

## Application Working Overview

### Architecture Flow

```
Frontend (React)     Backend (FastAPI)     Database (PostgreSQL)
     |                      |                       |
     | HTTP Requests        | SQLAlchemy ORM        |
     |---------------------->|                       |
     |                      | SQL Queries           |
     |                      |---------------------->|
     |                      |                       |
     | JSON Response        |                       |
     |<----------------------|                       |
```

### Authentication System

The application uses **demo role-based authentication** via HTTP headers:

- **Admin Role**: Full access to patient lifecycle, appointment deletion
- **Doctor Role**: Patient read/search, appointment/visit management

**Frontend Role Selection**: The UI provides role switcher to simulate different user types

**Backend Authorization**: All API endpoints validate the `X-Demo-Role` header

### Data Models & Relationships

```
Patients (1) -----> (N) Appointments (1) -----> (N) Visits
    |                     |                        |
    v                     v                        v
Archive/Restore     Status Transitions        Clinical Notes
    |                     |                        |
    v                     v                        v
Prescriptions     Queue System             Follow-ups
Audit Logs         Doctor Workload        Patient Timeline
Users             Analytics               Care Coordination
```

### Key Features in Action

1. **Patient Management**
   - Create patients with medical record numbers
   - Search and filter patients
   - Archive inactive patients
   - Comprehensive patient timeline
   - Prescription and follow-up history

2. **Appointment Workflow**
   - Schedule appointments for patients
   - Status tracking (scheduled, completed, cancelled, no_show)
   - Link appointments to clinical visits
   - Queue management for clinic operations
   - Doctor assignment and workload tracking

3. **Visit Documentation**
   - Create clinical encounters
   - Record complaints and diagnoses
   - Optional appointment linking
   - Prescription creation during visits
   - Follow-up scheduling

4. **Prescription Management**
   - Create prescriptions with multiple medications
   - Detailed dosage and frequency instructions
   - Prescription printing for patients
   - Link prescriptions to visits and patients

5. **Queue System**
   - Real-time clinic queue management
   - Patient check-in/check-out workflow
   - Queue status tracking (waiting, in_progress, completed)
   - Doctor queue assignment

6. **Follow-up Tracking**
   - Schedule patient follow-ups
   - Status management (pending, completed, cancelled, overdue)
   - Care coordination reminders
   - Link follow-ups to visits

7. **Analytics Dashboard**
   - Clinic summary statistics
   - Appointment trends and patterns
   - Doctor workload analysis
   - Patient acquisition metrics

8. **Audit Trail**
   - Automatic logging of all sensitive operations
   - Track who did what and when
   - Essential for healthcare compliance

### API Endpoints Summary

| Method | Endpoint | Purpose | Required Role |
|--------|----------|---------|---------------|
| GET | `/health` | System health check | Any |
| GET/POST | `/patients` | List/create patients | Admin/Doctor |
| GET/PATCH/DELETE | `/patients/{id}` | Patient operations | Admin/Doctor |
| GET | `/patients/{id}/timeline` | Patient timeline | Admin/Doctor |
| GET/POST | `/appointments` | List/create appointments | Admin/Doctor |
| GET/PATCH/DELETE | `/appointments/{id}` | Appointment operations | Admin (delete) |
| POST | `/appointments/{id}/check-in` | Check-in patient | Admin/Doctor |
| GET/POST | `/visits` | List/create visits | Admin/Doctor |
| GET | `/visits/{id}` | Visit details | Admin/Doctor |
| GET/POST | `/prescriptions` | List/create prescriptions | Admin/Doctor |
| GET/PATCH/DELETE | `/prescriptions/{id}` | Prescription operations | Admin/Doctor |
| GET | `/prescriptions/{id}/print` | Print prescription | Admin/Doctor |
| GET | `/queue` | View clinic queue | Admin/Doctor |
| POST | `/queue/{id}/call` | Call next patient | Admin/Doctor |
| POST | `/queue/{id}/complete` | Complete queue entry | Admin/Doctor |
| GET/POST | `/follow-ups` | List/create follow-ups | Admin/Doctor |
| GET/PATCH | `/follow-ups/{id}` | Update follow-up | Admin/Doctor |
| POST | `/follow-ups/{id}/complete` | Complete follow-up | Admin/Doctor |
| GET | `/analytics/summary` | Clinic analytics | Admin/Doctor |
| GET | `/analytics/appointments-by-day` | Appointment trends | Admin/Doctor |
| GET | `/analytics/doctor-workload` | Doctor workload | Admin/Doctor |

### Development Workflow

1. **Start Backend**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Start Frontend**: `npm run dev`
3. **Access Application**: `http://localhost:5173`
4. **API Documentation**: `http://localhost:8000/api/v1/docs`

### Production Considerations

- Replace demo role auth with JWT/session-based authentication
- Add database connection pooling
- Implement distributed rate limiting
- Add background job processing
- Set up monitoring and observability

## Tests

Run all backend tests:

```bash
cd backend
python3 -m pytest
```

Targeted confidence suites:

```bash
python3 -m pytest tests/test_auth_api.py tests/test_integration_flows.py
python3 -m pytest tests/test_schema_validation.py tests/test_audit_service_unit.py
```

Frontend build confidence check:

```bash
cd frontend
npm run build
```

## Deployment Plan

Detailed plan:

- [`docs/deployment.md`](docs/deployment.md)

Quick recommendation for lowest complexity/cost:

1. Frontend on Vercel
2. Backend on Railway (or Render)
3. Postgres on same backend vendor

Why:

- minimal ops overhead for solo maintenance
- straightforward environment variable management
- easy interview explanation

## Environment Separation

- local: `infra/.env.example`
- production template: `infra/.env.production.example`

Core production settings:

- `ND_ENVIRONMENT=production`
- `ND_DEBUG=false`
- `ND_DATABASE_URL=<managed postgres url>`
- `ND_CORS_ORIGINS=["https://<frontend-domain>"]`

## Demo Account and Data Strategy

This MVP uses role simulation, not user accounts.

- `admin`: patient lifecycle + appointment delete + full analytics
- `doctor`: patient read/search + appointment/visit/prescription management
- `receptionist`: read-only intake simulation with queue management

Use synthetic data only. Current demo dataset:

- **34 active patients** with comprehensive demographics
- **12 appointments** with various statuses
- **7 completed visits** with clinical documentation
- **15 prescriptions** across multiple patients
- **8 follow-ups** for care coordination
- **Queue system** with real-time status tracking

This rich dataset demonstrates all major clinic workflows and analytics capabilities.

## Portfolio Presentation

Use this as your portfolio/project blurb:

> Modular clinic MVP with FastAPI + React, covering patient, appointment, and
> visit workflows, with audit logging, standardized API error handling, and
> practical test coverage for critical flows.

Suggested screenshots and live demo script:

- [`docs/portfolio.md`](docs/portfolio.md)

## Known Limitations

- demo-role header auth only (no production auth/session model yet)
- in-memory rate limiting (single instance)
- no background workers
- no file attachments
- no notifications system
- no billing module
- no patient self-service portal

## Future Roadmap

1. replace demo-role auth with real authentication and user model
2. notifications and reminders system with async task processing
3. file attachments for documents and medical images
4. billing and insurance processing
5. patient self-service portal
6. stronger production controls (distributed rate limiting, observability, CI/CD)
7. mobile-responsive design improvements
8. advanced reporting and export capabilities

## Documentation Index

- architecture: [`docs/architecture.md`](docs/architecture.md)
- API summary: [`docs/api.md`](docs/api.md)
- deployment guide: [`docs/deployment.md`](docs/deployment.md)
- portfolio notes/demo script: [`docs/portfolio.md`](docs/portfolio.md)
