# DeepPulse — Roadmap

## Текущее состояние (v1.0)

DeepPulse оценивает качество RAG-систем через Answer Relevancy и Faithfulness.
Интегрирован с DeepThroath в единый unified dashboard.

**Текущие возможности:**
- Answer Relevancy + Faithfulness через DeepEval
- LLM-судьи: OpenRouter (любая модель), OpenAI, GigaChat
- YAML-конфигурация судей (аналогично DeepThroath)
- Checkpoint-восстановление при падении
- 4 Plotly-графика в unified dashboard
- 23 теста с полным покрытием edge cases

---

## Tier 1 — Высокий приоритет (v1.1)

### 1. GitHub Actions CI/CD Workflow

**Почему важно:** Ключевое преимущество перед ручной оценкой — автоматический запуск после каждого обновления KB или промпта.

```yaml
# .github/workflows/eval.yml
on:
  push:
    paths: ['data/questions.json', 'eval/config/**']
  schedule:
    - cron: '0 3 * * 1'
```

Включает:
- Публикацию Quality Score в PR comment
- Upload артефактов (metrics.json, report.md)
- Exit code 1 при деградации ниже порога

---

### 2. Дополнительные метрики RAG

Расширить за Answer Relevancy + Faithfulness:

| Метрика | Что измеряет | Нужен контекст? |
|---------|-------------|-----------------|
| Contextual Precision | Все ли извлечённые чанки релевантны? | Да |
| Contextual Recall | Все ли нужные факты присутствуют в контексте? | Да |
| Hallucination | Добавила ли модель информации, которой нет в KB? | Да |
| Answer Correctness | Насколько ответ соответствует эталонному? | Нет |

YAML-конфигурация в `eval_config.yaml`:
```yaml
metrics:
  answer_relevancy: true
  faithfulness: true
  contextual_precision: false   # включить при наличии retrieval_context
  hallucination: false
```

---

### 3. PDF-отчёт (аналог DeepThroath)

Сейчас: только Markdown. Добавить WeasyPrint PDF с:
- Обложкой (Quality Score, дата, имя клиента)
- Графиком по категориям
- Топ-5 проблемных записей с примерами
- Рекомендациями

---

### 4. Демо-данные (demo mode)

Без настроенного `.env` сейчас нет данных для показа. Добавить:
- `eval/data/demo_questions.json` — 20 примеров диалогов
- Pre-computed `eval/results/demo/metrics.json` — готовые результаты
- Кнопка "Загрузить демо-данные" в unified dashboard

---

### 5. Сравнение прогонов side-by-side

В unified dashboard: выбрать два прогона и увидеть дельту по каждой категории.

```
Прогон A (top_k=5): Quality Score 74 | AR 0.76 | FA 0.69
Прогон B (top_k=10): Quality Score 82 | AR 0.84 | FA 0.79
Дельта: +8 | +0.08 | +0.10 ✅
```

---

## Tier 2 — Средний приоритет (v1.2)

### 6. Поддержка локальных моделей (Ollama)

Для изоляции данных — судья на локальном Ollama:

```yaml
targets:
  - name: ollama-llama
    provider: ollama
    model: llama3.2
    url: http://localhost:11434
```

Нужен `OllamaJudge` класс (аналог из DeepThroath).

---

### 7. Slack / Telegram уведомления о деградации

При падении Quality Score ниже порога — алерт в канал:

```
🔴 DeepPulse Alert
Quality Score упал: 82 → 71 (-11)
Категория с наибольшей деградацией: "Юридические вопросы" (AR: 0.91 → 0.63)
Прогон: 2026-04-02_questions_v3
```

---

### 8. Batch-режим: несколько конфигов за один запуск

Сравнение top_k одной командой:

```bash
python eval/scripts/run_eval.py \
  --input data/questions.json \
  --judge gpt4o-mini-or \
  --batch eval/config/batch_top_k.yaml
```

Файл batch_top_k.yaml:
```yaml
variants:
  - name: top_k_5
    input: data/top_k5.json
  - name: top_k_10
    input: data/top_k10.json
  - name: top_k_20
    input: data/top_k20.json
```

---

### 9. Регрессионные аннотации на тренд-графике

Отмечать на графике: когда обновлялась база знаний, когда менялась модель.

```python
quality_trend_line(runs, annotations=[
    {"date": "2026-03-15", "label": "KB v2.0"},
    {"date": "2026-04-01", "label": "GPT-4o → Haiku"},
])
```

---

### 10. JUnit XML для CI/CD интеграции

Вывод результатов в формате, совместимом с любым CI:

```xml
<testsuite name="DeepPulse" tests="500" failures="89">
  <testcase name="session_42" classname="category.faq">
    <failure>Answer Relevancy: 0.43 (threshold: 0.7)</failure>
  </testcase>
</testsuite>
```

---

## Tier 3 — Долгосрочные улучшения (v2.0+)

### 11. API для интеграции в любой пайплайн

REST API поверх eval pipeline:

```
POST /api/v1/eval/run
{
  "records": [...],
  "judge": "gpt4o-mini-or",
  "threshold": 0.7
}
→ {"run_id": "...", "quality_score": 82.4, "results": [...]}
```

### 12. Кастомные метрики через YAML

```yaml
custom_metrics:
  - name: tone_consistency
    prompt: |
      Rate from 0 to 1 whether the answer maintains a professional tone.
      Query: {query}
      Answer: {answer}
    threshold: 0.8
```

### 13. Continuous monitoring (production)

Не только batch evaluation, но и оценка реальных диалогов из production в реальном времени. Интеграция с logging pipeline через webhook.

### 14. A/B тестирование retrieval-стратегий

Автоматический статистический тест значимости разницы между двумя конфигами:

```
top_k=5 vs top_k=10: p-value 0.003 → разница статистически значима
Рекомендация: top_k=10
```

### 15. Автоматические рекомендации по улучшению

LLM-анализ паттернов проблемных записей:

```
Анализ 89 записей с AR < 0.7:
- 67% содержат технические термины без определений в KB
- 24% — вопросы о процедурах, которые изменились в последнем обновлении
Рекомендация: обновить раздел KB "Процедуры" и добавить глоссарий
```

---

## Приоритизация

| # | Функция | Усилие | Ценность | Приоритет |
|---|---------|--------|----------|-----------|
| 1 | GitHub Actions | Низкое | Высокая | 🔴 Срочно |
| 2 | Дополнительные метрики | Среднее | Высокая | 🔴 Срочно |
| 3 | PDF-отчёт | Среднее | Высокая | 🟡 Скоро |
| 4 | Демо-данные | Низкое | Средняя | 🟡 Скоро |
| 5 | Side-by-side сравнение | Среднее | Высокая | 🟡 Скоро |
| 6 | Ollama | Низкое | Средняя | 🟢 Планово |
| 7 | Slack алерты | Среднее | Средняя | 🟢 Планово |
| 8 | Batch-режим | Среднее | Средняя | 🟢 Планово |
| 9 | Регрессионные аннотации | Низкое | Средняя | 🟢 Планово |
| 10 | JUnit XML | Низкое | Средняя | 🟢 Планово |
