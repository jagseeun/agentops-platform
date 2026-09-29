# AgentOps Platform

[![CI](https://github.com/jagseeun/agentops-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/jagseeun/agentops-platform/actions/workflows/ci.yml)

AI Agent의 실행 흐름을 운영 가능한 백엔드 구조로 다루기 위한 플랫폼 프로젝트입니다.

이 저장소는 처음에는 `agentops-mini`로 시작했지만, 현재는 PostgreSQL, Alembic, Redis, Celery를 붙여 실제 서비스에 가까운 구조로 확장한 상태입니다.

## 핵심 목표

- Agent, Workflow, Run을 API로 관리합니다.
- Run 생성 요청은 빠르게 받고, 실제 실행은 Worker가 비동기로 처리합니다.
- PostgreSQL을 기준 저장소로 사용합니다.
- Alembic으로 DB 스키마 변경 이력을 관리합니다.
- Redis와 Celery로 queue 기반 worker 흐름을 구성합니다.
- 테스트 DB를 운영/개발 DB와 분리해서 안전하게 테스트합니다.

## 전체 구조

```text
Client
  |
  v
FastAPI API
  |
  +--> PostgreSQL
  |
  +--> Redis queue
          |
          v
      Celery Worker
          |
          v
      PostgreSQL
```

Run 처리 흐름은 다음과 같습니다.

1. FastAPI가 Run을 `queued` 상태로 생성합니다.
2. FastAPI가 Redis queue에 `run_id`를 넣습니다.
3. Celery Worker가 queue에서 작업을 가져옵니다.
4. Worker가 아직 처리되지 않은 Run을 안전하게 claim합니다.
5. Run 상태를 `running`으로 바꿉니다.
6. Workflow step을 실행합니다.
7. 성공하면 `completed`, 실패하면 `failed`로 저장합니다.

## 기술 스택

- Python 3.13
- FastAPI
- SQLAlchemy
- PostgreSQL 16
- Alembic
- Redis
- Celery
- Pytest
- Docker Compose
- GitHub Actions
- GitHub Container Registry
- Kubernetes
- uv

## 주요 기능

- Workspace 생성
- Agent 등록
- Workflow 생성
- Run 생성 및 상태 조회
- Run retry
- Run timeline 조회
- Model call 기록
- Audit log 기록
- Celery worker 기반 비동기 Run 처리
- PostgreSQL migration 관리
- 테스트 DB 안전장치
- GitHub Actions 기반 CI 테스트 자동화
- Docker image build와 GHCR publishing workflow
- Kubernetes manifest 초안

## 주요 API

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/health` | API 상태 확인 |
| `POST` | `/workspaces` | Workspace 생성 |
| `POST` | `/agents` | Agent 생성 |
| `GET` | `/workspaces/{workspace_id}/agents` | Workspace의 Agent 목록 조회 |
| `POST` | `/workspaces/{workspace_id}/workflows` | Workflow 생성 |
| `POST` | `/workspaces/{workspace_id}/workflows/{workflow_id}/runs` | Run 생성 및 queue 등록 |
| `GET` | `/workspaces/{workspace_id}/runs/{run_id}` | Run 상태 조회 |
| `PATCH` | `/workspaces/{workspace_id}/runs/{run_id}/status` | Run 상태 변경 |
| `POST` | `/workspaces/{workspace_id}/runs/{run_id}/retry` | 실패한 Run 재시도 |
| `GET` | `/workspaces/{workspace_id}/runs/{run_id}/timeline` | Run timeline 조회 |

## 실행 방법

환경 변수 파일을 먼저 준비합니다.

```powershell
Copy-Item .env.example .env
```

Docker Compose로 전체 서비스를 실행합니다.

```powershell
docker compose up --build -d
```

실행 상태를 확인합니다.

```powershell
docker compose ps
```

DB migration을 적용합니다.

```powershell
docker compose exec api uv run alembic upgrade head
```

API 상태를 확인합니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

정상 응답:

```json
{"status":"ok"}
```

## 테스트

테스트는 별도 테스트 DB를 사용합니다.

`TEST_DATABASE_URL`이 `DATABASE_URL`과 같거나, 테스트 DB 이름이 `_test`로 끝나지 않으면 테스트가 실행되지 않도록 막아두었습니다.

```powershell
uv run pytest -q
```

이 안전장치는 실수로 개발 DB나 운영 DB를 테스트가 비우는 일을 막기 위한 장치입니다.

## CI

이 프로젝트는 GitHub Actions로 CI를 실행합니다.

CI는 push 또는 `main` 대상 pull request에서 실행되며, GitHub Actions 안에서 PostgreSQL 16 서비스를 띄우고 `agentops_test` DB를 만든 뒤 migration과 전체 테스트를 실행합니다.

자동 검증 흐름은 다음과 같습니다.

1. Repository checkout
2. Python 3.13 설치
3. uv 설치와 의존성 동기화
4. PostgreSQL test database 생성
5. Alembic migration 적용
6. `pytest` 실행

## Deployment Pipeline

이 프로젝트는 배포 자동화로 가기 위한 기본 파이프라인을 구성했습니다.

현재 자동화된 범위는 다음과 같습니다.

- Pull request에서 pytest CI 실행
- Pull request에서 Docker image build 검증
- `main` push에서 Docker image build
- `main` push에서 GHCR로 Docker image publish

현재 Docker image는 다음 이름으로 publish됩니다.

```text
ghcr.io/jagseeun/agentops-platform:latest
ghcr.io/jagseeun/agentops-platform:<commit-sha>
```

`latest`는 최신 main image를 가리키고, `commit-sha` tag는 특정 commit으로 만든 image를 추적하기 위해 사용합니다.

아직 실제 Kubernetes 클러스터에 자동 배포하는 단계까지는 구현하지 않았습니다.

## Kubernetes Manifests

Kubernetes 배포 초안은 다음 폴더에 있습니다.

```text
deploy/kubernetes/
```

현재 manifest는 API, Worker, ConfigMap, Secret 예시, Service, 로컬 검증용 PostgreSQL/Redis 리소스를 포함합니다.

```text
api-deployment.yaml
worker-deployment.yaml
api-service.yaml
configmap.yaml
secret.example.yaml
postgres-deployment.yaml
postgres-service.yaml
redis-deployment.yaml
redis-service.yaml
```

로컬 Docker Desktop Kubernetes에서 dry-run 검증을 완료했습니다.

```powershell
kubectl apply --dry-run=client -f deploy/kubernetes
```

PostgreSQL과 Redis manifest는 로컬 Kubernetes 검증용입니다. 운영 환경에서는 Neon DB 같은 managed PostgreSQL과 managed Redis 사용을 전제로 합니다.

## Migration

현재 migration 상태 확인:

```powershell
docker compose exec api uv run alembic current
```

모델 변경 후 migration 생성:

```powershell
docker compose exec api uv run alembic revision --autogenerate -m "describe change"
```

최신 migration 적용:

```powershell
docker compose exec api uv run alembic upgrade head
```

## Docker Compose 구성

현재 Compose는 다음 서비스를 함께 실행합니다.

- `api`: FastAPI 서버
- `worker`: Celery worker
- `postgres`: PostgreSQL DB
- `redis`: Celery broker

API와 Worker는 같은 PostgreSQL과 Redis를 바라봅니다.

## 작업 기록

주요 작업 기록은 `docs/`, `notes/`에 정리되어 있습니다.

- `notes/baseline.md`
- `docs/postgres-alembic.md`
- `notes/day10-db-contamination-check.md`
- `notes/day15-celery-run-check.md`
- `notes/day16-retry-policy.md`
- `notes/day18-worker-shutdown-check.md`
- `notes/day20-capstone-check.md`

## 현재 상태

현재 이 프로젝트는 단순 미니 프로젝트를 넘어, 운영 가능한 백엔드 플랫폼 구조로 확장되었습니다.

구현된 기반은 다음과 같습니다.

- PostgreSQL 전환
- Alembic migration 도입
- 테스트 DB 분리와 안전장치
- Redis broker 구성
- Celery worker 기반 Run 처리
- Run atomic claim
- Docker Compose 기반 API, Worker, DB, Redis 통합 실행
- GitHub Actions 기반 pytest CI
- GHCR image publishing workflow
- Kubernetes manifest 초안과 dry-run 검증

다음 단계는 인증/인가 고도화, observability 강화, 실제 Kubernetes 배포 검증, cloud database 연결입니다.
