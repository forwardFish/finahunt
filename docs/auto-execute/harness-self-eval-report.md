# Harness Self-Evaluation Report

Generated: 05/14/2026 11:00:13

- Status: PASS
- Passed: 8/8

| Test | Status | Details | Evidence |
|---|---|---|---|
| PRD fixture generates requirement candidates | PASS | Expected upload/report/7-day-plan requirement candidates; got 3. | docs\auto-execute\requirement-candidates.json |
| PRD fixture generates story candidates | PASS | Expected upload/report story candidate. | docs\auto-execute\story-candidates.json |
| Story test points materialize to commands/evidence | PASS | Expected route/api/visual materialization with commands and evidence outputs. | docs\auto-execute\story-materialized-tests.json |
| Story quality gate accepts normalized story | PASS | Expected story quality gate to pass normalized P0 story. | docs\auto-execute\story-quality-gate.json |
| Bad requirement missing evidence fails final gate | PASS | Expected final gate non-zero for missing evidence; exit=1 verdict=HARD_FAIL. | docs\auto-execute\machine-summary.json |
| Bad UI missing screenshot fails UI verifier | PASS | Expected compare-ui HARD_FAIL when PASS UI lacks actual screenshot. | docs/auto-execute/results/compare-ui.json |
| Bad story without testPoints fails story gate | PASS | Expected story quality gate HARD_FAIL for P0 story without testPoints. | docs\auto-execute\story-quality-gate.json |
| PASS_WITH_LIMITATION strict semantics are encoded | PASS | Expected final gate to reject limitations in Strict mode. | scripts/acceptance/run-final-gate.ps1 |
