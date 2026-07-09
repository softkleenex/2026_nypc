# User Log Storage Review

검토 시점: 2026-07-08 12:44 KST 이후. 2026-07-08 13:00 KST경 표준 구조로 이동 완료.

## 결론

현재 `bots/`의 유저 로그는 `bots/user_logs/` 아래 표준 구조로 정리했다. 새 중간평가 로그도 평가 번호와 시각을 드러내는 폴더에 저장하고, 각 대전 로그는 `<대전ID>_<A|B>.txt` 형식을 표준으로 삼는다.

## 현재 상태

| 폴더 | 성격 | 상태 |
| --- | --- | --- |
| `bots/user_logs/eval14_bot_unknown_20260703_1500/` | 과거 평가 #14 | 팀명 기반 원본 파일을 `matches/eval14_<번호>_<A|B>.txt`로 정규화, 원본명은 `manifest.tsv`에 보존 |
| `bots/user_logs/eval25_bot62_20260707_1000/` | 중간평가 #25, 2026-07-07 10:00 KST | 대전 로그 20개, `ranking.txt`, `manifest.tsv` 포함 |
| `bots/user_logs/eval26_bot77_20260707_1500/` | 중간평가 #26, 2026-07-07 15:00 KST | 대전 로그 20개, `ranking.txt`, `manifest.tsv` 포함 |
| `bots/user_logs/eval28_bot91_20260708_1000/` | 중간평가 #28, 2026-07-08 10:00 KST | 대전 로그 20개, `ranking.txt`, `manifest.tsv` 포함 |

## 표준 저장 방식

```text
bots/
  user_logs/
    eval<eval-no>_bot<bot>_<YYYYMMDD_HHMM>/
    ranking.txt              # 순위/퍼포먼스/대전 목록 원본 텍스트
    manifest.tsv             # 파일명, 원본명, 진영, 결과 매핑
    summary.tsv              # 선택: 직접 만든 요약표 또는 과거 요약
    matches/
      <match-id>_A.txt        # 우리가 LEFT
      <match-id>_B.txt        # 우리가 RIGHT
```

기존처럼 `무제.txt`로 받은 순위 페이지는 `ranking.txt`로 저장한다. 원래 파일명이나 상대 팀명은 `manifest.tsv`에 남긴다.

## 운영 규칙

- 유저 로그는 삭제하거나 덮어쓰지 않는다. 정리할 때는 `manifest.tsv`로 원본 파일명과 새 파일명을 연결한다.
- 상대 팀 이름은 시간에 따라 의미가 약해질 수 있으므로 파일명보다 `대전ID`를 기준으로 식별한다.
- 중간평가 상대와 상대 코드 수준은 평가 시각마다 바뀔 수 있다. 분석은 절대 점수보다 진영별 승패, 티어별 손실, WA/급사, 성장 곡선 중심으로 한다.
- 새 평가 저장 후 `cd bots && tar czf archive/logs_backup_<날짜>.tar.gz *_nypc_log user_logs`로 백업을 갱신한다.
