# Deployment Pipeline Progress

## 오늘 한 일

AgentOps Platform을 로컬 실행 수준에서 배포 준비 단계까지 확장했다.

큰 흐름은 다음과 같다.

```text
CI
→ Docker image build
→ GHCR publish
→ Kubernetes manifest
→ local Kubernetes apply
→ migration Job
→ Neon DB 연결
→ Kubernetes API에서 Neon DB write 검증
```

## CI

GitHub Actions에서 pytest를 자동 실행하도록 구성했다.

CI는 PostgreSQL service를 띄우고, `agentops_test` DB를 만든 뒤 Alembic migration과 pytest를 실행한다.

이제 main 또는 main 대상 PR에서 테스트가 자동으로 검증된다.

## Docker image와 GHCR

Dockerfile로 image가 정상 build 되는지 확인하는 workflow를 추가했다.

main push에서는 image를 GHCR에 publish한다.

image 이름은 다음 형태다.

```text
ghcr.io/jagseeun/agentops-platform:latest
ghcr.io/jagseeun/agentops-platform:<commit-sha>
```

`latest`는 최신 main image를 가리키고, `commit-sha`는 특정 commit으로 만든 image를 추적하기 위해 사용한다.

## Kubernetes manifest

`deploy/kubernetes/`에 API, Worker, ConfigMap, Secret 예시, Service manifest를 추가했다.

로컬 Kubernetes 검증을 위해 Postgres와 Redis manifest도 추가했다.

운영에서는 Kubernetes 안에 직접 DB를 띄우기보다 Neon DB 같은 managed PostgreSQL을 사용하는 방향이 더 적절하다.

## Local Kubernetes 검증

Docker Desktop Kubernetes에서 `agentops` namespace를 만들고 manifest를 실제 적용했다.

확인한 것:

- API Pod Running
- Worker Pod Running
- Postgres Pod Running
- Redis Pod Running
- API `/health` 응답 확인
- Worker가 Redis에 연결되는 로그 확인
- Alembic migration 적용
- API로 Workspace 생성
- Postgres Pod에서 row 직접 조회

이 검증으로 Kubernetes 안에서 API, Worker, Postgres, Redis가 함께 동작하는 흐름을 확인했다.

## Migration Job

처음에는 API Pod 안에서 직접 migration을 실행했다.

```powershell
kubectl exec -n agentops deployment/agentops-api -- uv run alembic upgrade head
```

이후 `migration-job.yaml`을 추가해서 Alembic migration을 Kubernetes Job으로 실행할 수 있게 했다.

Job은 한 번 실행하고 끝나는 작업에 적합하다.

완료된 Job이 계속 남지 않도록 `ttlSecondsAfterFinished: 300`도 추가했다.

## Neon DB 검증

Neon DB를 managed PostgreSQL로 연결했다.

검증한 것:

- SQLAlchemy engine으로 Neon 연결
- `select 1` 성공
- Alembic migration을 Neon DB에 적용
- 로컬 FastAPI에서 Neon DB로 Workspace 생성
- Neon DB에서 row 직접 조회

Neon connection string은 secret이므로 문서나 repository에 기록하지 않는다.

## Kubernetes에서 Neon DB 사용

Kubernetes의 `agentops-secret`을 Neon `DATABASE_URL`로 교체했다.

Secret 변경 후 API와 Worker Deployment를 rollout restart했다.

Kubernetes API를 통해 Workspace를 생성했고, Neon DB에 저장되는 것을 확인했다.

로컬 FastAPI로 만든 Workspace가 `id: 1`, Kubernetes API로 만든 Workspace가 `id: 2`가 되어서 두 실행 환경이 같은 Neon DB를 바라보고 있음을 확인했다.

## 오늘 이해한 것

- `DATABASE_URL`을 바꾸면 같은 코드가 다른 PostgreSQL을 바라볼 수 있다.
- Neon은 MongoDB가 아니라 managed PostgreSQL이다.
- `psycopg`는 Python/SQLAlchemy가 PostgreSQL과 통신하게 해주는 driver다.
- Kubernetes Pod는 컨테이너를 담아 실행하는 단위다.
- Service는 Pod를 이름으로 찾고 연결하게 해준다.
- Job은 한 번 실행하고 끝나는 작업에 적합하다.
- Completed Job은 실패가 아니라 정상 종료 상태다.
- TTL은 완료된 Job을 일정 시간 뒤 자동 삭제하기 위한 설정이다.

## 아직 남은 것

- Redis를 managed Redis로 바꿀지 결정
- GitHub Actions에서 Kubernetes rollout까지 자동화
- Ingress 또는 LoadBalancer로 외부 접속 구성
- production Secret 관리 방식 정리
- observability와 로그/메트릭 강화
