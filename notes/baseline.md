## Gate 1 Baseline

## Git 기준 상태
- 초기 AgentOps Mini 상태는 이미 commit/push 했다.
- git status --short 결과가 비어 있었다.
- 따라서 working tree는 clean 상태이다.
- 현재 브랜치는 main이다. 

## 확인한 명령
- git status --short
    - working tree가 clean한지 확인했다.
    - 결과 : 출력 없음
- git branch --show-current
    - 현재 기준 브랜치를 확인했다.
    - 결과 : main
- rg -n "create_engine|SessionLocal|DATABASE_URL|create_all" app tests
    - DB engine, SessionLocal, DATABASE_URL, create_all 위치를 확인했다.
- rg -n "process_run|poll|queued|fail_timed_out_runs" app tests
    - Worker polling 진입점, process_run(), queued 상태, timeout 실패 처리 위치를 확인했다.

## 테스트 기준
- 이전에 확인한 전체 테스트 결과는 74개 통과다.
- Gate 1에서는 전체 테스트를 다시 실행하지 않았다.
- 이유는 현재 테스트가 기본 SQLite DB인 agentops.db를 오염 시킬 수 있기 때문이다.

## DB 구조 위치
- engine 정의 파일 : app/db/session.py
- SessionLocal 정의 파일 : app/db/session.py
- Base.metadata.create_all() 위치 : app/main.py:10

## Worker / Run 위치
- polling Worker 진입점 : app/workers/run_worker.py:10의 process_next_queued_run()
- process_run() 위치 : app/workers/run_worker.py:27
- Run 생성 후 queued가 되는 위치 : app/models/run.py:13

## 완료 기준
- 기존에 확인한 74개 통과 결과를 기준으로 기록했다.
- 파일 위치를 notes/baseline.md에 기록했다.
- 작업 브랜치를 만들었다: feat/postgres-celery-upgrade
