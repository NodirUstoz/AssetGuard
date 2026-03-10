# AssetGuard - IT Asset Management System

A comprehensive, production-grade IT asset management system for tracking hardware, software licenses, maintenance schedules, depreciation, check-in/check-out workflows, audit logs, and compliance.

## Architecture

- **Backend:** Django 5.x + Django REST Framework
- **Frontend:** React 18 with Redux Toolkit
- **Database:** PostgreSQL 16
- **Cache / Broker:** Redis 7
- **Task Queue:** Celery 5 with Celery Beat
- **Reverse Proxy:** Nginx
- **Containerization:** Docker & Docker Compose

## Features

### Asset Lifecycle Management
- Full hardware and software asset tracking with unique asset tags
- QR code label generation for physical asset identification
- Check-in / check-out workflow with assignment history
- Category and type taxonomy for flexible asset classification
- Location and department-based asset organization

### Software License Management
- License tracking with seat counts, expiration dates, and renewal workflows
- Per-user and per-device license assignment
- Automated renewal reminder notifications via Celery tasks
- License compliance dashboards

### Maintenance & Warranty
- Scheduled and ad-hoc maintenance tracking
- Warranty period management with expiration alerts
- Maintenance cost tracking and vendor management
- Calendar view for upcoming maintenance windows

### Financial / Depreciation
- Straight-line and declining-balance depreciation methods
- Automated monthly depreciation entry generation
- Current book value calculations
- Depreciation schedule reporting

### Audit & Compliance
- Comprehensive audit log for every asset mutation
- Scheduled compliance audits with pass/fail tracking
- Audit history and result reporting

### Reporting & Analytics
- Asset summary and utilization dashboards
- Depreciation reports with export capability
- License compliance reports
- Maintenance cost analysis

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd assetguard
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

3. Build and start all services:
```bash
docker-compose up --build -d
```

4. Run database migrations:
```bash
docker-compose exec backend python manage.py migrate
```

5. Create a superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. Access the application:
   - **Frontend:** http://localhost
   - **API:** http://localhost/api/
   - **Admin:** http://localhost/api/admin/
   - **API Docs:** http://localhost/api/docs/

## Development

### Backend (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (without Docker)

```bash
cd frontend
npm install
npm start
```

### Running Celery Workers

```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

## API Endpoints

| Resource            | Endpoint                     | Methods                     |
|---------------------|------------------------------|-----------------------------|
| Authentication      | `/api/auth/login/`           | POST                        |
| Authentication      | `/api/auth/logout/`          | POST                        |
| Users               | `/api/accounts/users/`       | GET, POST                   |
| Departments         | `/api/accounts/departments/` | GET, POST, PUT, DELETE      |
| Assets              | `/api/assets/`               | GET, POST, PUT, PATCH, DEL  |
| Asset Categories    | `/api/assets/categories/`    | GET, POST, PUT, DELETE      |
| Asset Assignments   | `/api/assets/assignments/`   | GET, POST, PATCH            |
| Licenses            | `/api/licenses/`             | GET, POST, PUT, PATCH, DEL  |
| License Assignments | `/api/licenses/assignments/` | GET, POST, DELETE            |
| Maintenance         | `/api/maintenance/schedules/`| GET, POST, PUT, DELETE      |
| Maintenance Logs    | `/api/maintenance/logs/`     | GET, POST                   |
| Warranties          | `/api/maintenance/warranties/`| GET, POST, PUT, DELETE     |
| Depreciation        | `/api/depreciation/schedules/`| GET, POST                  |
| Depreciation        | `/api/depreciation/entries/` | GET                         |
| Audits              | `/api/audits/logs/`          | GET                         |
| Audit Schedules     | `/api/audits/schedules/`     | GET, POST, PUT              |
| Compliance          | `/api/audits/compliance/`    | GET, POST                   |
| Reports             | `/api/reports/asset-summary/`| GET                         |
| Reports             | `/api/reports/depreciation/` | GET                         |
| Reports             | `/api/reports/license-compliance/` | GET                   |

## Environment Variables

See `.env.example` for a complete list of configurable environment variables.

## Project Structure

```
assetguard/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # Users, departments, employees
│   │   ├── assets/         # Core asset management
│   │   ├── licenses/       # Software license tracking
│   │   ├── maintenance/    # Maintenance & warranty
│   │   ├── depreciation/   # Financial depreciation
│   │   ├── audits/         # Audit logs & compliance
│   │   └── reports/        # Reporting & analytics
│   ├── config/             # Django settings & configuration
│   └── utils/              # Shared utilities
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/            # API client modules
│       ├── components/     # Reusable React components
│       ├── pages/          # Top-level page components
│       ├── store/          # Redux store & slices
│       ├── hooks/          # Custom React hooks
│       └── styles/         # Global CSS
├── nginx/                  # Nginx reverse proxy config
├── docker-compose.yml
└── .env.example
```

## License

This project is proprietary software. All rights reserved.
