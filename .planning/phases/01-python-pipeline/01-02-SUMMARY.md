---
phase: 01-python-pipeline
plan: "02"
subsystem: custom-metrics-scaffold
tags: [ragas, custom-metrics, autodiscovery, python-package]
dependency_graph:
  requires: [ragas-importable]
  provides: [custom-metrics-package, ExampleCustomMetric-discoverable]
  affects: [eval/eval_ragas_metrics.py]
tech_stack:
  added: []
  patterns: [MetricWithLLM+SingleTurnMetric inheritance, PydanticPrompt for structured LLM output, @dataclass decorator for RAGAS metrics, score clamping guard]
key_files:
  created:
    - eval/custom_metrics/__init__.py
    - eval/custom_metrics/example_metric.py
  modified: []
decisions:
  - "No __all__ or ragas imports in __init__.py — autodiscovery uses pkgutil.iter_modules, not __all__; early imports would cause failures when ragas absent"
  - "score clamp max(0.0, min(1.0, float(out.score))) in _single_turn_ascore — mitigates T-01-02-02 (LLM hallucinated score outside valid range)"
  - "Russian docstring in example_metric.py — user will copy this template; English boilerplate would be inconsistent with project language convention"
metrics:
  duration: "5 minutes"
  completed: "2026-04-18"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 01 Plan 02: Custom Metrics Scaffold Summary

**One-liner:** Created `eval/custom_metrics/` Python package with `ExampleCustomMetric` class inheriting `MetricWithLLM + SingleTurnMetric`, enabling Plan 03 autodiscovery via `pkgutil + issubclass`.

## Objective

Create scaffold for custom RAGAS metrics: a Python package `eval/custom_metrics/` with a working example (`example_metric.py`) that Plan 03 can use for autodiscovery. The example must compile, inherit the correct base classes, and implement `_single_turn_ascore` without `NotImplementedError`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create custom_metrics package marker | 624faee | eval/custom_metrics/__init__.py |
| 2 | Create ExampleCustomMetric template | d85d78e | eval/custom_metrics/example_metric.py |

## Verification Results

All acceptance criteria passed:

**Task 1 (`__init__.py`):**
- File exists: confirmed
- `python3 -c "import importlib.util; ..."` exits 0: OK
- `grep -c "MetricWithLLM"` = 1: OK
- Lines = 3 (within 3-5): OK
- No `import ragas` or `import langchain`: OK

**Task 2 (`example_metric.py`):**
- `python3 -c "import ast; ast.parse(...)"` exits 0: AST OK
- `grep -c "class ExampleCustomMetric(MetricWithLLM, SingleTurnMetric)"` = 1: OK
- `grep -c "class CompletenessOutput(BaseModel)"` = 1: OK
- `grep -c "class CompletenessPrompt(PydanticPrompt"` = 1: OK
- `grep -c "async def _single_turn_ascore"` = 1: OK
- `grep -c "NotImplementedError"` = 0: OK
- `grep -c "name: str = "` = 1: OK
- `grep -cE "^from ragas"` = 3 (>= 2): OK
- Lines = 78 (within 40-120): OK

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. `ExampleCustomMetric._single_turn_ascore` has a real implementation that calls `self.completeness_prompt.generate(...)` - not a stub, not `NotImplementedError`. The metric will be executable after `pip install -r requirements.txt`.

## Threat Flags

None. Both new files introduce no network endpoints, auth paths, or schema changes at trust boundaries. The score clamping guard (`max(0.0, min(1.0, float(out.score)))`) mitigates T-01-02-02 as specified in the threat model.

## Self-Check: PASSED

- `eval/custom_metrics/__init__.py` exists: FOUND
- `eval/custom_metrics/example_metric.py` exists: FOUND
- Commit 624faee exists: FOUND
- Commit d85d78e exists: FOUND
- 0 deletions in either commit
