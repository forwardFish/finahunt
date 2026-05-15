# Acceptance Comparison Loop

A delivery is complete only when one comparison round shows the implementation, requirement docs, UI references, contract map, tests, and evidence are aligned with no unresolved P0/P1 gaps.

| Round | Result | Requirement alignment | UI alignment | Contract alignment | Test evidence | Remaining gaps | Next action | Evidence |
|---|---|---|---|---|---|---|---|

| round-001 | HARD_FAIL | ok | ok | ok | gap | 4 gaps / 2 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-001.json |
| round-002 | HARD_FAIL | ok | gap | gap | ok | 101 gaps / 0 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-002.json |
| round-003 | HARD_FAIL | ok | gap | gap | ok | 101 gaps / 0 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-003.json |
| round-004 | HARD_FAIL | ok | ok | ok | ok | 1 gaps / 0 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-004.json |
| round-005 | PASS | ok | ok | ok | ok | 0 gaps / 0 limitations | No unresolved comparison gaps detected. Proceed to code review/final report. | docs\auto-execute\comparison\round-005.json |
| round-006 | PASS | ok | ok | ok | ok | 0 gaps / 0 limitations | No unresolved comparison gaps detected. Proceed to code review/final report. | docs\auto-execute\comparison\round-006.json |
| round-007 | PASS | ok | ok | ok | ok | 0 gaps / 0 limitations | No unresolved comparison gaps detected. Proceed to code review/final report. | docs\auto-execute\comparison\round-007.json |
| round-008 | HARD_FAIL | ok | ok | ok | ok | 12 gaps / 0 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-008.json |
| round-009 | HARD_FAIL | ok | ok | ok | ok | 20 gaps / 0 limitations | Use this comparison round as the next repair input, update implementation/evidence, then run another comparison round. | docs\auto-execute\comparison\round-009.json |
