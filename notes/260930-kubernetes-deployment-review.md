# 2026-09-30 Kubernetes Deployment Review

## 오늘 한 일
- GitHub Actions에서 Kubernetes rollout을 실행할 수 있는 workflow를 추가했다.
- API Service를 ClusterIP에서 LoadBalancer로 변경했다.
- LoadBalancer를 통해 port-forward 없이 `/health` 요청이 되는 것을 확인했다.

## 내가 이해한 것
- LoadBalancer는 외부 요청이 Kubernetes Service를 통해 API Pod가지 들어가게 해준다.
- KUBE_CONFIG는 GitHub Actions가 Kubernetes 클러스트에 접속하기 위하 설정 파일이다.
- DATABASE_URL은 API/Worker가 Neon DB에 접속하기 위한 값이다.
- CELERY_BROKER_URL은 Celery가 Redis queue를 찾기 위한 값이다.

## 아직 안 된 것
- GitHub Actions에서 실제 Kubernetes rollout를 실행하지는 않았다.
- 이유는 GitHub Secret에 KUBE_CONFIG가 아직 없고, 현재 Kubernetes가 로컬 Docker Desktop 환경이기 때문이다.
- 실제 실행에는 GitHub Actions가 접근 가능한 클라우드 Kubernetes 또는 self-hosted runner가 필요하다.

## 확인한 것
- LoadBalancer Service로 API 외부 접근 확인
- http://127.0.0.1:8000/health 요청 결과 ok