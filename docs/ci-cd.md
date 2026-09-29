# CI/CD Notes

이 문서는 AgentOps Platform의 CI/CD 흐름을 정리한 문서다.

현재 단계에서는 완전한 자동 배포까지 가지 않고, 먼저 다음 두 가지를 자동화한다.

- 테스트 자동 실행
- Docker image build 확인

## CI와 CD의 차이

CI는 코드를 main에 넣기 전에 프로젝트가 깨지지 않았는지 자동으로 확인하는 과정이다.

이 프로젝트의 CI는 GitHub Actions에서 PostgreSQL을 띄우고, 테스트 DB를 만든 뒤 migration과 pytest를 실행한다.

CD는 테스트를 통과한 코드를 실제 실행 환경에 배포하는 과정이다.

아직 이 프로젝트는 실제 서버나 Kubernetes 클러스터에 자동 배포하지 않는다. 지금은 CD로 가기 전 단계로 Docker image가 정상적으로 build 되는지만 확인한다.

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

아직 image를 registry에 push하지는 않는다.

현재 목표는 "이 앱이 컨테이너로 포장 가능한 상태인가"를 확인하는 것이다.

## 실행 조건

두 workflow는 다음 상황에서 실행된다.

- `main` 브랜치에 push될 때
- `main`을 대상으로 pull request를 열거나 업데이트할 때

따라서 feature branch에 push만 하면 실행되지 않는다.

feature branch 작업을 검증하려면 `main`을 대상으로 PR을 열어야 한다.

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
```

## 다음 단계

다음 단계는 Docker image를 GitHub Container Registry에 push하는 것이다.

예상 흐름:

```text
main merge
  |
  v
Docker image build
  |
  v
GHCR push
```

그 다음 단계는 Kubernetes manifest를 작성해서 API와 Worker를 배포 가능한 형태로 정리하는 것이다.
