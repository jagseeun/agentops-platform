# Day 16 Retry Policy

## 세 종류의 retry

## 1. Run retry
사용자가 failed Run을 다시 실행하는 재시도이다.
코드 위치는 RunService.retry_run()이다.
현재 정책 : 
- failed 상태의 Run만 retry 가능
- retry_count가 3 이상이면 차단
- retry 하면 retry_count를 1 증가
- Run status를 queued로 되돌린다.
- retry API에서 audit log를 남긴다.

## 2. Task retry
Celery worker가 일시적인 오류 때문에 같은 task를 다시 실행하는 재시도이다.
예시 : 
- DB 연결이 순간적으로 실패
- 외부 provider가 잠까나 실패
- worker 내부에서 일시적인 예외 발생
현재 process_run_task(run_id)는 기존 process_run(run_id)를 한 번 호출한다.

Task retry는 Run retry와 다르다.
- 사용자가 누르는 재시도가 아니다.
- Run retry_count를 올리는 정책과 섞지 않는다.
- 무한 retry가 되면 안된다.

## 3. Redelivery
worker가 메시지를 받은 뒤 완료 확인 전에 종료되면 broker가 메시지를 다시 전달할 수 있다.
Redeivery는 task retry와 다르다.
- task 코드가 retry를 요청한 것이 아니다.
- broker/worker의 메시지 전달 문제이다.
- 같은 run_id가 다시 들어올 수 있으므로 중복 실행 방지가 필요하다.

## 현재 정책
- Run retry는 사용자 요청 기반으로 유지한다.
- task retry는 무한 재시도를 하지 않는다.
- redelibery는 Day 17의 atomic claim으로 중복 실행을 막는다.
- validation 오류와 권한 오류는 task가 생성되기 전 API에ㅔ서 실패하므로 task retry 대상이 아니다.

## 다음 작업
Day 17에서 같은 run_id가 두 번 전달되어도 하나의 worker만 Run을 처리하도록 atomic claim을 추가한다.