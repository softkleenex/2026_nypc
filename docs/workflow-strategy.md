# NYPC Workflow and Strategy

이 문서는 기존 `docs/workflow.md`와 `strategy-plan.md`를 하나로 묶은 운영 문서다. 원문 내용은 아래 영역에 그대로 포함했고, 개발 루프와 누적 전략 기록은 이 문서를 기준으로 확인한다.

## 읽기 순서

1. 기존 `docs/workflow.md` 영역에서 검증 루프, 로그 정책, 제출 전 안전망을 확인한다.
2. 기존 `strategy-plan.md` 영역에서 과거 제출 결과, 현재 가설, 후보 연구 기록을 확인한다.
3. 새 실험 결론은 원본 흐름에 맞춰 전략 기록으로 남기고, 로그 원본은 보존한다.

## 보존 원칙

서버 A/B 로그와 유저 로그는 유일한 실측 데이터다. 이 통합본은 원문을 그대로 포함하며, 별도 통합 검사 문서는 공개 정리 과정에서 제거했다.

## 최신 작업 메모 (2026-07-08 19:50 KST, 183 후보)

- **후보 `bots/183.py + bots/183_data.bin` = 180 기반 + 그룹 HQ 의도 데이터
  + T30~70 근접 압박 요새화 보정.** `data.bin`에는 archive user log에서
  만든 `group_hq_policy` 15개 키를 추가했다. signal-only 키
  `(trace_hq_support bucket, target_policy_hq_support bucket)`는 held-out
  crossval에서 예측 189턴 중 184턴 정답, 오탐 5턴이었다. 다만 181에서
  이 신호는 eval29/proxy/direct 결과를 바꾸지 않아 **안전한 no-op 보강**으로
  해석한다.
- **실질 개선:** `243173_B`는 T50부터 기지 0개로 무너지고 T78부터 적 HQ행이
  시작되는 경제 붕괴형 손실이었다. 단순 `early_fortress` 완화(182)는
  `243173_B`를 T91 HQ패에서 T52 replay-WA 승 분기로 바꿨지만 proxy-rush
  seed1 구간에 2패를 만들었다. 183은 조건을 `len(enemy) >= len(mine)+1`,
  `invaders>=3`, `near_enemy>=3`, `turn<70`으로 좁혀 먼 전방 진입에는
  반응하지 않고 실제 본부 3홉권 압박에만 요새화한다.
- **검증:** `py_compile` 통과. eval29 replay-left는 180/181의 `19W/1L/0D`에서
  `20W/0L/0D`로 개선(`243173_B`: replay-WA), replay-right는 `19W/1L/0D`
  유지. sample10 `10W/0L/0D`. proxy seed1 count20 양진영은 180과 동일
  (`rush 40/0/0`, `econ 34/0/6`, `turtle 40/0/0`, `punch 40/0/0`).
  proxy seed41 count20 양진영은 non-rush 동일, rush는 180의 `32/8/0`에서
  183의 `36/4/0`으로 개선. 77/90 direct seed1 및 seed41 count20 양진영은
  180과 동일(`seed1 5/0/35`, `seed41 4/1/35`). `183_data.bin`은 19,087
  bytes, 전체 제출 파일 합계 약 84KB.
- **판정:** 183은 180보다 좁게 낫다. 개선은 replay-WA이므로 확정 승 증거는
  아니지만, 프록시 rush seed41 개선과 non-rush/direct 무회귀가 있어 현재
  최신 후보로 분류한다.

## 최신 작업 메모 (2026-07-08 16:27 KST, 151 후보)

- **후보 `bots/151.py` = 150 + 초단기 delayed mass 즉시 감지.** `241470_B`
  는 T25에 이미 상대 HQ L1, 상대 병력 `>= 내 병력 +4`, 상대 기지 수 <
  내 기지 수였는데, 150은 실제 침공 병력이 보일 때까지 기다려 T35 이후에야
  확장 루프를 멈췄고 이미 확장병이 빠진 뒤였다. 151은 같은 delayed mass
  조건 안에서 T35 전 이 강한 신호가 보이면 즉시 `rush_alert`를 켠다.
- **효과:** 150 대비 eval29에서 `241470_B`가 추가로 T61 HQ패에서 T50
  replay-WA 승 분기로 바뀐다. 151의 archived user replay는 100게임
  `92W/6L/2D`(`A: 62W/1L/1D`, `B: 30W/5L/1D`). 150 대비 유일한 결과
  변화는 `241470_B` 한 건이다.
- **검증:** `py_compile` 통과, sample16 `16W/0L/0D WA0`. proxy-rush
  seed1/41/81은 150과 동일(`65/15`, `68/12`, `59/21`). non-rush
  seed1/41/81도 150 및 145와 동일(`econ 66/1/13`, `67/2/11`, `68/3/9`;
  `turtle 79/0/1`, `76/0/4`, `79/0/1`; `punch 80/0/0` all). 77/90 direct
  seed1/41/81도 145/150과 동일(`4/0/76`, `6/1/73`, `10/8/62`; 90 seed81
  `10/6/64`). 공식 로그 97개 오른쪽 고정 재생은 `97W/0L/0D`. 파일 크기
  52,563 bytes, 누수 스캔은 프로토콜 `print("OK")`와 커맨드 출력만 남음.
- **판정:** 151은 150보다 좁게 더 낫다. 단, `241470_B` 개선도 replay-WA라
  실전 확정승은 아니며, “유저 대결 확실한 상위호환”보다는 “측정 회귀 없는
  rush 신호 보강 후보”로 분류한다. 추가 대형 시스템(상대 이동방향 추정,
  data.bin, 맵별 프로필)은 이식·오판 리스크가 커서 이번 제출 직전에는
  보류한다.

## 이전 작업 메모 (2026-07-08 16:08 KST, eval29 반영)

- **새 유저 로그 정형화:** `bots/145_user_log`의 중간평가 #29 로그를
  현재는 `bots/eval29_bot145_user_log/` 표준 구조로 보존한다.
  `summary.md`, `ranking_raw.txt`, match log 20개가 있으며 원본은
  건드리지 않았다. 사이트 결과는 Tier 9, rating 1920, 469/914위,
  `9W/10L/1D`.
- **145 재현:** eval29 전체를 현재 `bots/145.py`로 고정 재생하면 사이트
  결과와 동일한 `9W/10L/1D`, WA 0. 이번 로그는 replay 불일치가 아니라
  실제 약점 표본이다. 비승은 조기 HQ 사망형(`237667_B`, `240995_B`,
  `241470_B`, `242702_B`, `243173_B`, `245380_A`), 중후반 econ 압살형
  (`238554_B`), 턴제한/점수형(`239085_A`, `243657_B`, `244080_B`,
  `244910_B`)으로 분류했다.
- **후보 `bots/150.py`: delayed mass rush latch.** T25~60에 상대 HQ가 L1,
  상대 병력 `>= 내 병력 + 3`이면 delayed mass 기반 조건을 계산한다. 상대가
  기지를 덜 먹고 병력을 모은 사실을 T50 전까지 latch하고, 이후 실제 침공
  병력 `invaders >= 2`가 보이거나 같은 창에서 `invaders >= 4`이면
  `rush_alert`로 승격해 신규 확장/기지 건설을 멈춘다. 목적은 “기지 대신
  병력”으로 오는 중간 타이밍 러시에 확장 루프를 끊는 것이다.
- **eval29 효과:** `150.py`는 `245380_A`, `237667_B`, `240995_B`를
  replay-WA 승 분기로 바꾼다. 전체 archived user replay는 `91W/7L/2D`
  (eval29 포함 100게임). 145 기준 eval29 포함 누적은 `88W/10L/2D`였으므로
  손실 3개가 분기된다. 남는 eval29 비승은 `238554_B`, `239085_A`,
  `241470_B`, `242702_B`, `243173_B`, `243657_B`, `244080_B`, `244910_B`.
- **로컬 검증:** sample16 `16W/0L/0D WA0`. proxy-rush가 145 기준
  seed1/41/81 `62/18`, `66/14`, `56/24`에서 `65/15`, `68/12`, `59/21`로
  개선. non-rush seed1/41/81은 145와 동일(`econ 66/1/13`, `67/2/11`,
  `68/3/9`; `turtle 79/0/1`, `76/0/4`, `79/0/1`; `punch 80/0/0` all).
  77/90 direct seed1/41/81도 145와 동일(`4/0/76`, `6/1/73`,
  `10/8/62`; 90 seed81 `10/6/64`). 145와 150의 직접대결은 seed1~80
  `4/4/152`, seed81~160 `5/5/150`으로 대칭이다. 공식 로그 97개 오른쪽
  고정 재생은 `97W/0L/0D`. 파일 크기 52,424 bytes, 누수 스캔은 프로토콜
  `print("OK")`와 커맨드 출력만 남음.
- **data.bin 판단:** 2025 후기 3개를 확인했다. 상위권/상위 5% 사례는
  야추류 DP·확률 테이블을 10MiB `data.bin`에 압축해 적극 활용했고,
  단순 휴리스틱보다 강했다는 회고가 있다. 2026 현재 `145/150` 계열에는
  `data.bin` 읽기 코드가 없고, 저장소의 `tools/build_data_bin.py`는 과거
  26~28 계열의 map-profile JSON용이라 바로 150에 붙일 수 없다. 지금
  제출 직전에는 `data.bin` 이식보다 150 유지가 안전하다.
- **기각/보류:** `146.py`의 early HQ L2 hold는 rush proxy no-op.
  `147.py`의 넓은 delayed mass brake는 rush를 크게 개선했지만 proxy-punch
  seed63 left를 승리에서 패배로 바꿔 과범위. `148/149.py`는 더 좁힌
  중간 후보이며, 150이 같은 proxy 안전성과 더 많은 eval29 분기를 보여
  우선 후보가 됐다.

## 이전 작업 메모 (2026-07-08 14:50 KST, 145 제출 결과 반영)

- **공식 제출 결과:** `bots/145.py` 제출 후 받은 `bots/145_nypc_log`는 8승0패.
  1~6번은 HQ 파괴 승(`T140`, `T159`, `T195`, `T188`, `T185`, `T164`),
  7~8번은 턴제한 승. max turn time은 15ms.
- **재현성:** `python3 tools/run_log_replay.py bots/145_nypc_log --candidate
  bots/145.py --replay-side right --name 145-vs-145log-replay-right --timeout 60`
  결과 `8W/0L/0D`, replay-WA 0. 서버 로그와 현재 소스가 완전히 일치한다.
- **판정:** 145는 공식 8봇 기준에서도 143/144의 개선을 유지한 안정 제출이다.
  7번은 T200에 내 HQ L5 30HP, 상대 HQ L1 10HP/기지 0개, 8번은 내 HQ L5
  30HP, 상대 HQ L4 25HP라 턴제한 판정도 명확한 우위다. 다음 작업은
  중간평가 유저 결과 로그가 들어온 뒤 그 손실/무승부만 좁게 공략한다.
- **유저 로그 인덱스:** 과거 eval14/25/26/28의 80경기를 상대 티어, 우리
  제출봇, 당시 결과, `145.py` replay 결과, 원본 로그 경로로 매칭했다.
  당시 산출물은 `results/user-log-match-index.tsv`, 생성 스크립트는
  `tools/build_user_log_index.py`였다. 공개 요약은 현재 루트 `README.md`와
  `docs/183-user-log-analysis.md`에 남긴다.
  현재 145 replay 기준 남은 non-win은 eval26 `thomas` 한 경기
  (`215364_A`, Tier 9, `DRAW TURN_LIMIT`)뿐이다.
- **공식 로그 커버리지:** `30/45/60/61/62/76/77/78/91/125/143/145_nypc_log`
  전체 97게임을 `145.py`로 오른쪽 고정 재생했다. 원본 공식 로그는
  `87W/5L/5D`였지만 145 replay는 `97W/0L/0D`. 특히 원본 non-win 10개
  (`30`의 4/5/6/8, `45`의 6, `60`의 6, `76`의 3, `78`의 `211083`,
  `125`의 8, `143`의 8)이 전부 승 분기로 바뀐다. 자세한 표는
  `docs/official-log-coverage.md`.
- **대기 중 실험 계획:** 당시 사전 가설은 ①proxy-rush의 T80~110 HQ패
  방어 공백, ②`215364_A`의 종반 우위 미전환 두 가지다. 새 실험은 실제
  중간평가 non-win이 이 패턴 중 하나와 맞을 때만 시작한다.

## 이전 작업 메모 (2026-07-08 14:40-14:50 KST)

- **후보 `bots/145.py` = 144 + 기지 붕괴 중 안전 재건 reserve 우회.**
  `eval25`의 `204345_A`가 144에서도 T189 HQ패로 남아 있었다. 원인은 과거
  125에서 검증했던 패치가 현재 계열에 빠져 있었기 때문이다. 145는 미지맵,
  T45+, 내 기지 1개 이하, 후보 거점 2홉 내 적 없음일 때만 L1 기지 재건을
  `reserve` 패딩 없이 300골드 즉시구매로 허용한다.
- **검증:** `py_compile` 통과, 제출 누수 스캔 통과. `204345_A`는 T189
  HQ패에서 T146 replay-WA 승 분기로 전환. `eval25`는 A-side `12W/0L`,
  B-side `8W/0L`; `eval26`은 A-side `16W/0L/1D`, B-side `3W/0L`;
  `eval28`은 A/B 모두 `10W/0L`; `eval14`는 A-side `18W/0L`, B-side
  `2W/0L`; `143_nypc_log` 오른쪽 고정 재생 `8W/0L` 유지(WA 1).
- **로컬 대전:** sample16 `16W/0L/0D WA0`. 4프록시 seed1/41/81은 144와
  동일(`66/1/13`, `79/0/1`, `62/18/0`, `80/0/0`; `67/2/11`, `76/0/4`,
  `66/14/0`, `80/0/0`; `68/3/9`, `79/0/1`, `56/24/0`, `80/0/0`).
  77/90 직접대결 seed1/41/81도 144와 동일(`4/0/76`, `6/1/73`,
  `10/8/62`; 90은 seed81 `10/6/64`). 144 직접대결 seed1은 미러 수준
  `2/2/76`. 공식 `nation-providing/testing-tool.py` seed42 샘플 AI 양쪽
  스모크도 HQ 파괴 승리. max turn time 16ms.
- **판정:** 145가 현재 제출 후보. 144의 eval26 개선과 로컬 무회귀를 유지한
  채 eval25의 남은 실제 패배를 제거한다. 중간평가 시간이 가까우므로 추가
  실험보다 145 제출을 우선한다.

## 이전 작업 메모 (2026-07-08 14:20-14:40 KST)

- **후보 `bots/144.py` = 143 + T120 이후 병력열세 중 견제부대 분산 차단.**
  `eval26`의 `215758_A`는 T130 전후 상대 병력이 10기 이상 많아졌는데도
  최대 7기 견제부대가 전방에 흩어져 본부 방어가 무너졌다. 144는 미지맵
  견제부대 선발 조건에 `outmassed and turn >= 120` 차단을 한 줄 추가했다.
  조건은 기존 `outmassed` 정의상 T120~139, 적 병력 >= 내 병력 +5일 때만
  켜진다.
- **검증:** `py_compile` 통과, 제출 누수 스캔 통과. `eval26` 고정 재생은
  A-side가 `15W/1L/1D`에서 `16W/0L/1D`로 개선(`215758_A`: T155 HQ패 ->
  T130 replay-WA 승 분기), B-side는 `3W/0L` 유지. `eval28` 고정 재생은
  A/B 모두 `10W/0L` 유지, `143_nypc_log` 오른쪽 고정 재생도 `8W/0L`
  유지(WA 1). sample16 `16W/0L/0D WA0`.
- **로컬 대전:** 4프록시 seed1/41은 143과 완전 동일
  (`66/1/13`, `79/0/1`, `62/18/0`, `80/0/0`; `67/2/11`, `76/0/4`,
  `66/14/0`, `80/0/0`). seed81은 econ만 `68/6/6 -> 68/3/9`로 손실이
  무승부로 바뀌고 나머지는 동일. 77/90 직접대결 seed1/41/81은 143과 동일
  (`4/0/76`, `6/1/73`, `10/8/62`; 90은 seed81 `10/6/64`). 143 직접대결
  seed1/41은 미러 수준(`2/2/76`, `2/2/76`). max turn time 15ms.
- **기각:** 145/146은 남은 `215364_A` 무승부를 깨려고 T190+ 관문 release를
  앞당겼지만 승리 전환이 없었고, 146은 종반 병력 보존만 나빠져 삭제했다.
- **판정:** 144가 현재 최신 제출 후보. 143의 안전 검증을 유지하면서
  eval26의 마지막 실제 패배 replay를 승 분기로 바꾼다. 남은 `215364_A`
  무승부는 좁은 개선 근거가 없어 건드리지 않는다.

## 이전 작업 메모 (2026-07-08 13:50-14:20 KST)

- **후보 `bots/143.py` = 142 + 초중반 병력열세/압박 중 기지 레벨업 차단.**
  과거 108 후보의 안전 패치를 현재 142에 단일 이식했다. 조건은 T100 전,
  적 병력 >= 내 병력 +4, 공세/압박 중, HQ 목표 미달, HQ 업그레이드 가능,
  그리고 `hq_race`/`hq_score_race`/`_hq_stuck`/`need_train_cap`이 아닐 때만
  하위 기지 레벨업을 미룬다. 의도는 HQ L3 캐치업 자금을 기지 L2/L3가 먼저
  먹는 초중반 병력열세 패턴을 막는 것이다.
- **검증:** `py_compile` 통과, sample16 `16W/0L/0D WA0`. `143_nypc_log`
  오른쪽 고정 재생 8승0패(WA 1). `eval28` 고정 재생은 142와 동일하게
  A-side `10W/0L`, B-side `10W/0L`. `eval26` 고정 재생은 B-side가
  `2W/1L`에서 `3W/0L`로 개선(`212177_B`: T106 HQ패 -> T82 replay-WA
  승 분기), A-side는 142와 동일. 4프록시 seed1/41 640게임은 142와 승패
  완전 동일. 77/90 직접대결 seed1/41은 142와 동일. 142 직접대결 seed1/41은
  미러 수준(`2/2/76`, `2/2/76`). 추가 seed81 확인에서도 142와 완전 동일:
  4프록시(`econ 68/6/6`, `turtle 79/0/1`, `rush 56/24/0`, `punch 80/0/0`),
  77 직접대결 `10/8/62`, 90 직접대결 `10/6/64`, 142 직접대결 `2/2/76`.
  제출 누수 스캔 통과, max turn time 18ms.
- **판정:** 143이 현재 최신 제출 후보. 142의 eval28 전승 replay 분기를
  유지하면서 eval26의 남은 RIGHT 손실 1건을 추가로 건드린다. replay-WA는
  확정 승리 증거가 아니므로 서버/유저 중간평가로 최종 확인해야 한다.

- **후보 `bots/142.py` = 139 + RIGHT 동률 HQ race의 확정 경제우위 저축 보강.**
  `eval28`의 `233143_B`는 RIGHT가 후반 기지 13개 vs 5~6개, 병력 우위까지
  확보했지만 HQ L3 동률로 끝나 무승부였다. 140/141 탐색 결과, HQ race
  전체나 이른 경제우위까지 넓히면 프록시 회귀가 생겼다. 142는 `self.flip`
  상태에서 `hq_score_race`는 139처럼 막고, 추가로 T160+ `hq_race`,
  내 기지 >= 상대 기지 +4, 내 병력 >= 상대 병력일 때만 저축 중 1기/턴 훈련
  예외를 끈다.
- **검증:** `py_compile` 통과, sample16 `16W/0L/0D WA0`. `143_nypc_log`
  오른쪽 고정 재생 8승0패(WA 1). `eval28` 고정 재생은 A-side `10W/0L`,
  B-side `10W/0L`까지 개선(`233143_B`: 무승부 -> T200 턴제한 승,
  `232307_B`/`234056_B` 개선 유지). `eval26` 고정 재생은 139와 동일.
  4프록시 seed1/41 640게임은 139와 승패 완전 동일. 77/90 직접대결
  seed1은 139 대비 `3/0/77 -> 4/0/76`, seed41은 동일(`6/1/73`).
  139 직접대결 seed1/41은 미러 수준(`2/1/77`, `2/2/76`). 제출 누수 스캔
  통과, max turn time 20ms 이하.
- **기각:** 140은 같은 타깃을 바꿨지만 프록시에서 승리 3개가 무승부로
  내려갔다. 141은 프록시 seed1 econ에서 패배가 1개 늘어 기각.
- **판정:** 142가 현재 최신 제출 후보. `eval28` replay 기준으로 20게임 전부
  승리 분기까지 올라간 후보지만, replay-WA는 확정 승리 증거가 아니므로
  서버/유저 중간평가로 최종 확인해야 한다.

- **후보 `bots/139.py` = 136 + RIGHT HQ 점수 레이스 중 trickle train 차단.**
  `eval28`의 `232307_B`는 RIGHT가 기지/병력 경제에서 앞서지만 LEFT HQ가
  L4가 된 뒤에도 RIGHT가 HQ L3에 머물러 턴제한 HP 판정으로 졌다. 원인 확인:
  HQ L4 저축(`saving_for=2400`)은 켜졌지만, 고수입이면 저축 중에도
  1기/턴 훈련하는 예외가 계속 발동해 L4 비용을 못 모았다. 139는 RIGHT
  내부 시점(`self.flip`)이고 `hq_score_race`일 때만 이 예외를 끈다.
- **검증:** `py_compile` 통과, sample16 `16W/0L/0D WA0`. `143_nypc_log`
  오른쪽 고정 재생은 136과 동일한 8승0패(WA 1). `eval28` 고정 재생은
  A-side `10W/0L`, B-side가 136의 `8W/1L/1D`에서 `9W/0L/1D`로 개선
  (`232307_B`: T200 패 -> T133 replay-WA 승 분기, `234056_B` 개선 유지).
  `eval26` 고정 재생은 136과 동일. 4프록시 seed1/41 640게임은 136 기준과
  동일하거나 소폭 개선(seed41 econ `67/3/10 -> 67/2/11`). 77/90/136
  직접대결 seed1/41은 기준과 동일. 제출 누수 스캔 통과.
- **기각:** 137은 HQ race 전체에서 trickle train을 꺼 `232307_B`를 실제
  턴제한 승으로 바꿨지만 136 직접대결에서 대회귀(seed1 `3W/31L/46D`,
  seed41 `15W/23L/42D`). 138은 side 제한 없이 `hq_score_race`에 적용해
  직접대결은 안전했지만 `143_nypc_log` 5번이 승리에서 무승부로 내려가 기각.
- **판정:** 139가 현재 최신 제출 후보. 개선은 replay-WA 신호라 서버/유저
  중간평가로 최종 확인해야 한다.

- **후보 `bots/136.py` = 135 + 경제 붕괴 중 빈사 HQ 마무리.** `eval28`의
  `234056_B`에서 RIGHT가 기지 0개로 무너졌지만 LEFT HQ를 4HP까지 깎고도
  병력을 재투입하지 못해 T195 HQ패가 났다. 136은 `unknown_map`, T70+,
  내 기지 0개, 적 HQ HP 5 이하, 내 HQ 1홉 적 압박 0, 아군 3기 이상일 때만
  `collapse_finish`를 켜서 HQ 직행/웨이브 release/관문 대기를 해제한다.
- **검증:** `py_compile` 통과, sample16 `16W/0L/0D WA0`. `143_nypc_log`
  오른쪽 고정 재생은 135와 동일하게 8승0패(WA 1). `eval28` 고정 재생은
  A-side `10W/0L`, B-side가 135의 `7W/2L/1D`에서 `8W/1L/1D`로 개선
  (`234056_B`: T195 HQ패 -> T189 replay-WA 승 분기). `eval26` 고정 재생은
  135와 동일. 4프록시 seed1/41 640게임 및 77/90/135 직접대결 seed1/41은
  135 기준과 완전 동일. 제출 누수 스캔도 통과.
- **판정:** 실전 유저 로그 1건을 추가로 건드리는 좁은 후보. replay-WA는
  확정 승리 증거가 아니므로 서버/유저 중간평가로 최종 확인해야 한다.

## Source: former `docs/workflow.md`

> 통합 대상 원문: 작업 워크플로우. 아래 내용은 원본을 그대로 포함한다.

# NYPC 작업 워크플로우 (v3, 2026-07-03 밤 개정)

## 한 줄 요약

**서버 A/B가 유일한 검증. 알려진 8맵은 커맨드 동일성으로 보호. 유저전
개선은 전부 미지맵 게이트 뒤에.**

## v3 추가분 (v2 위에 얹음)

1. **결정론 보호 (커맨드 동일성 표준)**: 알려진 8맵의 성적은 "같은 코드
   경로 = 같은 게임"으로 보장된다. 모든 변경 후 재현 맵(맵4=29세대,
   맵7=30세대)과 성적 확정 맵의 리플레이를 돌려 **200턴 전체 LEFT 커맨드
   diff가 0**임을 확인한다. 결과만 같은 것은 요행이다 (46 전역 타이브레이크
   시도: 맵4가 T15에 발산했지만 결과는 우연히 같았음).
2. **미지맵 게이팅**: 유저전(랭킹) 개선은 전부 `self.unknown_map` 게이트
   뒤에 넣는다. 샘플 성적을 바이트 단위로 보존하면서 랭킹 게임만 진화시키는
   구조. 현재 게이트 뒤: 올인 가드, chip 기본, T100 거북이->parity 분류,
   hq_race 예외, 호위 확장, 대칭 타이브레이크.
3. **유저 중간평가 루프 (6시간 주기)**: 로그를
   `bots/eval##_bot<n>_user_log/`에 저장한다. `ranking_raw.txt`는
   레이팅/티어의 유일한 소스다. 분석
   순서: ① 진영별 승패 (RIGHT 편향 추적) ② 티어별 승패 (T5 업셋 패배가
   최대 레이팅 손실원) ③ 패배 게임 성장 커브 비교 (T50/100/150 시점
   기지/HQ/훈련) ④ 크래시/급사 스캔.
4. **맵 프로필(`MAP_PROFILES`)은 상호 간섭 불가** -> 여러 맵 실험을 한
   제출에 병렬 A/B로 실을 수 있다.

## 왜 v2인가

29~32 네 번의 제출로 확인된 사실: 로컬 게이트(프록시 풀 무패, 형제 스파링
압살, 리플레이 교란)와 서버 성적의 상관이 사라졌고, 마지막 두 사이클은
역상관이었다 (30: 4승3패1무 → 31: 3승1무4패 → 32: 2승6패).

- 정적 프록시는 적응형 서버 봇(5~8번)의 반응을 모사하지 못한다.
- 형제 스파링은 자기 계보의 약점 겨냥 능력만 잰다.
- 리플레이 WA 교란은 "게임이 달라졌다"이지 "이긴다"가 아니다.
- 행동 스위치가 쌓이면 상호작용 회귀가 매 사이클 터진다
  (기지 보초가 3번 원펀치 방어를 해체한 사례).
- 버그 수정조차 다른 버그와 상쇄 관계일 수 있다 (그림자 저축 픽스가
  "훈련을 지켜주던 낮은 댐"을 제거해 7번전 병력 동결을 유발한 사례).

## 개발 루프

```text
서버 로그 분석 -> 패인의 인과 가설 -> 한 가지 변경 -> 로컬 안전망 통과
-> 제출 -> 로그로 가설 검증 -> 승격 또는 롤백
```

1. 변경은 후보 번호를 올려서 만든다 (`bots/<n+1>.py = 서버 최고 성적 봇 + 변경 1개`).
2. 로컬 안전망 (이것만 돌린다):

```bash
CANDIDATE=bots/<n>.py
python3 -m py_compile "$CANDIDATE" tools/*.py
# 샘플 스모크: WA 0 + 10승 확인 (서버 1~2번 봇 안전망)
python3 tools/evaluate_pool.py --bot "$CANDIDATE" --start 1 --count 5 \
  --side both --pools sample --name <n>-sample-smoke
# 베이스 봇과 스파링: 변경이 켜지는지 + 큰 퇴행 없는지 (동률이어도 무방)
python3 tools/evaluate.py --bot "$CANDIDATE" \
  --opponent "python3 $PWD/bots/<base>.py" \
  --left-opponent "python3 $PWD/bots/<base>.py" \
  --side both --start 1 --count 10 --timeout 300 --name <n>-vs-<base> --quiet
```

3. 턴 시간을 확인한다 (`results.csv`의 max ms, 100ms 제한 — 32에서 49ms까지
   상승한 적 있음).
4. 제출하고 로그를 `bots/<n>_nypc_log/`로 저장, 파일명 `1.txt`~`8.txt` 정규화.
5. `tools/analyze_server_logs.py`와 `tools/log_timeline.py`로 변경의 가설이
   맞았는지 게임 단위로 확인한다. **8게임은 각각 결정적 매치업이라 승패
   집계보다 "어느 게임이 왜 플립됐나"가 A/B의 실제 판독값이다.**
6. 결론을 `strategy-plan.md`의 A/B 큐 섹션에 누적한다.

## 대표 답안 규칙

랭킹은 대표 답안 기준이다. **대표 답안은 항상 서버 성적 최고 봇으로 유지**
(현재 49.py 제출됨 / 후보 50.py — 공성 고정 버그 수정판). 레이팅 궤적:
#14 1750 → #15 1780 → #17 1990(T9) → #18 1910 → #19/20 1820(T7).

## 변경 설계 원칙

- 순수 버그픽스 > 파라미터 조정 > 행동 스위치. 새 스위치는 켜는 조건과
  꺼지는 조건, 기존 승리 시나리오와의 상호작용을 주석에 명시한다.
- 서버 로그에 근거 없는 변경은 만들지 않는다 (로컬에서만 보이는 개선은
  프록시 메타 과적합일 가능성이 높다).
- 이미 서버에서 검증된 픽스(예: 종반 보급 펀드 — 30의 굶주림 183회를 0으로)
  는 재검증 없이 이식 가능하다.

## 로그 정책 (v3.2, 경량화 -- 마감 이틀 전 기준)

전 로그는 `bots/logs_backup_*.tar.gz`에 백업됨. 원본은 운영
필수분만 유지: 게이트용 `29_nypc_log/4.txt`·`30_nypc_log/7.txt`·
`45_nypc_log/`. 새 평가 로그는 분석 후 백업 갱신하면 원본 삭제 가능.

## (구) 로그 보호 규칙 (v3.1, 유실 사고 후 신설)

**사고 기록 (2026-07-06)**: 평가 #15 유저 로그 폴더(43_user_log, 20게임)가
정리 작업 중 유실됨 (분석 결론은 문서에 보존, 원본은 복구 불가). 재발 방지:

1. **정리 스크립트는 화이트리스트 방식만**: 삭제/이동할 파일명을 명시적으로
   나열한다. 글롭/디렉터리 순회로 지우지 않는다.
2. `*_nypc_log/`, `*_user_log/`는 어떤 스크립트도 건드리지 않는다 (읽기 전용).
3. **주기 백업**: 로그 폴더 전체를 `bots/logs_backup_<날짜>.tar.gz`로
   압축 보관 (평가 데이터 추가 시마다). 현재: logs_backup_0706_0021.tar.gz.
4. 유저 로그 저장 규약: 폴더 `bots/eval##_bot<봇번호>_user_log/`, 파일명
   `<대전ID>_<A|B>.txt` (A=우리 LEFT), `summary.md`와 `ranking_raw.txt` 필수 포함.

## 검증 관행 (v3.1): 제출 전 이중 감사

큰 변경 묶음은 깨끗한 세션의 서브에이전트 2종으로 감사한다 (7/5~6 실증:
40여 제출 내내 잠복한 공성 고정 버그를 행동 감사가 발견):

- **적대 코드 감사**: 신규 코드의 룰 위반/게이트 누수/기능 상호작용을 코드
  인용 강제로 사냥. "코드가 맞는가."
- **행동 정량 감사**: 실게임 10판+에서 유휴 골드/유휴 병력/왕복 이동/공성
  공백을 게임당 수치로 계측. "행동이 알뜰한가." 둘은 별개의 감사다.

## 파일 정책

```text
bots/<best>.py          # 서버 최고 성적 봇 = 대표 답안 (삭제 금지)
bots/<candidate>.py     # 현재 후보 (제출 중 + 준비 중, 1~2개)
bots/<n>_nypc_log/      # 서버 로그 = 유일한 실측 데이터, 전부 보존
eval##_bot*_user_log/   # 유저 평가 로그와 표준 summary
results/                # 일회용. 현재 사이클 것만 남기고 주기적으로 비운다
opponents/proxy.py      # 참고용 유지 (스모크/실험에 씀, 게이트 아님)
```

- 서버 로그는 어떤 정리에서도 지우지 않는다. 코드에 대한 결론은 바뀌어도
  로그는 다시 못 얻는다 (같은 봇을 재제출하면 얻을 수는 있지만 제출 슬롯
  낭비다).
- `results/`가 커지면 (수백 MB) 현재 사이클 폴더만 남기고 삭제한다.
  결론은 항상 `strategy-plan.md`에 먼저 적는다.
- 후보 코드를 고치면 그 후보의 로컬 실험 결과는 무효 — 폴더를 지우고 다시
  돌린다.

## 제출/채점 요약

- 제출: 코드 1개(≤1MiB) + 선택 바이너리 1개(≤10MiB, 런타임 `data.bin`).
  현재 후보들은 `data.bin` 불필요.
- 제출 즉시 고정 8맵에서 샘플 AI 8개와 대결한 로그를 받는다. 같은 코드는
  같은 결과 (결정적).
- 예선 마감: **2026-07-08 22:00 KST**. 최소 상위 20팀 진출.
- 채점 환경: AWS c7a.2xlarge, Ubuntu 24.04, 턴당 100ms + 초읽기 5개.
- 제출 코드의 외부 API/네트워크 호출 금지.

## 분석 도구

```bash
python3 tools/analyze_server_logs.py bots/<n>_nypc_log   # 매크로 지표 표
python3 tools/log_timeline.py <log> --every 40           # 턴별 상태 추이
python3 tools/run_log_replay.py <log> --replay-side right --candidate <bot>
    # 기록된 상대 커맨드로 재대결. WA 교란 = 참고 신호일 뿐, 승리 보장 아님
python3 tools/extract_log_features.py bots/<n>_nypc_log  # feature 추출
```

`log_timeline.py` 주의: 결과 블록의 `TRAIN A4 B4`처럼 여러 ID가 한 줄에
오는 형식을 과거에 누락했던 적 있다 (수정됨). 수치가 직관과 어긋나면
도구 버그부터 의심한다.

## Source: former `strategy-plan.md`

> 통합 대상 원문: 전략 계획. 아래 내용은 원본을 그대로 포함한다.

# NYPC Strategy Plan

## User-Match Intermediate Eval #14 (2026-07-03 15:00, bot submitted 14:53)

Logs in `bots/????_user_log/` (20 identified games): **9W 8L 3D vs real users.**

Loss patterns:
1. **17-turn all-in rush death** ('어 나혼자야'): opponent trained 3 extra by
   T3 and sent all 5 at our HQ; our T2 base build (300g) had spent the
   defense budget (3 defenders vs 5). ALL generations 37-42 die identically.
   -> 43's all-in guard (unknown-map only: enemy total >= 5 by T8 -> halt
   base builds, train everything). Replay: 17-turn death -> t169 WIN.
2. Out-macro'd by high-tier users (6 of 8 losses: trains 21v92, 31v69...).
   Engine ceiling; the raid/tiebreak work targets this class.
3. One tiebreak loss DESPITE out-training (105v67) -- endgame HP race.

43 also carries the raid profiles for maps 6/8 (opponent's late upgrades are
funded by their outer economy; raiding it breaks the tiebreak parity).
Integrity: map4=29 / map7=30 command equality re-verified, sample 10W WA 0,
17ms.

## Current State

The latest two real server submissions are:

```text
bots/24.py
bots/25.py
```

## A/B Submission Queue (methodology v2, 2026-07-03)

One change per submission; server result vs 30's 4W3L1D baseline decides
whether the change stays. Both queued fixes are server-evidenced, not
speculative:

```text
[verdict]   33 = 30 + expansion-savings shadow fix -> 3W 1D 4L.
            Exactly 30's result with bot 7 flipped W->L. Root cause found:
            the 300-gold shadow was a LOW dam that accidentally kept training
            flowing; the fix let HQ-tech saving (a 1200-3600 HIGH dam) freeze
            the army at 10 while adaptive bot 7 grew to 36. The underlying
            flaw is "saving while outnumbered", not the shadow fix itself.
[verdict]   34 = 33 + supply fund + GLOBAL train-to-parity -> 2W 1D 5L, rejected.
            But the per-game reading was gold: parity SAVED map 5 (survived
            to turn limit at 91v99 alive) and DREW map 6, while KILLING maps
            3/8 (tech starvation, HQ L1, dead at t80 on 3). Parity is a
            per-map shape, not a global rule.
[verdict]   35 = map profiles v1 -> 3W 1D 4L. Profile MECHANISM proven:
            map6 flipped L->D exactly as replayed. But hq_rush starved the
            army (map8 D->L) and war_econ failed to reproduce 30's map7 win.
[verdict]   36 -> 4W 2D 2L (wins 1,2,3,7 / draws 6,8 / losses 4,5).
            PREDICTION EXACT, game by game. New best; representative moved
            to 36. Map4 upgraded to a turn-limit L5v5 loss (was HQ death).
[verdict]   37 -> 4W 3D 1L, new best. BOT 5 KILLED for the first time ever
            (HQ destroyed t182; commit-push + sticky target + map5 parity).
            Map4 L->D as predicted, map3 faster (t156). Costs: map6 D->L
            (opponent reached L2 late), map7 W->D (commit-push broke the
            30-reproduction, which depended on the old retreat toggle).
[verdict]   38 -> 4W 4D 0L. FIRST ZERO-LOSS RESULT. Map6 L->D restored;
            map7 stayed D (live bot 7 adapts past the recorded reproduction
            -- replay's limit reconfirmed). Representative -> 38.
[verdict]   39 -> 4W 4D 0L (same as 38). Map8 attempt NEUTRALIZED: we
            reached L5, adaptive bot 8 followed to L5 (was L4v4), 30-30
            again, and we ended 24v35 behind. Bot 8 mirrors any static
            shape; its map is structurally a draw ceiling. Maps 4/6/7
            similar (superior adaptive armies). Sample plateau reached.
[ready]     42 = 41 + tiebreak exploits for the last two draws:
            - map6: opponent's HQ upgrade is a FIXED SCHEDULE (t197 across
              3 submissions regardless of our level). hq_rush t150 without
              parity (33-army upkeep was eating all tech gold) reaches L4
              by t181 vs their L2\@197. Replay trajectory confirms.
            - map8: opponent mirrors our HQ level with 20-33 turn lag.
              hq_delay_last=182 postpones our L5 purchase so the earliest
              reaction lands at t202+ (out of game). Worst case = current
              draw (no downside).
            Reproduction integrity: map7=30 and map4=29 command equality
            re-verified after edits. Sample 10W WA 0.
            Projected 8W 0L 0D possible; conservative 6W 2D 0L floor.
[old]       41 = 40 + DETERMINISTIC WIN REPRODUCTION. The game is
            deterministic, so any historically-won live game is a
            guaranteed win if we reproduce that bot's behavior exactly:
            - map7 = 30's engine (shadow, old_retreat, no_fund, no_sticky,
              deep_recall): 200-turn command diff vs 30's winning log =
              IDENTICAL. Win guaranteed.
            - map4 = 29's engine (gen29 flag reverts under_pressure,
              illegal-save skip, intercept condition + the flags above):
              200-turn command diff vs 29's winning log = IDENTICAL.
              Win guaranteed (t190 HQ kill).
            Preservation: maps 1/3/5/6/8 replay identical to 39, sample
            10W WA 0, 17ms. Verification standard upgraded from result-
            match to FULL-GAME COMMAND EQUALITY.
            Projected 6W 2D 0L -- realistic maximum (6/8 never beaten live).
[old]       40 = 39 + unknown-map runtime adaptation. Participant matches
            are played on unknown maps where NO map profile fires -- ranking
            games run the bare default engine. On unknown maps only (known
            8 hashes excluded -> sample score 100% preserved, verified by
            full-length identical replays): chip=True by default, and a
            turn-100 classifier (no invasion + outnumbered = turtle/growth
            opponent) switches on parity. Local A/B on random maps:
            proxy-econ 4W->5W (0 losses), turtle unchanged. 26ms.
[old]       38 = 37 + map6 {+hq_rush t165} (level-follow for the tiebreak)
            + map7 {+old_retreat} (completes the literal 30 reproduction).
            Both map-scoped; map5 win replays TURN-BY-TURN identical.
            Replays: map7 WIN restored, map6 L->D, map4 D kept, map5 WIN
            kept, sample 10W WA 0, 26ms. Projected 5W 3D 0L -- first
            zero-loss projection.
[old]       37 = 36 + profiles v3 + commit-push engine fixes.
            Profiles: map4 chip+no_push (we led 50v27 at T150, pushed, lost
            everything to their fortress; hold the lead, force 30-30, chip
            with numbers), map5 parity (34's survival shape).
            Engine (from the game-4 bottleneck audit):
            - commit push: retreat only on home invasion; the alive<enemy-5
              toggle caused attack/retreat flapping (T170-174: 38 attack +
              42 staging moves simultaneously)
            - sticky wave target: hold target until destroyed (siege gaps of
              6-8 turns let half-dead bases stand)
            - no deep recall: units in the enemy half never get recall orders
              (T185: 52 recall orders marched 30+ units home through the
              enemy army -> annihilated)
            Gates: map4 replay L->DRAW, map3 WIN t156 (faster), map7 WIN
            preserved, map6 DRAW, map5/8 diverged (WA t181/t168 -- the
            engine change is this submission's experiment). Sample 10W WA 0,
            27ms. Projected 4W 3D 1L.
[old]       36 = 33 + supply fund + profiles v2:
            map6 parity (server-proven), map7 shadow+no_fund (= literal
            revert of the shadow fix on that map; replay reproduces 30's
            win TURN-BY-TURN), maps 4/5/8 back to default engine.
            Replay suite: map3 W(166) map6 D map7 W map8 D, all clean,
            sample 10W WA 0, 27ms. Projected 4W 2D 2L (beats 30's 4W3L1D).
            NOTE: a silent edit-script failure (assert aborted before write)
            cost one debugging round -- always verify file state after
            scripted edits.
[old]       35-note: MAP_PROFILES keyed by map hash
            (verified stable across all 5 submissions). Overrides only on
            losing maps: 4/8 hq_rush(t60), 5 parity+hq_rush(t140), 6 parity,
            7 war_econ+hq_cap2 (30's winning shape). Maps 1/2/3 untouched.
            Replays vs 34's recordings: map3 WIN t197 clean, map8 WIN
            turn-limit clean (tiebreak flipped), map6 DRAW clean, map5/7
            disrupted early, map4 still loss. Sample smoke 10W WA 0,
            vs 33 2W2L16D (default behavior preserved), max 26ms.
[ideas]     HQ-race exception (turn-limit losses are HQ-level tiebreaks),
            paid-move waste (1.4k-2.3k gold vs bots 4/5 = 12-19 warriors),
            49ms proximity-scan optimization
```

A/B reading note: the 8 server games are deterministic matchups, so the real
verdict of a submission is WHICH game flipped and WHY, not the aggregate
score.

Representative answer on the server should stay on the best-scoring bot
(currently 30) until a challenger beats 4W 3L 1D.

## 32.py Server Result (2026-07-03)

```text
2W 6L -- worst so far; triggered the methodology revision above.
Base sentries dispersed home defense; bot 3's punch killed us at turn 106.
```

## 31.py Server Result (2026-07-03, logs in bots/31_nypc_log/)

```text
3W 1D 4L: wins 1, 2, 3 -- draw 4 -- losses 5, 6, 7, 8
Bot 4 (fast economy) improved to a DRAW; bot 3 stayed a win via turn-limit.
Bots 7 and 8 regressed: the war economy overreacts to PERSISTENT light
harassment, freezing HQ tech. All three turn-limit losses were HQ-LEVEL
tiebreaks (L3v4, L4v5, L3v4).
```

Failure anatomy:

- Bot 7: two roving harassers vetoed every expansion claim; 2 bases and total
  passivity for 160 turns despite army parity (10 vs 9).
- Bot 8: two raiders demolished bases one by one (worker+turret loses 1v2);
  49 field-combat deaths from one-by-one interception feeding; economy hit
  zero bases by turn 160.

## 32.py (candidate, gates passed 2026-07-03)

1. Group interception: respond to invaders only when free responders
   outnumber them (no more trickle-feeding 1v3 fights).
2. Escorted expansion: if no claimable stronghold exists, fewer than 4 bases,
   and only light harassment, send the group to clear the nearest contested
   stronghold, which reopens claims (breaks the bot-7 deadlock).
3. HQ race exception: from turn 110, if the enemy HQ level >= ours and no
   full invasion, HQ savings are allowed and protected from training even
   under pressure (the tiebreak is ultimately an HQ-level race).
4. Base sentries: bases with enemies within 4 hops hold work-cap+1 warriors;
   sentry + worker + turret self-defeats small raids (bot-8 fix). This broke
   the bot-8 collapse trajectory in replay (identical through 200 before,
   diverges at 114 now).

Gate results:

```text
pool 40 games: econ 5W 0L 15D, turtle 10W 0L 10D, rush 20W, punch 20W -- zero losses
sample 10W 0L, WA 0 everywhere
vs 30: 10W 2L 8D    vs 31: 2W 3L 15D (noise-range; sentries pay off only vs harassers)
replays: bot7 disrupted t195, bot8 collapse broken t114; bot5/6 unchanged (next targets)
```

## 30.py Server Result (2026-07-02, logs in bots/30_nypc_log/)

```text
4W 3L 1D: wins 1, 2, 3, 7 -- losses 4, 5, 6 -- draw 8
Bot 3 flipped back to a WIN (war-economy fix, as the replay predicted).
Bot 7 flipped to a WIN (illegal-upgrade-saving fix).
Bot 8 improved to a DRAW; bot 6 lost on HQ-level tiebreak (L3 vs L4).
Bot 4 regressed to a narrow loss (74 vs 80 alive at turn 192 -- coin-flip range).
```

## 31.py (candidate, gates passed 2026-07-02)

Fixes, each tied to a measured failure:

1. `outmassed` requires enemy_bases < my_bases: growth bots (server 6) that are
   ahead in BOTH army and economy must be out-grown, not hunkered against.
   Scout-level presence (1-2 near HQ) no longer flips war economy.
2. Interception targets invaders in MY half only near my buildings: kills the
   2-raider worker-slaughter treadmill without chasing frontier stacks.
3. Raid mode (turn 120+, no invasion, 2 waves ready, HQ L3+): eat the outer
   economy of home-stack turtles instead of waiting for an advantage that
   never comes.
4. Endgame chip (turn 180+): if losing the HQ-HP tiebreak, always attack;
   if tied, attack only with +4 alive. Turn 188+ base workers join (bases
   score nothing).
5. Expansion-savings shadow fix (THE big one): saving 300 for a stronghold
   that is not actually claimable (contested center) sat first in the queue
   and blocked HQ tech forever -- both 29 and 30 spend entire games at HQ L1
   on contested-center maps. Now we save only while a claim is live.
6. Endgame supply fund: training cannot eat the remaining upkeep budget
   (observed: 106 hunger events after a turn-175 push drained gold).

Gate results:

```text
vs 29: 16W 0L 4D      vs 30: 12W 2L 6D     (30 vs siblings was all draws)
proxy-econ 3W 0L 17D  proxy-turtle 13W 0L 7D  (both zero losses; 30 had 4L each)
proxy-rush 20W        proxy-punch 19W 1L      sample 10W, WA 0 everywhere
replays: bot3 WIN, bot6 DRAW, bot8 WIN, bot4/5 disrupted (WA)
max 2ms/turn, 29KB source, no data.bin
```

## 29.py Server Result (2026-07-02, logs in bots/29_nypc_log/)

```text
3W 5L: wins 1, 2, 4 -- losses 3, 5, 6, 7, 8
Bot 4 (fast economy) flipped to a WIN as the proxy pool predicted.
Bot 3 (basic aggressive) flipped to a LOSS at turn 79.
```

Diagnosis from logs:

- Bot 3 plays "bunker punch": 3 bases, HQ L1 forever, masses 16+ at home with
  zero forward presence, then one 13-warrior punch at ~turn 70. 29 spent 1800
  gold on HQ tech exactly as the punch landed and died 9-trains-vs-17.
- Bot 7 froze 29 at 955 gold: enemies camping the HQ region make UPGRADE
  illegal, but 29 kept SAVING for that upgrade, which locked training.

30.py fixes (validated by replaying the recorded bot-3 game: 29 dies turn 79,
30 wins turn 187; pool results unchanged, vs 25 17W1L2D, vs 29 0L 20D):

- `under_pressure` (raid, HQ-adjacent enemy, or being outmassed by 5+ before
  turn 140) switches to war economy: no tech saving, train at cap.
- Never save for an upgrade that is illegal due to enemy presence.
- Any enemy near the HQ triggers interception, not just 3+ raiders.
- New `proxy-punch` pool style approximates bot 3 (calibration imperfect:
  29 still beats it 10-0; the recorded-log replay is the real regression test).

`29.py` is a fresh macro-first bot grown from the proxy engine (NOT from the
26-28 heuristic lineage). It needs no `data.bin`. Stale unsubmitted candidates
(`26.py`, `27.py`, `28.py`) and all pre-24 history now live directly under `bots/`.

29.py gate results (2026-07-02, per docs/workflow.md):

```text
proxy-econ   seeds 1-5+11-15:  7W  4L  9D   (28.py was 0W)
proxy-turtle seeds 1-5+11-15: 12W  4L  4D   (28.py was 0W)
proxy-rush   seeds 1-5+11-15: 20W  0L  0D
sample smoke seeds 1-5:       10W  0L, WA 0
vs 24.py     seeds 1-10 both: 17W  1L  2D
vs 25.py     seeds 1-10 both: 17W  1L  2D
max per-turn 3ms, 24KB source
```

Key mechanisms in 29.py, in causal order of discovery (each fixed a measured
failure -- see results/29-v*-proxy-pool):

1. Economy flywheel: training into open worker slots outranks savings.
2. Builder stays as worker on the base it just built (income from day one).
3. Arrived expanders hold position while saving for the build.
4. Contested strongholds claimed only with local force superiority.
5. Base upgrades capped at L2 (L3 is 8 warriors' worth of gold for +1 slot).
6. Proportional defense: intercept raids (3+), evacuate and fortress on
   invasions (8+), rush-alert lockdown in the first 30 turns.
7. Push only with numeric advantage (alive >= enemy + 8) and HQ tech, in
   waves, targeting weakly-guarded enemy buildings; HQ override from turn 182.

## Diagnosis 2026-07-02: Self-Play Collapse

The local selection loop had converged to a degenerate turtle meta:

- All candidate-vs-submission games ended at turn 200, mostly draws
  (a local draw game showed 17 vs 11 total trains in 200 turns).
- 28.py passed the old "no new losses vs latest two" gate while actually
  LOSING to 24/25/27 on turn-limit HP comparison (0W in all pairings).
- Official bots 4-8 play a completely different game: 3 bases by turn ~21,
  6-10 bases total, 4 HQ upgrades, 41-111 trains, HQ kill around turn 187-195.
- Conclusion: the benchmark, not the heuristics, was the bottleneck. Improving
  against a meta that contains no fast-economy opponent cannot move the server
  score.

Fix: `opponents/proxy.py` imitates the official macro styles and is now the
primary selection gate. Calibration against 25.py (known server 3W 5L):

```text
proxy-econ   (bots 4/5):   25.py 0W 8L 2D, HQ_DESTROYED turns 194-198
proxy-turtle (bots 6/7/8): 25.py 0W 4L 6D, turn-limit HP losses
proxy-rush   (bots 1-3):   25.py 8W 2D    (25 also beat those on the server)
28.py baseline: 0% vs proxy-econ, 0% vs proxy-turtle, 100% vs proxy-rush
```

The proxy reproduces the server failure pattern locally, so raising proxy
win rate is the development target. See docs/workflow.md for the gate commands.

Key lesson encoded in the proxy itself (useful for the real bot too): training
into open worker slots is an economic investment (120 gold -> 15/turn, 9-turn
payback), so economy saving must never starve worker training, and pushes must
wait for HQ tech (warrior HP) and travel in waves, not trickles.

## Competition Structure

The qualifier is an iterative submit-and-analyze round.

- A submission can include one code file and optionally one binary file.
- Code must be at most 1 MiB (1,048,576 bytes).
- The optional binary file must be at most 10 MiB (10,485,760 bytes).
- If a binary file is uploaded, it is exposed at runtime as `data.bin`.
- In Python, read it with `open("data.bin", "rb")`.
- Uploaded `data.bin` bytes count as additional memory used by the program.
- `data.bin` is available only at runtime and is not available during compilation.
- Runtime external API calls, including OpenAI API calls, are not a viable submission strategy. The judge does not guarantee network access, API keys cannot be safely embedded, and the per-turn 100ms limit leaves no room for remote inference.
- Immediately after submission, NYPC evaluates the answer against sample AIs and returns win/draw/loss results plus logs.
- The input is fixed.
- Sample AIs use the same strategy on the same input, so submitted logs are repeatable feedback for that submitted bot.
- Answers can be submitted many times.
- Among submitted answers, one representative answer can be selected for evaluation.
- Periodic rankings against other participants use the selected/latest representative submission state; confirm the UI before relying on a non-latest bot.
- At least the top 20 teams advance.

Qualifier round deadline:

```text
2026-07-08 22:00 KST
```

Execution environment:

```text
AWS c7a.2xlarge
AMD EPYC 4th gen custom processor
Clock: 3.7 GHz
Architecture: 64 bit
OS: Ubuntu 24.04
```

Strategic implication: submit stable candidates often enough to harvest official-bot logs, but avoid leaving an obviously experimental regression as the representative answer used for ranking.

For model-assisted work, use external tools only offline: analyze logs, generate maps/features/tables, then package the result into source constants or `data.bin`. The submitted bot must be self-contained.

## Current Server Baseline

`25.py` was submitted and `bots/25_nypc_log/` has been normalized to `1.txt` through `8.txt`.

Assuming the submitted bot is LEFT, the official-bot result is:

```text
25.py: 3W 5L
wins:  1.txt, 2.txt, 3.txt
losses: 4.txt, 5.txt, 6.txt, 7.txt, 8.txt
```

Important observations from `25.py`:

```text
25_nypc_log/4.txt: loses by HQ_DESTROYED on turn 189 after front shuttle/oscillation and enemy fast economy.
25_nypc_log/5.txt: loses by HQ_DESTROYED on turn 187; left trains 48, right trains 111, and left has long empty-command production gaps.
25_nypc_log/6.txt: loses by HQ_DESTROYED on turn 194 while stuck at 3 bases against enemy 7 bases.
25_nypc_log/7.txt: loses by HQ_DESTROYED on turn 191 after feeding units into a larger enemy stack.
25_nypc_log/8.txt: survives to turn limit but loses final state; expansion/rebuild is late.
```

So `26.py` targets meaningless work first: idle production, over-defense at home, A-B-A movement reversals, unwinnable base defense, and late mass response.

## Lessons From NYPC 2025 Reviews

The 2025 Code Battle writeups point to a deeper workflow than single-file heuristic tuning:

- Maintain many candidate strategies and pick a champion from large local leagues.
- Do not trust official sample bots alone; sample bots can be weak, weird, or unrepresentative.
- Save logs and statistics for each candidate, then select by robust matchups rather than one lucky score.
- Use offline computation or data files when the game has a stable state space or fixed inputs.
- Compress/quantize data only after measuring information loss against the original table.
- Prefer wider, reliable candidate evaluation over a deep but brittle search when the heuristic can prune away the real best move.
- Add dynamic strategy switching after identifying opponent style, instead of playing one fixed policy.
- Keep the final submitted representative conservative if experimental variants beat the champion locally but have side-effect risk.

The direct translation for this problem:

- Build a small league/test harness around saved submitted bots and candidate variants.
- Turn server logs into features: map fingerprint, enemy base timing, HQ timing, train count, pressure distance, HQ siege timing, final HP/result.
- Add opponent classification: rush, turtle, fast economy, balanced pressure, passive/idle.
- Track or estimate enemy gold/resources from observed successful actions and deterministic income/upkeep.
- Use map-specific or opponent-class-specific parameter profiles once enough official logs identify stable patterns.
- Treat official 8-bot logs as data. Submission count is plentiful, so stable submissions are a way to query the official environment.

## data.bin Opportunities

`data.bin` gives us a 10 MiB side channel for precomputed data. This matters because the official input is fixed and sample AIs are deterministic for the same input.

Evidence from our logs:

- Official logs across submissions keep stable map hashes for every corresponding index.
- This strongly suggests the 8 official sample-AI matches use stable indexed maps/opponents across submissions.
- Example regression to target:
  - index 7 map hash stayed the same
  - `8.py` survived to `RIGHT_WIN TURN_LIMIT`
  - `9.py` lost by `RIGHT_WIN HQ_DESTROYED`

Useful candidates:

- Map fingerprints -> official-bot index/profile parameters.
- Official-bot fingerprints from the 8 returned logs -> response profiles.
- Precomputed stronghold rankings, chokepoints, rush paths, defense anchor regions.
- Candidate parameter tables selected by `(map_id, opponent_profile, side)`.
- Compact statistics from local leagues: which profile beats which prior submission on which map class.

Recommended phases:

1. `data.bin` v0: no file. Hardcode only tiny profile experiments directly in code while proving value.
2. `data.bin` v1: compact map-hash table for the 8 official sample maps, profile labels, and small parameter overrides.
3. `data.bin` v2: larger table generated from local leagues and official logs, keyed by map features/profile class rather than exact map only. Used since `26.py`; the current candidate reads `28_data.bin`.
4. `data.bin` v3: precomputed path/stronghold/chokepoint scores if runtime computation or code-size pressure becomes meaningful.

Rules for using it safely:

- The bot must still run if `data.bin` is missing, so local testing remains simple.
- Keep the binary format tiny and versioned.
- Measure whether the data improves official-log replay and latest-two sparring before depending on it.
- Do not spend the 10 MiB budget on raw logs; store compact features/tables.
- For the current 8 official maps, exact hash-based overrides can fit in source code; use `data.bin` only when the table becomes too large or generated too often to maintain safely by hand.

## Candidate Research Notes (26 -> 28 lineage)

Inherited by the current candidate line from submitted `25.py`:

- Official map hash fingerprinting compatible with server log hashes.
- Built-in official 8-map profile table plus optional JSON `data.bin` override.
- Candidate-specific local data lookup: `26_data.bin`.
- Approximate enemy gold tracking from enemy upgrades, training, income, and upkeep.
- Profile-gated worker fill, urgent defense, HQ catch-up, and map-specific target-army caps.
- Protected-worker retention so base workers are not accidentally pulled into HQ worker/defender roles.
- Map/side plan data for expansion order, safe expansion order, frontier order, and staging.
- Anti-idle production when the enemy army is clearly ahead and no immediate HQ threat exists.
- Over-defense release so home garrison shrinks when the enemy is too far to punish.
- Abort rules for unwinnable base defense.
- Late swarm staging against huge enemy stacks.

Historical `26.py` validation before upload (pre-diagnosis; the all-draw
pattern below is exactly the degenerate meta described in the 2026-07-02
diagnosis section, not evidence of strength):

```text
sample smoke, seeds 1..10 both sides: 20W 0L 0D, WA 0
26 vs 24 local spar, seeds 151..170 both sides: 0W 0L 40D, WA 0
26 vs 25 local spar, seeds 151..170 both sides: 0W 0L 40D, WA 0
```

Official `25.py` server result:

```text
25.py: 3W 5L
wins: 1, 2, 3
losses: 4, 5, 6, 7, 8
```

Replay-side WA is not a real official win guarantee; it only means the new policy changes the state enough that recorded opponent commands become illegal.

Official `25` right-side replay with `26.py`:

```text
7W 1L, WA 4
Hard replay loss remains official map 5 (`77a57b8f617a`), turn 190.
```

So the current candidate is uploadable as a conservative probe, but the next work after submission should focus on official map 5.

Priority order (updated 2026-07-02):

1. Rebuild the candidate's macro so it beats `proxy-econ` and `proxy-turtle`:
   match the official expansion curve (3 bases ~turn 21, 5 by ~45), keep worker
   slots trained, tech HQ to 4-5, then attack in waves.
2. Gate every candidate on the proxy pool first, sample smoke second,
   latest-two spar third (see docs/workflow.md).
3. Submit the first candidate that clearly beats proxy-econ/turtle and analyze
   which official bots flip to wins.
4. Use `tools/extract_log_features.py` after every submission; if a proxy pool
   result disagrees with the server result, recalibrate the proxy styles from
   the new official logs.
5. Add broader opponent profile detection only when backed by official
   evidence.

The target is a reproducible selection loop: official logs -> proxy styles ->
candidate variant -> proxy-pool gate -> server submission -> recalibration.

Current official-bot profile sketch from `25.py` logs:

```text
1: passive/no-economy target; 25 wins by HQ_DESTROYED
2: short rush/interaction; 25 wins by HQ_DESTROYED
3: moderate economy/pressure; 25 wins by TURN_LIMIT
4: fast economy/many bases; 25 loses by HQ_DESTROYED
5: heavier fast economy/mass training; 25 loses by HQ_DESTROYED
6: turtle/tech/economy; 25 loses by HQ_DESTROYED
7: economy/turtle with large stack; 25 loses by HQ_DESTROYED
8: economy/turtle; 25 loses by TURN_LIMIT
```

## Official Python Sample Code

NYPC's Python/PyPy sample files are located outside the repo at:

```text
/Volumes/samsd/download_samsd/samplecode/
```

Both `sample-codepy.py` and `sample-codepypy.py` are identical. They are useful as protocol references, but the strategy is intentionally minimal: on turn 1, move every friendly warrior toward the enemy HQ and do nothing else.

Takeaways:

- Keep their parser/turn-result assumptions in mind when changing protocol code.
- Do not use the sample strategy as a performance baseline.
- The sample tracks only our gold, so enemy resource estimation is not provided by the official example.

## Validation Loop

Before upload, run:

```bash
CANDIDATE=bots/<candidate>.py
python3 -m py_compile "$CANDIDATE" tools/*.py
```

Run latest-two submission sparring:

```bash
python3 tools/run_submission_spar.py \
  --candidate "$CANDIDATE" \
  --latest 2 \
  --start 1 \
  --count 10 \
  --side both \
  --name candidate-vs-last2-10
```

Use `--count 10` for iteration to keep `bots/<candidate>_<submitted>log/` compact. Increase to `20` or `50` only for final confidence.

This also refreshes:

```text
bots/<candidate>_<old>log/
bots/<candidate>_<latest>log/
bots/<candidate>_<old>log.txt
bots/<candidate>_<latest>log.txt
```

After editing the candidate, delete stale local sparring logs before trusting any result:

```bash
rm -rf bots/<candidate>_*log bots/<candidate>_*log.txt
```

If server logs are available, analyze them:

```bash
python3 tools/analyze_server_logs.py bots/<submitted>_nypc_log
```

For a specific server loss replay:

```bash
python3 tools/run_log_replay.py \
  'bots/<submitted>_nypc_log/<loss>.txt' \
  --replay-side right \
  --candidate "$CANDIDATE" \
  --name replay-loss
```

Current local check files should live beside the bot. Latest baseline
(2026-07-02, gate order per docs/workflow.md):

```text
28.py proxy pool: proxy-econ 0W 10L, proxy-turtle 0W 10L, proxy-rush 10W 0L, WA 0
28 vs 24/25 spar: 0W 5L 15D each (turn-limit HP losses)
```

## Acceptance Criteria

- `WA = 0` in local checks.
- proxy-econ / proxy-turtle win rate at or above the previous candidate
  (primary criterion; current baseline is 0%).
- No new losses against proxy-rush or the latest two submissions.
- Server-loss replay should show materially disrupted losing trajectories without local WA.
- New server logs should show fewer idle production gaps, less over-defense, and fewer unwinnable base feeds.

## After Each Server Submission

1. Upload the current candidate.
2. NYPC starts sample-AI evaluation immediately and returns win/draw/loss logs.
3. Treat that uploaded file as the next submitted snapshot.
4. Delete the oldest submitted snapshot so only the latest two submitted snapshots remain.
5. Store NYPC logs for that submission as `bots/<number>_nypc_log/`.
6. Create the next candidate as the next numeric file, for example `bots/5.py`.
7. Delete the submitted candidate's local sparring logs, because they describe the pre-submission candidate-testing loop.
8. Use the new server logs as the next source of truth.
9. If the UI allows choosing a representative answer, make sure the intended stable submission is selected for ranking.

Example shape after submitting a candidate:

```bash
rm bots/<old>.py
rm -rf bots/<candidate>_*log bots/<candidate>_*log.txt
mv <downloaded_log_dir> bots/<submitted>_nypc_log
cp bots/<submitted>.py bots/<next_candidate>.py
```

Remaining core files:

```text
bots/<latest>.py
bots/<submitted>.py
bots/<submitted>_nypc_log/
bots/<next_candidate>.py
```

## Directory Policy

Keep:

```text
bots/<latest two submitted>.py
bots/<current candidate>.py
bots/<submission_number>_nypc_log/
bots/<candidate>_<submitted>log/
bots/<candidate>_<submitted>log.txt
docs/workflow.md
tools/
nation-providing/
game-rule.md
strategy-plan.md
```

Disposable:

```text
logs/
__pycache__/
.DS_Store
```

Do not reintroduce weak local synthetic opponent pools unless a new pool is demonstrably stronger than the current candidate.

## 2026-07-08 Movement Intent / Data Notes

`tools/analyze_move_intent.py` measures enemy MOVE-target ambiguity from logs.
Single-step movement is too noisy: in archived user logs, enemy steps compatible
with our HQ are actually HQ-bound only about 29% of the time. The signal becomes
usable after consecutive intersection: 2-3 tracked steps with a candidate set of
5 or fewer are HQ-bound about 88-90% of the time.

`bots/154.py` applies that signal conservatively: only 4 high-confidence
incoming-HQ enemies trigger rush/pressure, and 5 trigger full threatened mode.
Verification versus `151.py`: sample16 stays `16W/0L`; proxy-rush improves
seed1 `65/15 -> 76/4` and seed81 `59/21 -> 76/4`, with seed41 unchanged
`68/12`; non-rush proxy seed1/41/81 is unchanged; direct 77/90 gates are
unchanged (`77`: seed1 `6/0/74`, seed41 `6/1/73`, seed81 `10/8/62`; `90`
seed81 `10/6/64`). Eval29 full replay is unchanged in win/loss, and official
right-side replay over available submitted logs is `89W/0L/0D`. Current
candidate: `bots/154.py`.

`bots/155.py` experiments with `data.bin` map profiles generated by
`tools/build_155_data_bin.py` (`bots/155_data.bin`, 62KB, 108 profiles). The
loader works, but using generated expansion/staging plans regressed direct
77 seed1 to `6W/6L/68D`, so 155 is not a submission candidate. Continue using
data.bin only after the stored signal is narrower than generic map plans
(for example verified choke/intercept flags rather than replacing expansion
order wholesale).

`tools/build_intent_data_bin.py` is the narrower data.bin follow-up. It stores
only log-verified directed edges that were actually HQ-bound often enough
(default `min_count=3`, `min_precision=0.75`). Current
`bots/156_data.bin`/`bots/157_data.bin` is 9.8KB with 52 map profiles and
300 hot HQ edges. Offline replay accounting found 864 cases where the data
hot-edge signal adds an HQ-intent trigger beyond the map-only tight route
condition.

`bots/156.py` uses the hot-edge data only as a supplemental route confidence
signal; `bots/157.py` additionally lowers the intent threshold from `4/5` to
`3/4` only on maps where hot edges exist. With `bots/157_data.bin`, sample16
is `16W/0L`; proxy-rush seed1/41/81 remains `76/4`, `68/12`, `76/4`; direct
77 seed1/41 remains `6/0/74`, `6/1/73`; eval29 full replay remains
`A 19/1/0`, `B 14/5/1`; official right-side replay remains `89W/0L/0D`.
Targeted data-heavy replays do branch: for example `234494_A` changes from
HQ-destroyed T195 to replay-WA T130, and `211811_A` from replay-WA T99 to T92.
This proves data.bin can drive movement-intent behavior without replacing the
general map policy.

`tools/evaluate_intent_data.py` and `tools/intent_policy_data.py` split the
question into map memory versus generic movement features. Map-hash edge data
is extremely precise on seen maps (`hot_edge_actual_hq` 98.7%, data-extra
trigger precision 98.4% over archived user logs), but has zero coverage when an
entire eval folder uses unseen map hashes. Generic feature buckets do generalize:
training without eval29 still gives eval29 `39/39` HQ-bound generic triggers,
and training without eval28 gives eval28 `101/101` HQ-bound generic triggers.

`tools/build_combined_intent_data_bin.py` combines both signals. Current
`bots/159_data.bin` is 10.8KB with 52 map profiles, 300 map-specific HQ edges,
and 32 generic policy keys. `bots/158.py` lowered the intent threshold whenever
generic policy was present, but this regressed direct 77 seed1 to `6W/2L/72D`.
`bots/159.py` keeps generic policy as a hot-step supplement while only lowering
the threshold on maps with map-specific hot edges; this restores direct 77 seed1
to `6W/0L/74D`. Verified so far: sample16 `16W/0L`, proxy-rush seed1/41/81
`76/4`, `68/12`, `76/4`, direct 77 seed1/41 `6/0/74`, `6/1/73`, non-rush
seed1 unchanged, eval29 A replay `19/1/0`. Conclusion: generic policy is useful
as confidence evidence, but not strong enough by itself to lower global defense
thresholds.

Held-out bot-level checks: `bots/160.py` is 159 code with `bots/160_data.bin`
trained without eval29. On eval29, generic policy still reports `39/39`
HQ-bound triggers, while map-edge coverage is zero; replay remains unchanged
(`A 19/1/0`, `B 14/5/1`). `bots/161.py` is 159 code with `bots/161_data.bin`
trained without eval28. On eval28, generic policy reports `101/101` HQ-bound
triggers, and replay is `A 20/0/0`, `B 20/0/0`. This is the closest current
proxy for new middle-eval maps: generic policy generalizes as a conservative
confidence signal, while map-specific edge data should be treated as memory for
repeated maps.

`tools/analyze_building_intent.py` checked whether enemy movement traces can
predict attacks on our non-HQ bases. Offline precision is high only under very
narrow conditions: `steps>=2`, candidate count exactly 1, and that candidate is
one owned non-HQ base. Broader base-intent defense is unsafe. `bots/162.py`
(`<=2` candidates, 2 intents) regressed direct 77 seed1 to `6W/2L/72D`;
`bots/164.py` (`<=2`, 3 intents) had the same regression; `bots/165.py`
(exactly 1 candidate) still regressed direct 77 seed1 from `159: 6/0/74` to
`8/4/68`. Conclusion: do not move troops for inferred base intent yet. The
signal is useful for analysis, not policy.

`tools/analyze_user_style_features.py` now matches archived user logs with
opponent metadata and early style features, writing
`results/user-style-features.tsv`. Across 100 archived user games the biggest
observable bias is side/style: LEFT `39/18/7`, RIGHT `8/24/4`; `delayed_mass`
opponents are `29/37/8`, while fast macro and hq-tech buckets are mostly wins.
For eval29 specifically, losses are `8/10` on RIGHT and `9/10` in
`delayed_mass`. This means the remaining issue is not pure target inference:
it is RIGHT-side response to T40-T90 expansion plus army pressure.

`bots/166.py`/`167.py`/`168.py`/`169.py` explored an early HQ training-cap
savings gate for that RIGHT delayed-mass weakness. `166.py` was command no-op.
`167.py` converted `242702_B` from T90 HQ loss to replay-WA T85 and kept direct
77 seed1/41/81 equal to 159, but regressed proxy-rush seed1 from `76/4` to
`72/8`. `168.py` restricted the gate to map-specific hot-edge data; proxy-rush
returned to `76/4`, but eval29 B became no-op. `169.py` excluded all-in alert
but still had the proxy-rush `72/8` regression. Conclusion: keep
`bots/159.py + bots/159_data.bin` as the strongest current data candidate;
data.bin should stay as conservative intent confidence until a new policy
passes proxy-rush and direct gates.

`tools/movement_target_policy_data.py` extends movement analysis from
HQ-bound-only to generic target-type prediction. It builds compact JSON
`data.bin`-style policies from movement features and can run eval-folder
cross-validation. Current artifacts:
`results/movement-target-policy-data.bin`,
`results/movement-target-policy-crossval.tsv`,
`results/movement-target-hq-crossval.tsv`, and
`results/movement-target-attack-crossval.tsv`.

Cross-validation result: broad actionable target-type prediction is not safe
yet. Holding out each archived eval folder, all non-field labels cover only
3.0-5.6% of enemy MOVE records and score 83.9-88.8% precision. The weak labels
are `my_building` and `enemy_building`: held-out `my_building` predictions are
0% in multiple folds, and `enemy_building` is only 68.3-82.3%. Do not use this
for base defense or opponent economy/return policy.

HQ-only target policy is much cleaner. With labels `my_hq,enemy_hq`, held-out
coverage is 2.0-3.6% and precision is 93.7-100.0%; eval28/eval29 held-out are
100.0%. This supports the existing direction: data.bin can add conservative
HQ movement confidence, but base-target inference and broad target-class
switching remain analysis-only until they pass held-out and direct/proxy gates.

`tools/intent_policy_data.py` now has `crossval` and `trace` subcommands and
resets live warrior traces at log boundaries during evaluation. The reset did
not change the current aggregate crossval numbers, but it matches actual bot
runtime semantics and avoids future multi-log contamination.

Generic HQ-intent parameter checks: current `159_data.bin` uses
`policy_min_count=20`, `policy_min_precision=0.85`. Leave-one-eval-out trigger
precision is eval14 `86.1%`, eval25 `91.8%`, eval26/eval28/eval29 `100.0%`.
Lowering generic policy precision to `0.80` gives more route triggers
(eval14 `214`, eval26 `27`, eval28 `134`, eval29 `40`) with trigger precision
no worse in this archive, so `bots/170.py` was created as `159.py` plus
`bots/170_data.bin` built with `--policy-min-precision 0.80`.

`bots/170.py + bots/170_data.bin` is an analysis no-op candidate for now:
eval29 RIGHT replay remains `7W/5L/1D`, proxy-rush seed1 remains `76W/4L`,
direct 77 seed1 remains `6W/0L/74D`, and event logs match 159. The broader data
adds one eval29 generic HQ trigger (`240611_B.txt` T178, correctly HQ-bound)
but that log already wins and the extra signal is too late to affect commands.
Conclusion: p80 data is plausible but not currently useful without a policy
that consumes lower-count late HQ signals differently.

`tools/build_combined_intent_data_bin.py` can now embed
`movement_target_policy_data.py` output as `target_policy` in the same combined
data.bin. `bots/171.py` reads `target_policy` labels and treats `my_hq`
predictions as extra hot evidence. `bots/172.py` is the stronger consumption
variant: when target-policy predicts `my_hq`, it raises that trace's
`hot_steps` to at least 2 immediately.

Runtime result: `bots/171.py`/`bots/172.py` with `171_data.bin`/`172_data.bin`
are safe but command no-op on the current gates. The combined data has 137
target-policy keys and on eval29 predicts 181 `my_hq` moves plus 520
`enemy_hq` moves at 99.7% total precision, but eval29 RIGHT replay stays
`7W/5L/1D`, proxy-rush seed1 stays `76W/4L`, direct 77 seed1 stays
`6W/0L/74D`, sample16 stays `16W/0L`, and event logs match 159. Interpretation:
HQ target-policy is real signal, but the existing decision points either
already react or receive it too late. The next useful step is not more labels;
it is finding a decision that consumes late/high-confidence HQ intent
differently, such as HQ repair/counter-race/garrison sizing, then validating
against direct/proxy gates.

`bots/173.py`/`bots/174.py` tried those first consumption points. `173.py`
allows high-confidence incoming-HQ intent to trigger HQ upgrade/repair before
enemies reach 1-hop range. `174.py` extends the `threatened` incoming-HQ gate
from T120 to T180. Both remain command no-op on eval29 RIGHT replay and keep
proxy-rush seed1 `76W/4L`, direct 77 seed1 `6W/0L/74D`, sample16 `16W/0L`.
This suggests the late signal is not enough by itself: in the target losses the
bot often lacks gold for HQ repair/upgrade or already has all surviving units at
HQ.

`tools/analyze_hq_intent_lead_time.py` measures how many turns each HQ-intent
signal leads enemy arrival at 1-hop from our HQ. With `172_data.bin`, eval29
has 95 HQ-bound enemy movement sequences: tight-route detects 81, combined
detects 79, target-policy detects 64. Target-policy is more often early:
`lead>=2` is 25 sequences versus 7 for tight/combined. On the five remaining
eval29 RIGHT losses, target-policy gets `lead>=2` on 12 sequences, while
combined gets only 3. Archive-wide: combined detects more total HQ sequences
(`968/1191`) but target-policy is close on `lead>=3` (`258` vs `263`) despite
lower total detections. Interpretation: target-policy is valuable specifically
as an earlier warning signal, not as a broader replacement for combined
HQ-intent.

`bots/175.py`/`bots/176.py` consumed late target-policy HQ intent by relaxing
T160+ supply reserve and immediately counting target-policy hits as 2 hot
steps. This produced real command changes on `238554_B` and delayed the HQ loss
from T183 to T186 without flipping the result. Proxy-rush seed1 stayed
`76/4`, direct77 seed1 stayed `6/0/74`, and sample16 stayed `16/0`.

`bots/177.py` revisited the earlier `167.py` HQ L1 escape idea with a much
narrower gate: RIGHT only, enemy base lead +2, at least 4 own bases, no enemy
at HQ 1-hop, and delayed-mass style pressure. This flips `242702_B` to a real
HQ-destroyed replay win and changes `244910_B` to replay-WA, raising eval29 B
from `7/5/1` to `9/3/1`. It keeps proxy-rush seed1/41/81 at
`76/4`, `68/12`, `76/4`, direct77 seed1/41 at `6/0/74`, `6/1/73`, and
sample16 at `16/0`.

`bots/178.py` tried only raising RIGHT macro-catchup expansion target/parallel
when enemy bases led, but it was command no-op because the bot had almost no
free units; workers were already assigned to existing bases.

`bots/179.py` released up to two safe non-HQ workers as settlers during RIGHT
macro-catchup. It raised eval29 B replay to `12/1/0`, but proxy-econ seed41
regressed one draw to a loss (`159: 67/2/11`, `179: 67/3/10`) on a balanced
economy game, so the +2 base-lead release was too broad.

`bots/180.py + bots/180_data.bin` narrows that worker release to enemy base
lead +3 while keeping the 177 HQ L1 escape. Current verification: eval29 B
replay `12/1/0` with 7 replay-WA branches, eval29 A replay unchanged `6/1/0`;
sample16 `16/0`; proxy-rush seed1/41/81 `76/4`, `68/12`, `76/4`;
proxy-econ seed1/41 `66/1/13`, `67/2/11`; proxy-turtle seed1/41 `79/0/1`,
`76/0/4`; proxy-punch seed1/41 `80/0/0`, `80/0/0`; direct77 seed1/41/81
`6/0/74`, `6/1/73`, `10/8/62`; direct90 seed1/41 `6/0/74`, `6/1/73`.
Conclusion: 180 is the strongest current data-assisted candidate, but replay-WA
wins are branch signals, not guaranteed server wins. The remaining eval29 B
loss is `243173_B`, an early total-economy collapse where even correct HQ
intent arrives with almost no gold or bases.

`tools/analyze_group_hq_intent.py` now measures same-turn grouped enemy movement
support for our HQ. It reports per-turn enemy mover count, actual HQ-bound
movers, one-step HQ compatibility, multi-step trace HQ support, target-policy
HQ support, and state columns such as bases, alive counts, HQ level, and enemy
near3. This directly tests the "multiple troops moving together" hypothesis.

Archive-wide grouped HQ findings: one-step support is too noisy even at high
thresholds (`step_hq_support>=12`: `152/236`, 64.4%). Multi-step trace support
is better but still not submit-safe alone (`trace_hq_support>=6`: `243/294`,
82.7%; `>=8`: `168/191`, 88.0%). The data.bin target-policy remains much
cleaner (`target_policy_hq_support>=1`: `293/300`, 97.7%; `>=3`: `209/210`,
99.5%; `>=5`: `166/166`, 100.0%).

For `243173_B`, grouped trace detects the HQ attack much earlier than the
target-policy: actual HQ-bound moves start at T78, `trace_hq_support` reaches
3 at T83 and 8 at T88, while target-policy only appears at T90. However,
state-filtered archive precision is not enough for a broad bot trigger:
`trace>=3 and bases0 and HQ L1` is only `25/38` (65.8%), and
`trace>=6 and bases0 and HQ L1` is `13/19` (68.4%). Interpretation: grouped
trace is a useful analysis/data feature, but not yet a direct action trigger.
The next data.bin direction is to learn a grouped trace policy with additional
map/turn/economy features, not to hard-code raw trace thresholds.
