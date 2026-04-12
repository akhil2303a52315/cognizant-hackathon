# Deployment Guide

## Prerequisites

- **Python** 3.12+
- **Node.js** 18+ (LTS)
- **Docker** & Docker Compose (optional, for containerized deploy)
- **Git**

## Quick Start (Local Development)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/supplychaingpt-council.git
cd supplychaingpt-council
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
& "venv/Scripts/python.exe" -m pip install -e ".[dev]"

# Or activate first:
# Windows CMD:  venv\Scripts\activate.bat
# PowerShell:   venv\Scripts\Activate.ps1
# Linux/Mac:    source venv/bin/activate

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000` (or 3001 if 3000 is in use)

### 4. Verify

```bash
# Backend health check
curl http://localhost:8000/health

# API test (requires API key)
curl -H "X-API-Key: dev-key" http://localhost:8000/council/export/test-session

# MCP tools list
curl -H "X-MCP-API-Key: dev-mcp-key" http://localhost:8000/mcp/tools
```

---

## Docker Deployment

### Using Docker Compose

```bash
docker compose up --build
```

This starts:
- **FastAPI backend** on port 8000
- **Vite frontend** on port 3000 (dev mode)
- **Redis** on port 6379
- **Neo4j** on ports 7474/7687
- **PostgreSQL (Neon)** — configured via `NEON_DATABASE_URL`

### Production Docker Build

```dockerfile
# Backend Dockerfile (multi-stage)
FROM python:3.12-slim AS builder
WORKDIR /app
COPY backend/ ./backend/
COPY pyproject.toml .
RUN pip install -e ".[dev]"

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile (multi-stage)
FROM node:18-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## AWS Deployment (Hackathon)

### ECS Fargate Setup

1. **Push images to ECR**:
```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t supplychaingpt-backend ./backend
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/supplychaingpt-backend
```

2. **Create ECS services**:
   - Backend: Fargate task with 0.5 vCPU, 1GB RAM
   - Frontend: S3 + CloudFront static hosting (build `dist/` folder)

3. **Environment variables** (set in ECS task definition):
   - All keys from `.env.example`
   - `CORS_ORIGINS=https://your-domain.com`

4. **Load Balancer**: Application Load Balancer routing `/api/*` → backend, `/*` → frontend

### Cost-Optimized (Free Tier)

| Service | Tier | Cost |
|---------|------|------|
| AWS ECS Fargate | Free tier | $0 (first year) |
| Neon PostgreSQL | Free tier | $0 (0.5GB) |
| Redis Cloud | Free tier | $0 (30MB) |
| S3 + CloudFront | Free tier | $0 (first year) |
| Groq API | Free tier | $0 (rate-limited) |
| Firecrawl | Free tier | 500 credits/month |

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | LLM provider (primary) |
| `OPENROUTER_API_KEY` | No | Alternate LLM provider |
| `NVIDIA_API_KEY` | No | Alternate LLM provider |
| `GOOGLE_API_KEY` | No | Gemini provider |
| `COHERE_API_KEY` | No | Cohere provider |
| `NEON_DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection (`redis://localhost:6379`) |
| `NEO4J_URI` | Yes | Neo4j bolt URI |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `PINECONE_API_KEY` | Yes | Vector DB for RAG |
| `FIRECRAWL_API_KEY` | No | Web scraping (mock fallback if missing) |
| `NEWSAPI_KEY` | No | News API (mock fallback if missing) |
| `API_KEYS` | Yes | Comma-separated API keys for auth |
| `MCP_API_KEY` | Yes | MCP endpoint auth key |
| `RATE_LIMIT_PER_MINUTE` | No | Default: 60 |
| `LOG_LEVEL` | No | Default: INFO |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| PowerShell script blocked | Use `& "venv/Scripts/python.exe"` instead of activating |
| Frontend TS errors | `npm install` to install missing types |
| Redis connection refused | Start Redis: `docker run -d -p 6379:6379 redis:7` |
| Neo4j connection refused | Start Neo4j: `docker run -d -p 7474:7474 -p 7687:7687 neo4j:5` |
| Firecrawl mock data | Set `FIRECRAWL_API_KEY` in `.env` for real data |
