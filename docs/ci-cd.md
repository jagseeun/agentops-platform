# CI/CD Notes

이 문서는 AgentOps Platform의 CI/CD 흐름을 정리한 문서다.

현재 단계에서는 완전한 자동 배포까지 가지 않고, 먼저 다음 두 가지를 자동화한다.

- 테스트 자동 실행
- Docker image build 확인
- GitHub Container Registry push

## CI와 CD의 차이

CI는 코드를 main에 넣기 전에 프로젝트가 깨지지 않았는지 자동으로 확인하는 과정이다.

이 프로젝트의 CI는 GitHub Actions에서 PostgreSQL을 띄우고, 테스트 DB를 만든 뒤 migration과 pytest를 실행한다.

CD는 테스트를 통과한 코드를 실제 실행 환경에 배포하는 과정이다.

아직 이 프로젝트는 실제 서버나 Kubernetes 클러스터에 자동 배포하지 않는다. 지금은 CD로 가기 전 단계로 Docker image build와 GHCR push까지 확인한다.

## 현재 GitHub Actions

현재 workflow는 두 개다.

### CI

파일:

```text
.github/workflows/ci.yml
```

역할:

- Python 3.13을 준비한다.
- uv로 의존성을 설치한다.
- PostgreSQL 16 service를 띄운다.
- `agentops_test` 테스트 DB를 만든다.
- Alembic migration을 적용한다.
- 전체 pytest를 실행한다.

이 workflow는 테스트 DB 안전장치가 실제 CI 환경에서도 동작하는지 확인한다.

### Docker Image

파일:

```text
.github/workflows/docker-image.yml
```

역할:

- repository를 checkout한다.
- Dockerfile로 image를 build한다.
- main push일 때 GitHub Container Registry에 image를 push한다.

PR에서는 image build까지만 확인한다.

main에 merge된 뒤 push 이벤트가 발생하면 GHCR에 image를 올린다.

현재 목표는 "이 앱이 컨테이너로 포장 가능하고, GitHub의 image 저장소에 올릴 수 있는 상태인가"를 확인하는 것이다.

## GHCR

GHCR은 GitHub Container Registry의 줄임말이다.

GitHub repository가 source code를 저장하는 곳이라면, GHCR은 Docker image를 저장하는 곳이다.

현재 image 이름은 workflow에서 다음 값으로 만든다.

```yaml
IMAGE_NAME: ghcr.io/${{ github.repository }}
```

이 repository에서는 실제로 다음 이름이 된다.

```text
ghcr.io/jagseeun/agentops-platform
```

Docker build 단계에서는 같은 image에 두 개의 tag를 붙인다.

```text
ghcr.io/jagseeun/agentops-platform:<commit-sha>
ghcr.io/jagseeun/agentops-platform:latest
```

`latest`는 가장 최근에 main에서 build된 image를 쉽게 가리키기 위한 tag다.

`commit-sha` tag는 정확히 어떤 commit으로 만든 image인지 추적하기 위한 tag다.

따라서 평소에는 `latest`를 볼 수 있고, 문제가 생겼을 때는 commit sha tag로 정확한 버전을 추적할 수 있다.

## 실행 조건

두 workflow는 다음 상황에서 실행된다.

- `main` 브랜치에 push될 때
- `main`을 대상으로 pull request를 열거나 업데이트할 때

따라서 feature branch에 push만 하면 실행되지 않는다.

feature branch 작업을 검증하려면 `main`을 대상으로 PR을 열어야 한다.

## Kubernetes manifest

Kubernetes manifest는 GHCR에 올라간 Docker image를 실제 실행 환경에서 어떻게 띄울지 설명하는 파일이다.

현재 manifest는 실제 운영 배포 완성본이 아니라, API와 Worker를 Kubernetes에서 실행하기 위한 초안이다.

파일 위치:

```text
deploy/kubernetes/
```

현재 파일은 다음과 같다.

```text
configmap.yaml
secret.example.yaml
api-deployment.yaml
worker-deployment.yaml
api-service.yaml
```

### ConfigMap

파일:

```text
deploy/kubernetes/configmap.yaml
```

역할:

- 공개해도 되는 환경 변수를 관리한다.
- 현재는 `CELERY_BROKER_URL`을 담는다.

### Secret example

파일:

```text
deploy/kubernetes/secret.example.yaml
```

역할:

- 민감한 환경 변수의 예시를 보여준다.
- 현재는 `DATABASE_URL` 예시를 담는다.
- 실제 비밀번호나 실제 DB URL은 public repository에 넣지 않는다.

### API Deployment

파일:

```text
deploy/kubernetes/api-deployment.yaml
```

역할:

- FastAPI API 컨테이너를 실행한다.
- GHCR image인 `ghcr.io/jagseeun/agentops-platform:latest`를 사용한다.
- `/health` endpoint로 readiness check를 한다.
- ConfigMap과 Secret에서 환경 변수를 가져온다.

### Worker Deployment

파일:

```text
deploy/kubernetes/worker-deployment.yaml
```

역할:

- Celery worker 컨테이너를 실행한다.
- API와 같은 GHCR image를 사용한다.
- 실행 command만 Celery worker 명령으로 바꾼다.
- ConfigMap과 Secret에서 환경 변수를 가져온다.

### API Service

파일:

```text
deploy/kubernetes/api-service.yaml
```

역할:

- `app: agentops-api` label이 붙은 API Pod를 찾는다.
- Kubernetes 내부에서 `agentops-api`라는 Service 이름으로 접근할 수 있게 한다.
- 8000번 port를 API 컨테이너의 8000번 port로 연결한다.

### 아직 남은 것

현재 manifest는 초안이므로 실제 배포 전에 다음이 더 필요하다.

- 실제 DB URL과 Redis URL 결정
- 실제 Secret 생성 방식 결정
- GHCR image 접근 권한 확인
- migration을 언제 실행할지 결정
- 외부 트래픽을 받을 Ingress 또는 LoadBalancer 결정
- Kubernetes 클러스터에서 실제 apply 검증

### Dry run 검증

Docker Desktop Kubernetes context에서 다음 명령으로 manifest dry run을 확인했다.

```powershell
kubectl apply --dry-run=client -f deploy/kubernetes
```

확인된 리소스:

- `deployment.apps/agentops-api`
- `service/agentops-api`
- `configmap/agentops-config`
- `secret/agentops-secret`
- `deployment.apps/agentops-worker`

이 검증은 실제 리소스를 만들지 않고, Kubernetes가 manifest를 생성 가능한 형태로 읽을 수 있는지 확인한다.

### Local apply 검증

Docker Desktop Kubernetes에서 `agentops` namespace를 만들고 manifest를 실제로 적용했다.

```powershell
kubectl create namespace agentops
kubectl apply -n agentops -f deploy/kubernetes
kubectl get pods -n agentops
```

확인한 Pod:

- `agentops-api`
- `agentops-worker`
- `postgres`
- `redis`

모든 Pod가 `Running` 상태가 되는 것을 확인했다.

API는 port-forward로 로컬에서 접근했다.

```powershell
kubectl port-forward -n agentops service/agentops-api 8000:8000
Invoke-RestMethod http://127.0.0.1:8000/health
```

`/health` 응답은 `ok`였다.

Worker 로그에서 Redis 연결도 확인했다.

```text
Connected to redis://redis:6379/0
celery ready
```

Kubernetes 안의 새 Postgres DB에 Alembic migration을 적용했다.

```powershell
kubectl exec -n agentops deployment/agentops-api -- uv run alembic upgrade head
```

그 다음 API를 통해 Workspace를 생성했다.

```powershell
$slug = "k8s-" + [guid]::NewGuid().ToString("N")
$workspace = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/workspaces" -ContentType "application/json" -Body (@{ name = "K8s Smoke"; slug = $slug } | ConvertTo-Json)
$workspace
```

생성된 row는 Postgres Pod 안에서 직접 확인했다.

```powershell
kubectl exec -n agentops deployment/postgres -- psql -U agentops -d agentops -c "select id, name, slug from workspaces;"
```

확인 결과:

```text
id | name      | slug
1  | K8s Smoke | k8s-...
```

이 검증으로 로컬 Kubernetes에서 API, Worker, Postgres, Redis가 함께 실행되고, API 요청이 Kubernetes 안의 Postgres에 저장되는 흐름을 확인했다.

### Local database note

`postgres-deployment.yaml`과 `redis-deployment.yaml`은 로컬 Kubernetes 검증용이다.

운영 환경에서는 Kubernetes 안에 직접 DB를 띄우기보다 Neon DB 같은 managed PostgreSQL과 managed Redis 사용을 전제로 한다.

### Neon DB 연결 검증

Neon DB는 managed PostgreSQL로 사용한다.

로컬 PowerShell에서 `DATABASE_URL`을 Neon connection string으로 임시 설정하고 SQLAlchemy 연결을 확인했다.

주의:

- Neon connection string에는 비밀번호가 포함되므로 repository와 문서에 기록하지 않는다.
- 로컬 검증에서는 PowerShell 환경 변수로만 임시 설정한다.
- Kubernetes에서는 실제 값을 `Secret`으로 주입한다.

연결 확인:

```powershell
uv run python -c "from app.db.session import engine; print(engine.url.render_as_string(hide_password=True)); print(engine.connect().exec_driver_sql('select 1').scalar())"
```

확인 결과:

```text
postgresql+psycopg://neondb_owner:***@...neon.tech/neondb?...
1
```

Neon DB는 새 DB였기 때문에 Alembic migration을 적용했다.

```powershell
uv run alembic upgrade head
```

확인 결과:

```text
Running upgrade  -> 92a89413b8f7, initial schema
```

FastAPI를 Neon DB에 연결한 상태로 실행한 뒤 Workspace 생성을 확인했다.

```powershell
$slug = "neon-" + [guid]::NewGuid().ToString("N")
$workspace = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/workspaces" -ContentType "application/json" -Body (@{ name = "Neon Smoke"; slug = $slug } | ConvertTo-Json)
$workspace
```

Neon DB에서 row 직접 조회도 확인했다.

```powershell
uv run python -c "from app.db.session import engine; print(engine.connect().exec_driver_sql('select id, name, slug from workspaces').all())"
```

확인 결과:

```text
[(1, 'Neon Smoke', 'neon-...')]
```

이 검증으로 로컬 FastAPI 코드가 Neon PostgreSQL에 연결되고, migration과 write/read가 정상 동작하는 것을 확인했다.

### Kubernetes에서 Neon DB 사용 검증

Kubernetes API/Worker가 로컬 Postgres Pod가 아니라 Neon DB를 바라보도록 `agentops-secret`을 교체했다.

실제 Neon connection string은 비밀값이므로 manifest나 문서에 기록하지 않는다.

사용한 흐름:

```powershell
kubectl delete secret -n agentops agentops-secret
kubectl create secret generic agentops-secret -n agentops --from-literal=DATABASE_URL="<neon-database-url>"
kubectl rollout restart deployment/agentops-api -n agentops
kubectl rollout restart deployment/agentops-worker -n agentops
```

Secret 변경 후 기존 Pod는 자동으로 새 환경 변수를 읽지 않으므로 API와 Worker Deployment를 재시작했다.

재시작 후 port-forward를 통해 Kubernetes API에 요청을 보냈다.

```powershell
$slug = "k8s-neon-" + [guid]::NewGuid().ToString("N")
$workspace = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/workspaces" -ContentType "application/json" -Body (@{ name = "K8s Neon Smoke"; slug = $slug } | ConvertTo-Json)
$workspace
```

확인 결과:

```text
id: 2
name: K8s Neon Smoke
slug: k8s-neon-...
status: active
```

이전에 로컬 FastAPI로 Neon DB에 생성한 Workspace가 `id: 1`이었고, Kubernetes API로 생성한 Workspace가 `id: 2`가 되었다.

이 결과로 로컬 FastAPI와 Kubernetes API가 같은 Neon DB를 바라보고 있음을 확인했다.

### Cleanup

로컬 Kubernetes 실습 리소스는 namespace 단위로 삭제한다.

```powershell
kubectl delete namespace agentops
```

이 명령은 `agentops` namespace 안에 만든 API, Worker, Postgres, Redis, Service, Secret, ConfigMap을 모두 삭제한다.

## 현재 흐름

현재 검증 흐름은 다음과 같다.

```text
feature branch 작업
  |
  v
main 대상 PR 생성
  |
  v
CI 실행
  |
  +--> PostgreSQL + pytest 검증
  |
  +--> Docker image build 검증
  |
  v
초록 체크 확인 후 merge
  |
  v
main push
  |
  v
GHCR image push
```

## 다음 단계

다음 단계는 GHCR에 올라간 image를 실제 배포 설정에서 사용할 수 있게 준비하는 것이다.

예상 흐름:

```text
GHCR image
  |
  v
Kubernetes manifest
  |
  v
API/Worker deployment
```

그 다음 단계는 Kubernetes manifest를 작성해서 API와 Worker를 배포 가능한 형태로 정리하는 것이다.
