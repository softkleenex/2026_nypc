# Integration Check

생성 시각: 2026-07-08 03:41:46 UTC

재검증 시각: 2026-07-08 13:02:24 KST

## 검증 방법

각 원본 파일의 UTF-8 텍스트가 해당 통합 문서 안에 정확히 포함되는지 검사했다. `Exact Included`가 `yes`이면 원본 전체가 통합본에 연속 문자열로 존재한다.

## 결과

전체 결과: PASS

| Group | Source | Lines | Bytes | SHA-256 | Target | Exact Included |
| --- | --- | --- | --- | --- | --- | --- |
| agent-context | docs/archive/AGENTS.before-agent-merge.md | 38 | 2932 | f36f8570494fff6a2f2415340efb795c644e3e34cbbaf323b370a4f71811fc89 | AGENTS.md | yes |
| agent-context | docs/archive/CLAUDE.before-agent-merge.md | 627 | 52311 | 1ec07125183709fa260928346ad8ed400d663e7cf3220ed75872cd1533216f9d | AGENTS.md | yes |
| workflow-strategy | docs/archive/workflow.before-workflow-merge.md | 157 | 8797 | 45215765b9e515c796dcf37906070733ab024b864dcf6e613cd3d359935a4546 | docs/workflow-strategy.md | yes |
| workflow-strategy | docs/archive/strategy-plan.before-workflow-merge.md | 672 | 31347 | a39be207517aeee20957635a0747b100f9cde7f37cfa6844a1d85f6aa9a2381d | docs/workflow-strategy.md | yes |
| nypc-overview-rules | nypc_개요.txt | 177 | 13734 | 4b1810ce7f437b67124413a50509dae5be14d92790780d2d3af395795029f958 | docs/nypc-overview-rules.md | yes |
| nypc-overview-rules | game-rule.md | 639 | 27034 | ded3f45305f5ba6e00eb76c655819a8e550d2a820954bcfbabd57cb93ccfc9ac | docs/nypc-overview-rules.md | yes |

## 주의

이 검사는 원문 누락 여부를 확인한다. 문서 앞부분의 읽기용 안내는 원문을 대체하지 않으며, 판단이 필요한 세부 사항은 아래 원문 영역을 기준으로 확인한다.

`bots/README.md`, `docs/bots-organization.md`, `docs/user-log-storage-review.md`는 제출 단위와 로그 보관 방식을 정리하기 위해 별도로 갱신한 운영 문서다. 루트 봇 파일 일부는 `bots/archive/`로 이동했고, 유저 로그는 `bots/user_logs/` 표준 구조로 이동했다.
