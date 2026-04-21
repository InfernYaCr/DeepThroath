---
phase: 01-python-pipeline
verified: 2026-04-18T00:00:00Z
status: human_needed
score: 7/9
overrides_applied: 0
human_verification:
  - test: "Run pip install -r requirements.txt in project .venv and confirm no conflicts"
    expected: "pip resolves ragas>=0.2.0, langchain-openai>=0.1.0, langchain-core>=0.2.0 alongside deepeval==3.9.3 and openai==2.30.0 without version conflicts"
    why_human: "ragas and langchain-* are not installed in .venv or eval/.venv. Cannot run the script to confirm the goal. Conflict checking requires live PyPI resolution and cannot be done without network access or modifying the environment."
  - test: "Run python eval/eval_ragas_metrics.py eval/top_k/20260329_171419_exp_top_k_10.json with valid OPENAI_API_KEY and a reachable RAG API endpoint"
    expected: "Script completes without exception and creates eval/results/{timestamp}_20260329_171419_exp_top_k_10_ragas/metrics.json containing faithfulness_score, answer_relevancy_score, context_precision_score, context_recall_score, answer_correctness_score fields"
    why_human: "No ragas run has been executed — eval/results/ contains no _ragas folders. Requires live LLM API key and a running RAG endpoint configured in eval/config/eval_config.yaml or API_URL env var."
---

# Phase 1: Python Pipeline Verification Report

**Phase Goal:** Разработчик может запустить RAGAS-оценку командой `python eval/eval_ragas_metrics.py` и получить результаты в eval/results/
**Verified:** 2026-04-18
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python eval/eval_ragas_metrics.py` on an existing dataset completes without errors and creates `eval/results/{timestamp}_ragas/metrics.json` | ? UNCERTAIN | Script code is complete and correct. ragas + langchain-openai + langchain-core are in requirements.txt but NOT installed in .venv or eval/.venv. Script fails at `from ragas import ...` in current environments. No _ragas results folder exists in eval/results/. Requires installed deps + live API. |
| 2 | metrics.json contains computed values for all 5 metrics: Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall, AnswerCorrectness | ? UNCERTAIN | save_results() correctly maps all 5 metric keys to *_score fields (grep confirms faithfulness_score, answer_relevancy_score, context_precision_score, context_recall_score, answer_correctness_score all present). Cannot verify output file without a successful run. |
| 3 | If retrieval_context absent in all records, script does not crash and skips contextual metrics with warning | ✓ VERIFIED | select_metrics() checks `has_context = any(s.retrieved_contexts for s in dataset.samples)`. When False: UserWarning emitted, Faithfulness/ContextPrecision/ContextRecall skipped, AnswerRelevancy + AnswerCorrectness retained. Code path confirmed in eval_ragas_metrics.py lines 343-355. No external dependency needed. |
| 4 | Script uses OPENAI_API_KEY and OPENAI_BASE_URL from .env — same config as DeepEval | ✓ VERIFIED | `load_dotenv(Path(__file__).parent / ".env")` at line 39. build_judge() reads `os.environ["OPENAI_API_KEY"]` and `os.getenv("OPENAI_BASE_URL")` at lines 105-108. build_embeddings() same pattern lines 120-124. JUDGE_PROVIDER defaults to "openai". |
| 5 | Python classes from eval/custom_metrics/ are automatically discovered when folder exists | ✓ VERIFIED | discover_custom_metrics() uses pkgutil.iter_modules + importlib.import_module + issubclass(cls, MetricWithLLM) and issubclass(cls, SingleTurnMetric) checks at lines 298-330. ExampleCustomMetric in eval/custom_metrics/example_metric.py correctly inherits both base classes. sys.path fix in main() ensures eval.custom_metrics importable from any directory. |
| 6 | requirements.txt contains ragas, langchain-openai, langchain-core with deepeval==3.9.3 preserved | ✓ VERIFIED | grep confirms: ragas>=0.2.0 (line 18), langchain-openai>=0.1.0 (line 19), langchain-core>=0.2.0 (line 20). deepeval==3.9.3 (line 2) unchanged. deepteam==1.0.6 (line 1) unchanged. No monolithic `langchain` package added. Total 20 lines (was 17 + 3). |
| 7 | pip install -r requirements.txt passes without version conflicts | ? UNCERTAIN | Dependencies are specified with compatible range pinning (>=) alongside existing pinned versions. Cannot verify without running pip against live PyPI. ragas and langchain-* are not yet installed in either project venv. |
| 8 | eval/custom_metrics/ exists as a Python package with working ExampleCustomMetric template | ✓ VERIFIED | __init__.py: 3 lines, mentions MetricWithLLM, no ragas import (valid Python module). example_metric.py: 78 lines, AST valid, ExampleCustomMetric(MetricWithLLM, SingleTurnMetric) with @dataclass decorator, name="completeness", async _single_turn_ascore returning clamped float, no NotImplementedError, docstring in Russian. |
| 9 | eval/eval_ragas_metrics.py is a complete, runnable pipeline (not a stub) | ✓ VERIFIED | 508 lines. AST valid. All required functions present: build_judge, build_embeddings, load_eval_config, get_value_by_path, resolve_template, fetch_from_api, load_and_enrich_records, build_dataset, discover_custom_metrics, select_metrics, save_results, run_pipeline, main. raise_exceptions=False in evaluate(). No NotImplementedError. No v0.1 ragas API. No ThreadPoolExecutor. |

**Score:** 7/9 truths verified (2 uncertain — require human/live environment verification)

### Deferred Items

None. All phase 1 items are in scope for this phase.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | Python dependency list containing ragas | ✓ VERIFIED | 20 lines. ragas>=0.2.0, langchain-openai>=0.1.0, langchain-core>=0.2.0 appended. All 17 original lines preserved. |
| `eval/custom_metrics/__init__.py` | Package marker for autodiscovery (min 1 line) | ✓ VERIFIED | 3 lines. Valid Python. Mentions MetricWithLLM. No ragas import. |
| `eval/custom_metrics/example_metric.py` | Example custom metric with ExampleCustomMetric class (min 40 lines) | ✓ VERIFIED | 78 lines. All required elements present. AST valid. |
| `eval/eval_ragas_metrics.py` | Python pipeline with def main (min 250 lines) | ✓ VERIFIED | 508 lines. All required functions implemented. No stubs. |
| `eval/results/{timestamp}_{stem}_ragas/metrics.json` | RAGAS run output with faithfulness_score | ✗ MISSING | No _ragas results directory exists. This is a runtime artifact — requires successful end-to-end execution with installed dependencies and live APIs. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `requirements.txt` | `eval/eval_ragas_metrics.py` | `import ragas, langchain_openai` | PARTIAL | requirements.txt has ragas>=0.2.0 and langchain-openai>=0.1.0. Script imports both at module level. Link is structurally correct but packages not installed — import fails at runtime. |
| `eval/eval_ragas_metrics.py` | `eval/config/eval_config.yaml` | `yaml.safe_load` in load_eval_config() | ✓ WIRED | load_eval_config() opens CONFIG_PATH with yaml.safe_load. CONFIG_PATH = Path(__file__).parent / "config" / "eval_config.yaml". File exists. |
| `eval/eval_ragas_metrics.py` | RAG API endpoint | `httpx.Client(timeout=120.0, verify=False)` | ✓ WIRED (code) | fetch_from_api() uses httpx.Client at line 205. Falls back to API_URL env var when api_config absent. Raises RuntimeError with clear message if neither configured. |
| `eval/eval_ragas_metrics.py` | `ragas.evaluate` | `EvaluationDataset + metrics + LangchainLLMWrapper + RunConfig + raise_exceptions=False` | ✓ WIRED (code) | evaluate() call at lines 464-471 with all required params. EvaluationDataset(samples=...) at line 295. RunConfig(max_workers=3, max_wait=120) at line 463. |
| `eval/eval_ragas_metrics.py` | `eval/custom_metrics/*.py` | `pkgutil.iter_modules + importlib.import_module + issubclass(cls, MetricWithLLM) and issubclass(cls, SingleTurnMetric)` | ✓ WIRED | discover_custom_metrics() lines 298-330. Both issubclass checks present. Called from select_metrics() line 363. sys.path fix in main() ensures eval.custom_metrics importable. |
| `eval/eval_ragas_metrics.py` | `eval/results/{ts}_{stem}_ragas/metrics.json` | `json.dump with *_score fields` | ✓ WIRED (code) | run_dir = OUTPUT_DIR / f"{ts}_{stem}_ragas" at line 476. save_results() writes all 5 standard *_score fields + custom metric scores. Never executed — no output exists. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `eval_ragas_metrics.py: run_pipeline` | `records` | `load_and_enrich_records()` → `fetch_from_api()` → httpx POST to RAG API | Requires live API endpoint | ✓ FLOWING (code path complete, runtime dependency) |
| `eval_ragas_metrics.py: run_pipeline` | `dataset` | `build_dataset(records)` → `EvaluationDataset(samples=[SingleTurnSample(...)])` | Derived from records with field mapping | ✓ FLOWING (code path complete) |
| `eval_ragas_metrics.py: run_pipeline` | `result` | `evaluate(dataset, metrics, llm, embeddings, ...)` | Requires live LLM API + installed ragas | ✓ FLOWING (code path complete, runtime dependency) |
| `eval/results/{ts}_ragas/metrics.json` | Output file | `save_results(filtered_records, result, run_dir)` | NaN-to-None converted, json.dump | ✗ DISCONNECTED (never executed — no output file exists) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Usage message on no-args invocation | `python eval/eval_ragas_metrics.py` | `ModuleNotFoundError: No module named 'ragas'` | ✗ FAIL (deps not installed — correct behavior coded but unreachable) |
| "File not found" on nonexistent path | `python eval/eval_ragas_metrics.py /nonexistent.json` | `ModuleNotFoundError: No module named 'ragas'` | ✗ FAIL (same root cause — ragas not installed in any project venv) |
| AST validity of eval_ragas_metrics.py | `python3 -c "import ast; ast.parse(...)"` | `AST OK` | ✓ PASS |
| AST validity of example_metric.py | `python3 -c "import ast; ast.parse(...)"` | `AST OK` | ✓ PASS |

Note: Both behavioral failures have a single root cause — `ragas`, `langchain-openai`, `langchain-core` are declared in `requirements.txt` but not installed in the project's `.venv` or `eval/.venv`. The script code itself is correct.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RAGAS-01 | 01-03-PLAN.md | User can run RAGAS eval via eval/eval_ragas_metrics.py | ? NEEDS HUMAN | Script exists and is complete. Cannot confirm end-to-end run without installed deps + live API. |
| RAGAS-02 | 01-03-PLAN.md | Pipeline converts DeepEval format → RAGAS SingleTurnSample | ✓ SATISFIED | build_dataset() maps user_query→user_input, actual_answer→response, retrieval_context→retrieved_contexts, expected_answer→reference at lines 263-295. |
| RAGAS-03 | 01-03-PLAN.md | Pipeline computes all 5 standard metrics | ✓ SATISFIED (code) | select_metrics() returns [AnswerRelevancy(), Faithfulness(), ContextPrecision(), ContextRecall(), AnswerCorrectness()] when has_context and has_reference. All 5 imported at module level. |
| RAGAS-04 | 01-03-PLAN.md | Context metrics skipped gracefully if retrieval_context absent | ✓ SATISFIED | select_metrics() line 343-355: UserWarning emitted, contextual metrics skipped, AnswerRelevancy always included. |
| RAGAS-05 | 01-03-PLAN.md | Results saved to eval/results/{timestamp}_ragas/metrics.json in UI-compatible format | ✓ SATISFIED (code) | run_dir = OUTPUT_DIR / f"{ts}_{stem}_ragas" at line 476. save_results() produces all required fields. No actual output file yet. |
| RAGAS-06 | 01-03-PLAN.md | LLM judge configured via OPENAI_API_KEY/OPENAI_BASE_URL from .env | ✓ SATISFIED | load_dotenv at line 39. build_judge() reads env vars. build_embeddings() reads env vars. Same .env file as DeepEval. |
| RAGAS-07 | 01-02-PLAN.md | Pipeline supports custom metrics from eval/custom_metrics/ via autodiscovery | ✓ SATISFIED | discover_custom_metrics() + ExampleCustomMetric scaffold. sys.path fix ensures importability. |
| DEP-01 | 01-01-PLAN.md | ragas, langchain-openai, langchain-core added to requirements.txt | ✓ SATISFIED | All 3 lines present in requirements.txt (lines 18-20). |
| DEP-02 | 01-01-PLAN.md | Dependencies don't break existing deepeval==3.9.3 | ? NEEDS HUMAN | deepeval==3.9.3 line preserved in requirements.txt. ragas/langchain not yet installed — conflict status unverified. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | - | - | - | - |

No TODOs, FIXMEs, placeholders, NotImplementedErrors, hardcoded empty returns, or stub patterns found in any of the 4 key files. Code is substantive and complete.

### Human Verification Required

#### 1. Dependency Installation — pip install without conflicts

**Test:** In the project root, run `.venv/bin/pip install -r requirements.txt` (or create a fresh venv and install). Monitor for version conflict errors.

**Expected:** pip resolves ragas>=0.2.0, langchain-openai>=0.1.0, langchain-core>=0.2.0 successfully alongside the existing locked versions (deepeval==3.9.3, openai==2.30.0, pydantic==2.12.5). No `ERROR: Cannot install ... because these package versions have conflicting dependencies` messages.

**Why human:** Requires live PyPI network access and actual pip resolution. Cannot dry-run without network. Neither .venv nor eval/.venv currently has ragas/langchain installed, so the script is currently unrunnable despite correct code.

#### 2. End-to-End Pipeline Run

**Test:** After installing dependencies, with a valid OPENAI_API_KEY in eval/.env and a reachable RAG API configured in eval/config/eval_config.yaml (add `api:` block with url/method/extractors), run: `python eval/eval_ragas_metrics.py eval/top_k/20260329_171419_exp_top_k_10.json`

**Expected:** Script prints per-record API OK messages, prints metrics list, completes without exception, creates `eval/results/{timestamp}_20260329_171419_exp_top_k_10_ragas/metrics.json` containing rows with `faithfulness_score`, `answer_relevancy_score`, and other `*_score` fields.

**Why human:** Requires live LLM API (OpenAI or OpenRouter key), a running RAG API endpoint, and installed dependencies. The eval/config/eval_config.yaml currently has no `api:` block — the script will fall back to API_URL env var or raise RuntimeError. No _ragas result folder has ever been created.

### Gaps Summary

No hard gaps found in the code artifacts. All 4 required files exist and are substantive. All key functions are implemented correctly. The phase objective is blocked by **one environmental gap**: `ragas`, `langchain-openai`, and `langchain-core` are declared in `requirements.txt` but are not yet installed in the project's virtual environment(s). This means the script cannot currently be executed, and the phase goal ("developer can run the evaluation") cannot be confirmed without installing the dependencies and performing a live run.

The code is correct. The gap is operational: `pip install -r requirements.txt` needs to be run in the project venv, and an end-to-end test against real APIs needs to confirm the output format matches expectations.

---

_Verified: 2026-04-18_
_Verifier: Claude (gsd-verifier)_
