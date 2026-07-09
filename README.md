# 2026_nypc

NYPC 2026 Code Battle 예선 게임 `NEXT NATION`을 준비하며 만든 봇 개발
워크스페이스입니다.

- Team: `softkleenex.`
- Final submitted bot: `bots/183.py`
- Final submitted data file: `bots/183_data.bin`
- Main postmortem: `docs/183-user-log-analysis.md`

---

## 빠른 시작

- 대회와 게임 규칙은 `docs/nypc-overview-rules.md`에서 확인합니다.
- 제출 봇과 로그 보관 규칙은 `bots/README.md`와 `docs/bots-organization.md`에 정리했습니다.
- 봇 개발 흐름과 전략 기록은 `docs/workflow-strategy.md`가 기준입니다.
- 에이전트/기여자 작업 지침은 루트 `AGENTS.md`를 기준으로 봅니다.

```bash
python3 -m py_compile bots/<n>.py tools/*.py
python3 tools/evaluate_pool.py --bot bots/<n>.py --start 1 --count 5 --side both --pools sample --name <n>-sample-smoke
```

---

## 유저 상대 평가 그래프

아래 그래프는 중간평가 로그 기준입니다. 유저 상대 결과는 실제 대회 상대와의
대련 결과이며, 로컬 proxy/direct 결과와 일대일로 대응하지 않습니다.

```mermaid
xychart-beta
    title "User Evaluation Rating"
    x-axis ["#14 ?", "#25 62", "#26 77", "#28 91", "#29 145", "#30 183"]
    y-axis "rating" 0 --> 2500
    line [1750, 1980, 1910, 1880, 1920, 1710]
```

```mermaid
xychart-beta
    title "User Evaluation Score"
    x-axis ["#14 ?", "#25 62", "#26 77", "#28 91", "#29 145", "#30 183"]
    y-axis "score / 20" 0 --> 20
    line [10.5, 11.0, 11.0, 10.5, 9.5, 9.0]
```

```mermaid
xychart-beta
    title "User Evaluation Wins"
    x-axis ["#14 ?", "#25 62", "#26 77", "#28 91", "#29 145", "#30 183"]
    y-axis "wins" 0 --> 20
    bar [9, 10, 10, 9, 9, 8]
```

```mermaid
xychart-beta
    title "User Evaluation Losses"
    x-axis ["#14 ?", "#25 62", "#26 77", "#28 91", "#29 145", "#30 183"]
    y-axis "losses" 0 --> 20
    bar [8, 8, 8, 8, 10, 10]
```

| Eval | Bot | User W-D-L | Score | Tier | Rating | Rank |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| #14 | ? | 9-3-8 | 10.5 | 7 | 1750 | 249 / 700 |
| #25 | 62 | 10-2-8 | 11.0 | 9 | 1980 | 263 / 864 |
| #26 | 77 | 10-2-8 | 11.0 | 9 | 1910 | 256 / 876 |
| #28 | 91 | 9-3-8 | 10.5 | 7 | 1880 | 362 / 907 |
| #29 | 145 | 9-1-10 | 9.5 | 9 | 1920 | 469 / 914 |
| #30 | 183 | 8-2-10 | 9.0 | 7 | 1710 | 579 / 937 |

---

## 로컬 봇 상대 결과

대표 체크포인트만 요약했습니다. 각 bot마다 평가 범위가 다르므로 같은 표 안에서도
동일 조건 비교가 아닌 행은 설명을 함께 적었습니다.

```mermaid
xychart-beta
    title "Local Proxy Rush Win Rate"
    x-axis ["150", "151", "180", "183"]
    y-axis "win rate %" 0 --> 100
    bar [80.0, 80.0, 91.7, 95.0]
```

| Bot checkpoint | Local bot-opponent result |
| --- | --- |
| 150 | Proxy rush seed1/41/81: `192W/48L/0D` (`80.0%`). Non-rush proxy: econ `201W/6L/33D`, turtle `234W/0L/6D`, punch `240W/0L/0D`. |
| 151 | Same proxy totals as 150; selected because it improved one eval29 replay branch without local regression. |
| 180 | Proxy rush seed1/41/81: `220W/20L/0D` (`91.7%`). Direct vs 77/90 seed1 improved from `4W` to `6W` with no added losses. |
| 183 | Proxy smoke seed1+41: rush `76W/4L/0D` (`95.0%`), econ `67W/1L/12D`, turtle `78W/0L/2D`, punch `80W/0L/0D`. Final user eval still regressed. |

---

## 주요 Bot 서명

- 0062 bot: early user-eval baseline. Tier 9 / rating 1980까지 올렸지만, 고티어 상대로 경제와 HQ race 취약점이 남았습니다.
- 0077 bot: 안정 기준선. 이후 후보의 direct sparring 기준으로 오래 사용했습니다.
- 0091 bot: 초반 all-in mass 감지와 desperate race gate가 들어간 안전 후보 계열의 중심입니다.
- 0125 bot: 기지 붕괴 중 안전 재건 reserve 우회로 실제 손실 로그를 처음 크게 건드린 후보입니다.
- 0135 bot: 공식 8번 draw 원인을 제거한 제출 후보입니다.
- 0145 bot: 공식 서버 로그 8승 제출 이후 eval29 유저 로그 분석의 기준점입니다.
- 0150 bot: delayed mass rush latch로 eval29 손실 3개를 replay branch에서 개선했습니다.
- 0151 bot: 초단기 delayed mass 즉시 감지 보강. 로컬 무회귀였지만 user score는 확정 개선으로 이어지지 않았습니다.
- 0180 bot: `data.bin` 기반 target-policy와 RIGHT macro 보정을 묶은 강한 로컬 후보입니다.
- 0183 bot: 최종 제출본. grouped HQ policy data와 T30-T70 근접 압박 요새화 보정이 들어갔지만, 최종 유저 평가에서는 zero-base fallback과 midgame economy preservation 약점이 드러났습니다.

---

## 폴더 구조

- `bots/`: 활성 제출 봇과 NYPC/유저 로그. `*_nypc_log/`, `*_user_log/`, `archive/`는 보존 데이터입니다.
- `tools/`: 평가, 리플레이, 로그 분석, 튜닝 스크립트입니다.
- `nation-providing/`: 공식 로컬 테스트 도구, 샘플 코드, 설정 파일입니다.
- `opponents/`: 로컬 평가용 프록시 상대입니다.
- `docs/`: 통합 문서, 운영 문서, postmortem입니다.
- `results/`: 생성된 평가 결과입니다. Git에는 올리지 않고 결론만 문서화합니다.

---

## Postmortem

최종 `183`의 이동 예측은 precision은 높았지만 sparse했습니다. 마지막 유저 로그에서
더 큰 문제는 다음 세 가지였습니다.

- zero-base / no-expansion fallback 부재
- 중반 HQ 직행 wave에 대한 전용 방어 부족
- T90-T160 base preservation 실패

자세한 내용은 `docs/183-user-log-analysis.md`에 정리했습니다.
