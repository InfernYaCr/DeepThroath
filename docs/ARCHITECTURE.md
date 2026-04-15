# DeepThroath — Technical Architecture

## Overview

DeepThroath is a five-layer analytics platform for automated LLM security testing. Each layer has a single responsibility and communicates through typed interfaces.

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5 — Report Generation  (src/reports/)            │
│  Jinja2 HTML + WeasyPrint PDF + Security Score          │
├─────────────────────────────────────────────────────────┤
│  Layer 4 — Dashboard (src/dashboard/)                   │
│  Streamlit + Plotly: KPI, charts, OWASP expanders, PDF  │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — Data (src/data/)                             │
│  Transformer + Parquet storage + history versioning     │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — Red Team (src/red_team/)                     │
│  DeepTeam runner, async callbacks, OWASP registry       │
├─────────────────────────────────────────────────────────┤
│  Layer 1 — Target LLM (Anthropic / OpenRouter / any)   │
│  Model under test + LLM-as-a-Judge (same or different)  │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
config/targets.yaml
config/attack_config.yaml
        │
        ▼
scripts/run_redteam.py          ← CLI / CI entry point
        │  --target qwen-7b --judge gemini-flash
        ▼
src/red_team/runner.py
  create_openrouter_callback()  ← wraps target LLM (async)
  run_red_team()
        │  simulator_model = evaluation_model = judge
        ▼
deepteam.red_team()             ← generates adversarial inputs
  attacks: PromptInjection, Roleplay, CrescendoJailbreaking, LinearJailbreaking
  vulnerabilities: 6 categories (PromptLeakage, PIILeakage, ...)
  judge: LLM-as-a-Judge → binary score (0=safe / 1=unsafe)
  ignore_errors=True            ← ModelRefusalError handled gracefully
        │
        ▼ RiskAssessment object
src/data/transformer.py
  transform_risk_assessment()   ← reads .overview.vulnerability_type_results
                                   adds OWASP fields, ASR, severity, judge_version
        │
        ▼ pd.DataFrame
src/data/storage.py
  save_results()                ← results/latest.parquet
                                ← results/history/{ts}.parquet
        │
        ▼
src/dashboard/app.py            ← streamlit run src/dashboard/app.py
  load_latest() + load_history()
  charts: pie, bar, trend, heatmap (Plotly, локализация RU)
  OWASP expanders with remediation steps
  PDF/HTML export button
        │
        ▼
src/reports/generator.py
  build_report_context()        ← Security Score, top vulns, evidence dialogs
src/reports/pdf_export.py
  render_html_report()          ← Jinja2 → HTML
  export_pdf()                  ← HTML → PDF via WeasyPrint
```

---

## Module Interfaces

### `src/red_team/severity.py`

```python
class Severity(str, Enum): CRITICAL | HIGH | MEDIUM | LOW

@dataclass(frozen=True)
class OWASPCategory:
    id: str           # LLM01..LLM10
    name: str         # локализованное название (RU)
    severity: Severity
    description: str  # описание риска (RU)
    remediation: str  # шаги исправления (RU)

OWASP_REGISTRY: dict[str, OWASPCategory]
# Keys: deepteam vulnerability class names (PromptLeakage, Toxicity, ...)
# Smart matching: "ToxicityType.PROFANITY" → strips suffix → "Toxicity"

SEVERITY_WEIGHTS: dict[str, float]  # Critical=0.40, High=0.30, Medium=0.20, Low=0.10
SEVERITY_COLORS: dict[str, str]     # CSS hex colors per severity
SEVERITY_BADGE: dict[str, str]      # emoji badges per severity

def get_owasp_category(vulnerability_name: str) -> OWASPCategory
# Handles composite names like "ToxicityType.PROFANITY" → "Toxicity"
```

### `src/red_team/attacks.py`

```python
@dataclass
class AttackConfig:
    name: str
    attack_class: str       # dotted import path
    params: dict[str, Any]
    enabled: bool

@dataclass
class VulnerabilityConfig:
    name: str
    vulnerability_class: str
    params: dict[str, Any]
    enabled: bool

DEFAULT_ATTACKS: list[AttackConfig]        # 4 attacks (2 single-turn, 2 multi-turn)
DEFAULT_VULNERABILITIES: list[VulnerabilityConfig]  # 6 vulnerability types

def build_attacks(configs: list[AttackConfig]) -> list[Any]
def build_vulnerabilities(configs: list[VulnerabilityConfig]) -> list[Any]
```

### `src/red_team/runner.py`

```python
def create_anthropic_callback(
    model: str,
    system_prompt: str,
    api_key: str | None = None
) -> Callable  # async: (str, list[RTTurn] | None) -> RTTurn

def create_openrouter_callback(
    model: str,
    system_prompt: str,
    api_key: str | None = None,
    site_url: str | None = None,
    site_name: str | None = None,
) -> Callable  # async: (str, list[RTTurn] | None) -> RTTurn

def run_red_team(
    model_callback: Callable,
    attack_configs: list[AttackConfig] | None = None,
    vulnerability_configs: list[VulnerabilityConfig] | None = None,
    attacks_per_vulnerability_type: int = 1,
    evaluation_model: DeepEvalBaseLLM | None = None,
) -> RiskAssessment
# Note: red_team() is SYNCHRONOUS. evaluation_model also used as simulator_model.

def run(
    model: str,
    system_prompt: str,
    attacks_per_vulnerability_type: int = 1,
    provider: str = "anthropic",
    api_key: str | None = None,
    judge_preset: str | None = None,
) -> RiskAssessment
```

### `src/red_team/judges.py`

```python
class OpenRouterJudge(DeepEvalBaseLLM):
    # Uses openai.OpenAI / AsyncOpenAI with OpenRouter base_url

class OllamaJudge(DeepEvalBaseLLM):
    # Uses local Ollama server at http://localhost:11434

JUDGE_PRESETS: dict[str, dict] = {
    "gemini-flash": {"provider": "openrouter", "model": "google/gemini-2.0-flash-001"},
    "gpt-4o-mini":  {"provider": "openai",     "model": "gpt-4o-mini"},
    "llama3-70b":   {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct"},
    "haiku":        {"provider": "anthropic",  "model": "claude-haiku-4-5-20251001"},
    "ollama-llama": {"provider": "ollama",     "model": "llama3.2"},
    # ...
}

def build_judge(provider, model, api_key, ollama_url) -> DeepEvalBaseLLM | None
def build_judge_from_preset(preset: str) -> DeepEvalBaseLLM | None
```

### `src/data/transformer.py`

```python
def transform_risk_assessment(
    risk_assessment: Any,    # deepteam.RiskAssessment
    model_version: str,
    judge_version: str = "N/A",
    session_id: str | None = None,
) -> pd.DataFrame
```

**Output DataFrame schema:**

| Column | Type | Description |
|--------|------|-------------|
| `vulnerability` | str | deepteam class name (e.g. "PromptLeakage") |
| `owasp_id` | str | LLM01–LLM10 |
| `owasp_name` | str | Human-readable category (RU) |
| `severity` | str | Critical / High / Medium / Low |
| `pass_rate` | float | 0.0–1.0 |
| `asr` | float | 1 – pass_rate |
| `passed` | int | Tests passed |
| `failed` | int | Tests failed |
| `errored` | int | Tests errored (ignore_errors=True) |
| `total` | int | passed + failed |
| `attack_type` | str | Attack class names (comma-separated) |
| `model_version` | str | Target model identifier |
| `judge_version` | str | Judge model identifier |
| `session_id` | str | Optional session tag |
| `timestamp` | str | ISO 8601 UTC |
| `conversations` | str | JSON array of {input, output, score, reason, attack_method, error} |

### `src/data/storage.py`

```python
def save_results(df: pd.DataFrame) -> Path
def load_latest() -> pd.DataFrame | None
def load_history() -> pd.DataFrame          # all scans concatenated
```

### `src/reports/generator.py`

```python
def calculate_security_score(df: pd.DataFrame) -> float   # 0–100
def build_report_context(
    df: pd.DataFrame,
    history_df: pd.DataFrame,
    client_name: str = "Client"
) -> dict[str, Any]
```

---

## Security Score Formula

```
score = Σ(pass_rate_i × weight_i) / Σ(weight_i) × 100

where weight = { Critical: 0.40, High: 0.30, Medium: 0.20, Low: 0.10 }
```

---

## Key Design Decisions

### Async Callbacks
deepteam's `red_team()` runs in `async_mode=True` by default and wraps the `model_callback` via `get_async_model_callback`. The callback **must** be `async def` and use async HTTP clients (`AsyncAnthropic`, `AsyncOpenAI`). A sync callback causes `TypeError: object RTTurn can't be used in 'await' expression`.

### Simulator = Judge
deepteam requires a `simulator_model` (generates attack prompts) and an `evaluation_model` (judges responses). Both default to `gpt-4o-mini` via `OPENAI_API_KEY`. We pass the same custom judge for both to avoid dependency on OpenAI keys.

### RiskAssessment API
deepteam 1.0.6 `RiskAssessment` has no `to_df()` method. Data is extracted by iterating:
- `risk_assessment.overview.vulnerability_type_results` → `VulnerabilityTypeResult`
- `risk_assessment.test_cases` → `RTTestCase`

---

## Configuration

### `config/targets.yaml`
Named target profiles: `default` (Claude Haiku), `qwen-7b`, `qwen-72b`, `qwen-custom`. Each has `provider`, `model`, and `system_prompt`.

### `config/attack_config.yaml`
Controls `attacks_per_vulnerability_type`, `asr_threshold`, `judge_preset`, and lists of enabled attacks/vulnerabilities.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | For Anthropic targets | — | Anthropic API key |
| `OPENROUTER_API_KEY` | For OpenRouter targets/judge | — | OpenRouter API key |
| `OPENAI_API_KEY` | For OpenAI judge | — | OpenAI API key |
| `ASR_THRESHOLD` | No | 0.20 | CI failure threshold |
| `RESULTS_DIR` | No | ./results | Results output directory |

---

## Dependency Graph

```
scripts/run_redteam.py
  └── src/red_team/runner.py
        ├── src/red_team/attacks.py
        ├── src/red_team/judges.py
        └── deepteam (external, ==1.0.6)
  └── src/data/transformer.py
        └── src/red_team/severity.py
  └── src/data/storage.py

src/dashboard/app.py
  ├── src/data/storage.py
  ├── src/dashboard/charts.py
  │     └── src/red_team/severity.py
  ├── src/dashboard/logs_table.py
  ├── src/reports/generator.py
  │     └── src/red_team/severity.py
  └── src/reports/pdf_export.py
        └── src/reports/templates/
```

---

## File Size Budget

All source files kept under 500 lines per CLAUDE.md constraints:

| File | Lines |
|------|-------|
| severity.py | ~185 |
| attacks.py | ~80 |
| runner.py | ~135 |
| judges.py | ~155 |
| transformer.py | ~70 |
| storage.py | ~50 |
| generator.py | ~100 |
| pdf_export.py | ~28 |
| charts.py | ~87 |
| logs_table.py | ~75 |
| app.py | ~145 |
