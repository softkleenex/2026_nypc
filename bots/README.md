# Bots Directory Guide

이 폴더는 NYPC 제출 봇, 선택 데이터 파일, 공식/중간평가 로그를 보관한다. 자세한 개발 흐름은 `../docs/workflow-strategy.md`, 현재 컨텍스트는 `../AGENTS.md`를 먼저 확인한다.

## Submission Units

- 기본 제출 단위는 `숫자.py`와 선택 파일 `숫자.data` 한 세트다.
- 현재 루트에는 전환점 `77.py`, 비교 기준 `90.py`/`91.py`, 개선 후보 `125.py`, 최신 후보 `132.py`-`135.py`만 둔다. 발견된 `.data` 파일은 없다.
- 같은 번호의 코드와 데이터는 같은 제출 후보로 취급한다. 둘 중 하나라도 바꾸면 새 번호를 사용한다.
- Python 외 언어를 쓰는 경우에도 번호를 기준으로 같은 규칙을 적용한다.

## Active Files

```text
<n>.py                 제출 코드 또는 제출 후보
<n>.data               선택 데이터 파일, 있을 때만 코드와 같은 번호로 보관
<n>_nypc_log/          제출 직후 NYPC가 제공하는 8개 공식 봇 상대 로그
user_logs/             정형화한 중간평가 로그
archive/               지난 세대 코드, 중요 로그, logs_backup_*.tar.gz 백업
```

## NYPC Logs

`<n>_nypc_log/`는 제출 이후 거의 즉시 제공되는 8개 공식 봇과의 대전 기록이다. 가능하면 파일명을 `1.txt`부터 `8.txt`까지 정규화한다. 이 로그는 같은 제출 코드의 공식 샘플 환경을 읽는 핵심 자료이므로 분석 후에도 삭제하지 않는다.

## User Evaluation Logs

`user_logs/`는 중간평가 결과다. 상대는 매 평가마다 달라질 수 있고, 상대 팀의 대표 제출 코드도 시간에 따라 바뀔 수 있다. 따라서 절대 점수보다 진영별 승패, 티어별 손실, 급사/WA, 성장 곡선을 본다.

표준 구조는 `user_logs/eval<번호>_bot<봇번호>_<YYYYMMDD_HHMM>/` 아래 `ranking.txt`, `manifest.tsv`, `matches/`이다. `matches/`의 파일명은 가능한 한 `<대전ID>_<A|B>.txt`를 사용한다. `A`는 우리가 LEFT였다는 뜻이다.

현재 보관된 유저 로그는 `user_logs/eval14_bot_unknown_20260703_1500/`, `eval25_bot62_20260707_1000/`, `eval26_bot77_20260707_1500/`, `eval28_bot91_20260708_1000/`이다.

## Storage Rules

- 로그 폴더는 읽기 전용 원자료로 취급한다.
- 정리 스크립트는 로그 폴더를 순회 삭제하지 않는다.
- 새 공식/유저 로그를 추가한 뒤에는 `cd bots && tar czf archive/logs_backup_<날짜>.tar.gz *_nypc_log user_logs`로 백업을 갱신한다.
- 로컬 실험 출력은 `../results/<name>/`에 둔다. 결론을 문서화하기 전에는 삭제하지 않는다.
