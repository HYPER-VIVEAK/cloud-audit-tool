# Cloud Audit Tool

Cloud security auditing platform with a FastAPI backend, React frontend, MySQL (auth/credentials), and MongoDB (scan history/results).

## Features
- Run AWS IAM, network, and storage scans.
- Store encrypted cloud credentials in MySQL.
- Persist scan history and metadata in MongoDB.
- View resources scoped by selected recent scan.
- Download scan reports as PDF from the Reports tab.

## Stack
- Backend: FastAPI, PyMySQL, PyMongo, boto3
- Frontend: React + Vite + Mantine + React Query
- Databases: MySQL 8.4, MongoDB 7

## Quick Start (Docker)
1. Copy `.env.example` to `.env`.
2. Start services:

```bash
docker compose up --build
```

3. Open frontend: `http://localhost:5173`
4. API base: `http://localhost:8000/api`

Default seeded login:
- Username: `admin`
- Password: `admin123`

To reset DB data and reseed:

```bash
docker compose down -v
docker compose up --build
```

## Main API Endpoints
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/scan/run`
- `GET /api/scan/history`
- `GET /api/scan/summary`
- `GET /api/scan/{scan_id}/report/pdf`
- `GET /api/resources/iam/users?scan_id=<id>`
- `GET /api/resources/s3/buckets?scan_id=<id>`
- `GET /api/resources/ec2/instances?scan_id=<id>`

## Notes
- New scan entries include credential metadata used by Resources and Reports views.
- Very old scan records may miss metadata needed for scan-scoped resource lookup.
