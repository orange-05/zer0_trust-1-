# DevGuard — Zero-Trust Supply Chain Security Pipeline

A DevSecOps platform that prevents vulnerable Flask applications from being deployed unless they pass security verification and image signing checks.

---

## What This Project Does

DevGuard is a **control system for build trust**. Every code change goes through a zero-trust pipeline before deployment:
```
Developer pushes code to GitHub
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                    CI PIPELINE                          │
│                                                         │
│  Stage 1: LINT (flake8)                                 │
│  ├── Checks code style and quality                      │
│  ├── Enforces PEP8 Python standards                     │
│  └── BLOCKS if: syntax errors, bad imports              │
│                    │                                    │
│  Stage 2: TEST (pytest)                                 │
│  ├── Runs all unit tests                                │
│  ├── Measures code coverage                             │
│  └── BLOCKS if: any test fails                          │
│                    │                                    │
│  Stage 3: DEPENDENCY SCAN (Trivy)                       │
│  ├── Scans requirements.txt against CVE database        │
│  ├── Checks every package you installed                 │
│  └── BLOCKS if: any CRITICAL vulnerability found        │
│                    │                                    │
│  Stage 4: DOCKER BUILD                                  │
│  ├── Builds container image                             │
│  ├── Non-root user, slim base image                     │
│  └── Saves image as artifact for next stages            │
│                    │                                    │
│         ┌──────────┴──────────┐                         │
│         ▼                     ▼                         │
│  Stage 5: IMAGE SCAN    Stage 6: SBOM                   │
│  ├── Trivy scans the    ├── Syft generates list         │
│  │   built Docker       │   of EVERY component          │
│  │   image for OS       │   inside the image            │
│  │   + package CVEs     └── Software Bill of            │
│  └── BLOCKS if:              Materials (audit trail)    │
│      CRITICAL CVE found                                 │
│         └──────────┬──────────┘                         │
│                    ▼                                    │
│  Stage 7: SIGN IMAGE (Cosign)                           │
│  ├── Cryptographically signs the Docker image           │
│  ├── Signature stored in public Sigstore/Rekor log      │
│  ├── Anyone can VERIFY the image came from your CI      │
│  └── ONLY runs on main branch after all gates pass      │
│                    │                                    │
│  Stage 8: SUMMARY                                       │
│  └── Security report written to GitHub Actions tab      │
└─────────────────────────────────────────────────────────┘
              │
              │  (only if ALL 8 stages pass)
              ▼
┌─────────────────────────────────────────────────────────┐
│                    CD PIPELINE                          │
│                                                         │
│  Stage 1: PRE-DEPLOY CHECKS                             │
│  └── Verifies CI passed before touching production      │
│                    │                                    │
│  Stage 2: DEPLOY                                        │
│  ├── Builds image on runner                             │
│  ├── Checks non-root user, Gunicorn, health endpoint    │
│  └── Would SSH to your server and run docker compose    │
│                    │                                    │
│  Stage 3: VERIFY                                        │
│  └── Post-deploy health checks on live app              │
│                    │                                    │
│  Stage 4: SUMMARY                                       │
│  └── Full deployment report in GitHub Actions tab       │
└─────────────────────────────────────────────────────────┘
              │
              ▼
     ✅ TRUSTED BUILD IN PRODUCTION
```
---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Docker + Docker Compose

### 1. Clone and install
```bash
git clone https://github.com/yourusername/devguard.git
cd devguard
pip install -r requirements.txt
```

### 2. Run the API
```bash
python run.py
# API available at http://localhost:5000
```

### 3. Run with Docker Compose (full stack)
```bash
docker compose up --build
# API:        http://localhost:5000
# Grafana:    http://localhost:3000  (admin / devguard123)
# Prometheus: http://localhost:9090
```

### 4. Run tests
```bash
pytest
# With coverage:
pytest --cov=app --cov-report=term-missing
```

---

## API Endpoints

### Health (no auth required)
```
GET  /api/v1/health
```

### Authentication
```
POST /api/v1/auth/register   → Create account
POST /api/v1/auth/login      → Get JWT token
GET  /api/v1/auth/me         → Current user (auth required)
```

### Pipelines (JWT required)
```
POST  /api/v1/pipelines                        → Create pipeline record
GET   /api/v1/pipelines                        → List all pipelines
GET   /api/v1/pipelines/<id>                   → Get specific pipeline
PATCH /api/v1/pipelines/<id>/status            → Update status
```

### Scans (JWT required)
```
POST /api/v1/scans                             → Submit scan result
GET  /api/v1/scans                             → List all scans
GET  /api/v1/scans/<id>                        → Get specific scan
GET  /api/v1/security-report                   → Aggregate security metrics
```

### Deployments (JWT required — Zero-Trust enforced)
```
POST /api/v1/deployments                       → Record deployment (BLOCKED if checks fail)
GET  /api/v1/deployments                       → List deployments
GET  /api/v1/deployments/<id>                  → Get specific deployment
```

---

## Example API Usage

```bash
# 1. Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "StrongPass123!"}'

# 2. Login (save the token)
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "StrongPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 3. Create pipeline
curl -X POST http://localhost:5000/api/v1/pipelines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commit_id": "abc123", "branch": "main", "triggered_by": "github-actions"}'

# 4. Submit passing scan
curl -X POST http://localhost:5000/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "pl-XXXX", "scan_type": "dependency", "tool": "trivy", "status": "passed", "critical_count": 0, "high_count": 1}'

# 5. Try deployment — will PASS (signed + no critical vulns)
curl -X POST http://localhost:5000/api/v1/deployments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "pl-XXXX", "image_tag": "devguard-api:1.0.0", "signed": true, "environment": "production", "status": "deployed"}'

# 6. Try deployment with signed=false — will return 403 BLOCKED
curl -X POST http://localhost:5000/api/v1/deployments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "pl-XXXX", "image_tag": "devguard-api:1.0.0", "signed": false, "environment": "production", "status": "deployed"}'
```

---

## Zero-Trust Policy

A deployment is **BLOCKED** if:
- `signed: false` — image not cryptographically signed
- Any scan has `status: "failed"`
- Any scan has `critical_count > 0`
- No scans exist for the pipeline

A deployment is **ALLOWED** only when:
- Image is signed (`signed: true`)
- All scan statuses are `"passed"`
- Zero critical vulnerabilities found

---

## Architecture

```
API Layer (Blueprints)        → routes, request parsing, response formatting
    ↓
Service Layer                 → business rules, zero-trust validation
    ↓
Repository Layer              → CRUD, JSON file read/write, thread-safe access
    ↓
Data Store (JSON files)       → users.json, pipelines.json, scan_reports.json, deployments.json
```

### File Structure
```
devguard/
├── app/
│   ├── api/              ← Flask Blueprints (routes)
│   ├── services/         ← Business logic
│   ├── repositories/     ← Data access layer
│   ├── utils/            ← Shared helpers
│   ├── config.py         ← Environment configs
│   ├── extensions.py     ← Flask extensions (JWT)
│   └── errors.py         ← Centralized error handlers
├── data/                 ← JSON data files
├── tests/                ← pytest test suite
├── .github/workflows/    ← GitHub Actions CI/CD
├── monitoring/           ← Prometheus + Grafana config
├── terraform/            ← AWS infrastructure as code
├── scripts/              ← Shell scripts for CI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## CI/CD Pipeline Stages

| Stage | Tool | Purpose |
|-------|------|---------|
| Lint | flake8 | Enforce code style |
| Test | pytest | Run unit tests + coverage |
| Dependency Scan | Trivy | Scan requirements.txt for CVEs |
| Docker Build | Docker | Build container image |
| Image Scan | Trivy | Scan image for OS/package CVEs |
| SBOM | Syft | Generate Software Bill of Materials |
| Sign | Cosign | Cryptographically sign the image |
| Report | curl/bash | Post results to Flask API |

---

## Deployment (Terraform + AWS)

```bash
cd terraform/

# Create terraform.tfvars (gitignored)
cat > terraform.tfvars << EOF
key_pair_name  = "your-aws-key"
github_repo    = "yourusername/devguard"
secret_key     = "$(openssl rand -hex 32)"
jwt_secret_key = "$(openssl rand -hex 32)"
EOF

terraform init
terraform plan
terraform apply

# Outputs the server IP and URLs
terraform output
```

---

## Stack

Python 3.11 · Flask 3.1 · Flask-JWT-Extended · Gunicorn · pytest · flake8 · Docker · GitHub Actions · Trivy · Cosign · Terraform · Prometheus · Grafana
