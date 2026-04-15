# DeepPulse — Technical Architecture

## Overview

DeepPulse is a four-layer analytics pipeline for automated RAG quality evaluation.
Each layer has a single responsibility and communicates through typed interfaces.

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4 — Dashboard (src/dashboard/)                   │
│  Streamlit + Plotly: Quality Score, charts, export      │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — Data (src/data/)                             │
│  eval_storage.py: JSON read, quality_score(), history   │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — Eval Pipeline (eval/eval_rag_metrics.py)     │
│  ThreadPoolExecutor, DeepEval metrics, checkpoint       │
├─────────────────────────────────────────────────────────┤
│  Layer 1 — LLM Judge (OpenRouter / OpenAI / GigaChat)  │
│  AnswerRelevancyMetric + FaithfulnessMetric             │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
config/targets.yaml
config/eval_config.yaml
        │
        ▼
eval/scripts/run_eval.py          ← CLI / CI entry point
        │  --input data.json --judge gpt4o-mini-or
        ▼
eval/eval_rag_metrics.py
  run_eval()
  ThreadPoolExecutor(MAX_WORKERS)
        │
        ├── evaluate_record() × N  ← each thread:
        │       1. build_judge()   ← OpenRouterJudge / GigaChatJudge / OpenAI string
        │       2. AnswerRelevancyMetric(judge, threshold)
        │       3. FaithfulnessMetric(judge, threshold)  ← only if retrieval_context present
        │       4. metric.measure(LLMTestCase)
        │       5. checkpoint_lock → save_checkpoint()
        │
        ▼ list[dict]
  metrics.json + metrics.csv
        │
        ▼
  generate_report() → report.md
        │
        ▼
src/data/eval_storage.py
  list_eval_runs()     ← discover results/ folders
  load_eval_run()      ← metrics.json → pd.DataFrame
  quality_score()      ← mean answer_relevancy × 100
        │
        ▼
src/dashboard/quality_charts.py
  ar_by_category_bar()
  ar_distribution_histogram()
  quality_trend_line()
  faithfulness_vs_relevancy_scatter()
        │
        ▼
src/dashboard/unified_app.py      ← streamlit run
  "✅ Качество RAG" section
```

---

## Module Interfaces

### `eval/eval_rag_metrics.py`

```python
def run_eval(
    input_path: str | Path,
    judge_config: dict,        # {"provider": "openrouter", "model": "...", "name": "..."}
    max_workers: int = 10,
    threshold: float = 0.7,
) -> Path                      # path to run_dir with results

class OpenRouterJudge(DeepEvalBaseLLM):
    # Uses openai.OpenAI with base_url="https://openrouter.ai/api/v1"
    # System prompt instructs Russian-language 'reason' field

class GigaChatJudge(DeepEvalBaseLLM):
    # Creates GigaChat() per call — not thread-safe when shared
    # Same Russian system prompt

def build_judge(verbose: bool = False) -> DeepEvalBaseLLM | str
# Returns judge instance (or OpenAI model name string for built-in DeepEval path)

def evaluate_record(record: dict, judge_config: dict | None, threshold: float) -> dict
# Thread worker: creates own judge + metric instances, returns result dict

def generate_report(results: list[dict], run_dir: Path) -> None
# Writes report.md with format_reason() post-processing
```

### `src/data/eval_storage.py`

```python
EVAL_RESULTS_DIR: Path   # eval/results/ — overridable for tests

def list_eval_runs() -> list[dict]
# Returns sorted list: [{name, path, timestamp, record_count, quality_score}]
# newest first; skips dirs without metrics.json

def load_eval_run(run_path: Path | str) -> pd.DataFrame
# Reads metrics.json → DataFrame

def load_latest_eval() -> pd.DataFrame | None
# Loads newest run

def quality_score(df: pd.DataFrame | None) -> float
# mean(answer_relevancy_score) × 100, rounded to 1 decimal; returns 0.0 on empty/None
```

**Output DataFrame schema:**

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | any | Record identifier |
| `top_k` | int/None | RAG retrieval parameter |
| `category` | str/None | Question category (for grouping) |
| `intent` | str/None | Query intent |
| `user_query` | str | User question |
| `expected_answer` | str/None | Reference answer |
| `actual_answer` | str | Bot response |
| `answer_relevancy_score` | float/None | 0.0–1.0 |
| `answer_relevancy_passed` | bool/None | score >= threshold |
| `answer_relevancy_reason` | str/None | Judge explanation (RU) |
| `faithfulness_score` | float/None | 0.0–1.0; None if no retrieval_context |
| `faithfulness_passed` | bool/None | score >= threshold |
| `faithfulness_reason` | str/None | Judge explanation (RU) |

### `src/dashboard/quality_charts.py`

```python
def ar_by_category_bar(df: pd.DataFrame) -> go.Figure
# Bar chart: average Answer Relevancy per category

def ar_distribution_histogram(df: pd.DataFrame, category: str | None = None) -> go.Figure
# Histogram: distribution of AR scores

def quality_trend_line(runs: list[dict]) -> go.Figure
# Line chart: Quality Score + pass rate over time

def faithfulness_vs_relevancy_scatter(df: pd.DataFrame) -> go.Figure
# Scatter: Faithfulness (y) vs Answer Relevancy (x), colored by category
```

---

## Configuration

### `eval/config/targets.yaml`

Named judge profiles. Each has `name`, `provider`, `model`, `description`, `threshold`.

```yaml
targets:
  - name: gpt4o-mini-or
    provider: openrouter
    model: openai/gpt-4o-mini
    description: "GPT-4o Mini via OpenRouter — recommended"
    threshold: 0.7
  - name: gigachat
    provider: gigachat
    model: GigaChat-Pro
    threshold: 0.7
```

### `eval/config/eval_config.yaml`

```yaml
max_workers: 10
default_judge: gpt4o-mini-or
metrics:
  answer_relevancy: true
  faithfulness: true
output_dir: results
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JUDGE_PROVIDER` | Yes | openrouter / openai / gigachat |
| `JUDGE_MODEL` | Yes | Model name for the provider |
| `OPENROUTER_API_KEY` | For OpenRouter | OpenRouter API key |
| `OPENAI_API_KEY` | For OpenAI | OpenAI API key |
| `GIGACHAT_CREDENTIALS` | For GigaChat | GigaChat Client Secret |

---

## Thread-Safety Design

```
ThreadPoolExecutor
    ├── Thread 1: build_judge() → own judge_1, metric_ar_1, metric_fa_1
    ├── Thread 2: build_judge() → own judge_2, metric_ar_2, metric_fa_2
    └── Thread N: ...

checkpoint_lock = threading.Lock()
    └── all threads → lock → read + append + write checkpoint.json
```

DeepEval metrics store `score` and `reason` as instance attributes — sharing across threads causes data races. Each thread creates fresh instances.

---

## Checkpoint Recovery

```
run_dir = results/{timestamp}_{input_stem}/
    │
    ├─ On start: load_checkpoint() → skip already-done record IDs
    ├─ Per record: save_checkpoint() under lock
    └─ On success: clear_checkpoint() → delete checkpoint.json
```

---

## Reason Post-Processing

DeepEval hardcodes "The score is X because Y" in library code.
format_reason() transforms it for Russian reports:

```
"The score is 0.85 because ответ содержит..."
→ "Оценка 0.85: ответ содержит..."
```

---

## Dependency Graph

```
eval/scripts/run_eval.py
  └── eval/eval_rag_metrics.py
        ├── deepeval (AnswerRelevancyMetric, FaithfulnessMetric, DeepEvalBaseLLM)
        ├── openai (OpenRouter-compatible client)
        └── gigachat

src/dashboard/unified_app.py
  ├── src/data/eval_storage.py
  │     └── eval/results/*.json
  └── src/dashboard/quality_charts.py

src/dashboard/quality_charts.py
  └── plotly
```

---

## File Size Budget

| File | Lines |
|------|-------|
| eval_rag_metrics.py | ~310 |
| eval/scripts/run_eval.py | ~75 |
| src/data/eval_storage.py | ~70 |
| src/dashboard/quality_charts.py | ~100 |
