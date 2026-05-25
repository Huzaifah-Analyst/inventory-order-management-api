# Inventory Order Management API

A production-style REST API for inventory and order management, built with **Django REST Framework**, **PostgreSQL**, **JWT authentication**, and full CI/CD via GitHub Actions.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development Setup](#local-development-setup)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [AWS Deployment Architecture](#aws-deployment-architecture)
- [Design Decisions](#design-decisions)

---

## Features

- **JWT Authentication** — register, login, token refresh, logout (token blacklist)
- **Product Management** — full CRUD with search (name/SKU), pagination, ordering, and negative-value validation
- **Customer Management** — full CRUD with search and ordering
- **Order Processing** — create orders with multi-item support, automatic total calculation, stock availability enforcement, and status-based stock deduction using database transactions
- **Status Lifecycle** — `PENDING → PROCESSING → COMPLETED | CANCELLED` with enforced valid transitions
- **Reporting** — top 5 best-selling products by quantity with revenue, scoped to completed orders only
- **Interactive API Docs** — Swagger UI at `/api/schema/swagger-ui/` and ReDoc at `/api/schema/redoc/`
- **Health Check** — `/api/health/` reports database connectivity
- **Docker-ready** — single `docker-compose up` gets you running

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 4.2 + Django REST Framework 3.15 |
| Database | PostgreSQL 16 |
| Auth | `djangorestframework-simplejwt` |
| Filtering | `django-filter` |
| API Docs | `drf-spectacular` (OpenAPI 3) |
| Testing | `pytest-django` + `factory-boy` |
| Linting | `flake8`, `black`, `isort` |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Project Structure

```
inventory_api/
├── config/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Local dev overrides
│   │   └── production.py    # Production hardening + AWS hints
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/            # JWT auth: register, login, refresh, logout
│   ├── products/            # Product CRUD
│   ├── customers/           # Customer CRUD
│   ├── orders/              # Order lifecycle + business logic
│   └── reports/             # Sales analytics
├── core/
│   ├── exceptions.py        # Unified error response format
│   ├── pagination.py        # Custom paginator with metadata
│   ├── views.py             # Health check
│   └── urls.py
├── tests/
│   ├── factories.py         # factory_boy model factories
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_orders.py
│   └── test_reports.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── pytest.ini
```

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/inventory-api.git
cd inventory-api

# 2. Create your environment file
cp .env.example .env

# 3. Start all services
docker-compose up --build

# 4. The API is now running at:
#    http://localhost:8000
#    http://localhost:8000/api/schema/swagger-ui/
```

---

## Local Development Setup

**Prerequisites:** Python 3.12+, PostgreSQL 16+

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dev dependencies
pip install -r requirements-dev.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your local PostgreSQL credentials

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser (optional)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

---

## API Reference

Interactive docs are available at **`/api/schema/swagger-ui/`** when the server is running.

### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/auth/register/` | Create a new account | No |
| POST | `/api/auth/login/` | Obtain JWT tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| POST | `/api/auth/logout/` | Blacklist refresh token | Yes |

### Products

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/products/` | List products (paginated, searchable) |
| POST | `/api/products/` | Create a product |
| GET | `/api/products/{id}/` | Retrieve a product |
| PATCH | `/api/products/{id}/` | Partial update |
| DELETE | `/api/products/{id}/` | Delete a product |

Query params: `?search=<name_or_sku>`, `?ordering=price`, `?page=1&page_size=10`

### Customers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/customers/` | List customers |
| POST | `/api/customers/` | Create a customer |
| GET | `/api/customers/{id}/` | Retrieve a customer |
| PATCH | `/api/customers/{id}/` | Partial update |
| DELETE | `/api/customers/{id}/` | Delete a customer |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orders/` | List orders (filterable by status/customer) |
| POST | `/api/orders/` | Create an order with items |
| GET | `/api/orders/{id}/` | Retrieve an order |
| PATCH | `/api/orders/{id}/status/` | Update order status |

**Order creation payload:**
```json
{
  "customer": 1,
  "items": [
    { "product": 3, "quantity": 2 },
    { "product": 7, "quantity": 1 }
  ]
}
```

**Business rules enforced:**
- Stock is checked at order creation time
- `price_at_purchase` is captured from the product's current price (price changes won't affect historical orders)
- `total_amount` is calculated automatically
- Stock is deducted only when status transitions to `COMPLETED`
- All stock operations run inside a `SELECT FOR UPDATE` database transaction

### Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/reports/top-products/` | Top 5 products by quantity sold |

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "product_id": 3,
      "product_name": "Widget Pro",
      "product_sku": "WGT-001",
      "total_quantity_sold": 240,
      "total_revenue": "4800.00"
    }
  ]
}
```

### Health Check

```bash
GET /api/health/
# Response: {"status": "healthy", "database": "connected"}
```

---

## Running Tests

```bash
# Run full test suite with coverage
pytest

# Run specific test file
pytest tests/test_orders.py -v

# Run with coverage report only (no threshold enforcement)
pytest --cov=apps --cov-report=html
```

Coverage threshold is set to **80%** and enforced in CI.

---

## CI/CD Pipeline

Every push to `main` or `develop` triggers the GitHub Actions pipeline:

```
┌─────────┐     ┌───────────────────────────┐     ┌──────────────┐
│  Push   │────▶│  Job 1: Lint              │────▶│  Job 2: Test │
│  / PR   │     │  flake8 · black · isort   │     │  pytest      │
└─────────┘     └───────────────────────────┘     │  + coverage  │
                                                   └──────┬───────┘
                                                          │
                                                   ┌──────▼───────┐
                                                   │  Job 3: Build│
                                                   │  Docker image│
                                                   └──────────────┘
```

The pipeline uses a real PostgreSQL 16 service container so tests run against an actual database, not SQLite.

---

## AWS Deployment Architecture

The recommended production deployment on AWS:

```
                          ┌─────────────────────────────────────────┐
                          │              AWS Cloud                   │
                          │                                          │
  Users ──▶  Route 53 ──▶ │  ALB (Application Load Balancer)        │
                          │   │                                      │
                          │   ├──▶ ECS Fargate (Django containers)   │
                          │   │       ├── Task 1 (gunicorn)          │
                          │   │       └── Task 2 (gunicorn)          │
                          │   │              │                       │
                          │   │              ▼                       │
                          │   │    RDS PostgreSQL (Multi-AZ)         │
                          │   │                                      │
                          │   └──▶ S3 Bucket                         │
                          │           ├── /static/                   │
                          │           └── /media/                    │
                          │                                          │
                          │  IAM Role ──▶ ECS Task (least privilege) │
                          │  CloudWatch ──▶ Container logs           │
                          │  Secrets Manager ──▶ DB credentials      │
                          └─────────────────────────────────────────┘
```

### Key services

| AWS Service | Purpose |
|---|---|
| **ECS Fargate** | Runs Django containers — serverless, auto-scaling, no EC2 to manage |
| **RDS PostgreSQL (Multi-AZ)** | Managed database with automatic failover and backups |
| **Application Load Balancer** | HTTPS termination, health-check routing |
| **S3** | Static files (`collectstatic`) and user-uploaded media |
| **CloudFront** | CDN in front of S3 for low-latency static file delivery |
| **Secrets Manager** | Stores `SECRET_KEY`, DB credentials — never in environment variables |
| **IAM Roles** | ECS task role with least-privilege S3 and Secrets Manager access |
| **CloudWatch** | Container logs, alarms on 5xx error rate and response latency |
| **Route 53** | DNS with health-check failover |

### Deployment steps (high-level)

```bash
# 1. Build and push Docker image to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ECR_URI>
docker build -t inventory-api .
docker tag inventory-api:latest <ECR_URI>/inventory-api:latest
docker push <ECR_URI>/inventory-api:latest

# 2. Run migrations as an ECS one-off task before deploying new version
aws ecs run-task --task-definition inventory-migrate ...

# 3. Update ECS service (triggers rolling deployment with zero downtime)
aws ecs update-service --cluster prod --service inventory-api --force-new-deployment
```

---

## Design Decisions

**Split settings (base / dev / prod)** — common Django best practice. Avoids accidentally enabling debug mode or weak secrets in production.

**Custom exception handler** — all errors return a consistent `{ success, status_code, error }` envelope, making client-side error handling predictable.

**`price_at_purchase` on OrderItem** — product prices can change over time. Capturing the price at order creation time ensures historical order accuracy.

**`SELECT FOR UPDATE` on stock deduction** — prevents race conditions when two requests try to complete orders for the same product simultaneously.

**Status transition validation** — enforcing `PENDING → PROCESSING → COMPLETED` via the serializer prevents invalid state changes (e.g., reopening a completed order).

**factory_boy for tests** — clean, composable test data without repetitive setup code. Each test only specifies what it cares about.

**Swagger UI included** — clients and frontend teams can explore and test the API interactively without reading raw code.
