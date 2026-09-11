# AgentOps Mini Platform

AI Agent, Workflow, Run, Worker, Model Gateway, 권한/로그/운영 리스크를 학습하기 위한 신입 개발자용 미니 플랫폼입니다.

## 실행

~~~bash
uv run uvicorn app.main:app --reload
~~~

## 테스트

~~~bash
uv run pytest
~~~

## 현재 구현된 기능

- GET /health
- POST /workspaces
- Agent Registry 기본 모델/schema

## 현재 모델

### Workspace

Workspace는 조직/고객사 단위로 데이터를 묶는 상위 리소스입니다.

### Agent

Agent는 실제 LLM 호출 코드가 아니라, Workflow에서 사용할 수 있는 Agent 정의입니다.
예: summarizer v1, classifier v2

Agent는 Workspace에 속하고, 같은 Workspace 안에서 같은 name + version은 중복될 수 없습니다.
현재는 모델과 schema만 구현되어 있으며, Agent 생성 API는 아직 없습니다.

## 현재 API

### GET /health

서버 상태 확인용 API입니다.

### POST /workspaces

Workspace를 생성합니다.

Request:

~~~json
{
  "name": "Acme",
  "slug": "acme"
}
~~~

Response:

~~~json
{
  "id": 1,
  "name": "Acme",
  "slug": "acme",
  "status": "active",
  "created_at": "..."
}
~~~

## Docker 실행

### Docker Compose로 실행
```bash
docker compose up --build
```

### Health check
```bash
curl http://127.0.0.1:8000/health
```

기대 응답 : 
```json
{"status" : "ok"}
```

### 종료
```bash
docker compose down
```

