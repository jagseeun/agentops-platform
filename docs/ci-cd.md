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
