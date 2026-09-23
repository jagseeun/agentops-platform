# Day 18 Worker Shutdown Check

## 확인한 상황
Worker가 Run을 claim한 뒤 중간에 종료되면 Run이 running 상태로 남을 수 있다.
현재 구조에서는 worker 종료 자체를 자동으로 복구하는 별도 supervisor는 없다. 대신 오래된 running Run을 찾아 failed로 바꾸는 복구 함수가 있다.

## 복구 경로
코드 위치는 `app/workers/run_worker.py`의 `fail_timed_out_runs()`이다.
이 함수는 다음 조건의 Run을 찾는다.
- status가 running
- started_at이 timeout 기준보다 오래 됨.

해당 Run은 다음 상태로 바뀐다.
- status : `failed`
- error_message: `run timed out after {timeout_seconds} seconds`
- finished_at 기록

## 테스트로 확인한 것
`tests/runs/test_run_worker.py`에서 다음 흐름을 확인했다.
- 최근 running Run은 failed로 바꾸지 않는다.
- 오래된 running Run 하나는 failed로 바꾼다.
- 오래된 running Run 여러 개를 failed로 바꾼다.
- timeout으로 failed 된 Run은 retry API로 다시 queued가 될 수 있다.

## Day 17과의 관계
Day 17에서 atomic claim을 추가 했기 때문에 같은 run_id가 중복 전달되어도 하나의 worker에서만 queued Run을 running으로 바꿀 수 있다.

Day 18의 복구는 그 이후 상황을 다룬다.
```text
claim 성공
-> running
-> worker 중간 종료
-> stuck running
-> fail_timed_out_runs()
-> failed
-> retry API
-> queued
```

## 현재 정책
- worker가 종료되면 Run이 running에 남을 수 있다.
- 오래된 running Run은 timeout 복구 대상으로 본다.
- timeout 복구 후 사용자는 retry API로 다시 실행할 수 있다.
- redelivery가 발생해 같은 run_id가 와도 atomic claim 때문에 이미 running인 Run은 다시 claim되지 않는다.