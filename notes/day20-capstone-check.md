# Day 20 Capstone Check

## 목표
새 환경처럼 compose 기반으로 AgentOps Platform을 실행하고, API부터 Worker까지 Run 처리 흐름이 끝까지 동작하는지 확인했다.
확인 대상 서비스는 다음과 같다.
- api
- worker
- postgres
- redis

## 실행 확인
`docker compose up --build -d`로 전체 서비스를 실행했다.
`docker compose ps`에서 다음 상태를 확인했다.
- api : Up
- worker: Up
- postgres: healthy
- redis: healthy
worker 로그에서 Celery가 Redis broker에 연결된 것도 확인했다.
- broker: `redis//redis:6379/0`
- task: `app.workers.tasks.process_run_task`
- result backend: disabled

## 발견한 문제
처음에는 컨테이너 안에서 Alembic 확인이 실패했다.
원인은 Docker 이미지 안에 migration 관련 파일이 없었기 때문이다.
누락된 파일 : 
- `alembic.ini`
- `alembic/`
해결 방법으로 Dockerflie에 Alembic 설정과 migration 폴더를 복사하도록 추가했다.
이후 컨테이너 안에서 Alembic 상태 확인이 가능해졌다.

## Run 처리 확인
compose로 실행한 API와 Worker를 기준으로 Run 생성 흐름을 확인했다.
진행한 흐름 :
- workspace 생성
- agent 생성
- workflow 생성
- workflow를 active로 변경
- run 생성
- worker가 task 처리
- run 상태 확인
최종 결과 : 
- workspace_id: 6
- workflow_id: 2
- run_id: 2
- status: completed
- started_at 값 생성됨
- finished_at 값 생성됨
- error_message 없음

## 내가 이해한 흐름
Run은 PostgreSQL에 저장된다.
Run을 만들면 처음 상태는 queued다.
FastAPI는 process_run_task.delay(run.id)로 Redis에 run_id를 전달한다.
Celey worker는 Redis에서 run_id를 꺼내고, process_run(run_id)를 실행한다.
Worker는 PostgreSQL에서 Run을 다시 찾아 상태를 바꾼다.
흐름은 다음과 같다.
```text
Run 생성
-> PostgreSQL에 queued로 저장
-> Redis에 run_id 전달
-> Celery worker가 run_id 수신
-> process_run(run_id) 실행
-> running
-> completed
```

## 장애와 복구 관점
Day 20 에서 확인한 중요한 장애는 컨테이너 이미지에 migration 파일이 누락된 문제였다.
로컬에서는 파일이 있어서 괜찮아 보였지만, 컨테이너 안에는 alembic.ini와 alembic/이 없어서 Alembic 명령이 실패했다.
이 문제를 통해 새 환경 검증에서는 로컬 기준이 아니라 컨테이너 내부 기준으로 확인해야 한다는 것을 알게 되었다.

## 개선하면 좋을 점
이번 Run 처리 확인은 PowerShell 명령을 수동으로 여러 번 실행했다.
반복하기에는 명령이 길기 때문에 이후에는 smoke script로 자동화하는 것이 좋다.
예상 후보 : 
- tools/celery_smoke.py
목표는 다음을 한 번에 확인하는 것이다.
- workspace 생성
- agent 생성
- workflow 생성
- run 생성
- completed 확인

## 정리
Day 20에서 compose 기반 실행, migration 확인, API healthy, Celery worker 연결, Run completed 흐름을 확인했다.
AgentOps Mini Platform이 PostgreSQL과 Redis/Celery worker를 사용하는 구조로 동작하는 것을 끝까지 검증했다.