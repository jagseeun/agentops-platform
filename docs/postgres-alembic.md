# PostgreSQL과 Alembic

## Fresh DB 절차
- PostgreSQL 컨테이너를 실행한다.
`docker compose up -d postgres`

- PostgreSQL 상태를 확인한다.
`docker compose ps`

- migration을 적용한다.
`uv run alembic upgrade head`

- 현재 적용된 migration을 확인한다.
`uv run alembic current`

## 앱 실행 기준
- 앱은 시작할 때 table을 자동 생성하지 않는다.
- DB schema는 Alembic migration이 관리한다.
- 빈 DB에서 API를 실행하려면 먼저 migration을 적용해야 한다.

## Health check
- API를 실행한다.
`uv run uvicorn app.main:app --reload`

- health endpoint를 확인한다.
`Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health`