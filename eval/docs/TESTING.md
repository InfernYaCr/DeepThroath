# Eval — Руководство по тестированию

## Быстрый старт

```bash
# Из корня проекта
python -m pytest tests/test_eval_storage.py tests/test_quality_charts.py -v
```

## Тестовые файлы

| Файл | Что тестирует |
|---|---|
| `tests/test_eval_storage.py` | `src/data/eval_storage.py` — загрузка и парсинг результатов |
| `tests/test_quality_charts.py` | `src/dashboard/quality_charts.py` — построение Plotly графиков |

## Структура тестов eval_storage

### Фикстуры

- `eval_results_dir(tmp_path, monkeypatch)` — перенаправляет `EVAL_RESULTS_DIR` во временную папку
- `sample_metrics` — список из 2 записей с корректными метриками

### Тест-кейсы

| Тест | Что проверяет |
|---|---|
| `test_list_eval_runs_empty_when_no_dir` | Возвращает `[]` если папка не существует |
| `test_list_eval_runs_returns_entries` | Возвращает записи с ожидаемыми ключами |
| `test_list_eval_runs_newest_first` | Сортировка — новые прогоны первыми |
| `test_load_eval_run_returns_dataframe` | Корректно загружает `metrics.json` в DataFrame |
| `test_load_eval_run_empty_json` | Пустой JSON возвращает пустой DataFrame |
| `test_quality_score_empty_returns_zero` | Пустой DataFrame → 0.0 |
| `test_quality_score_none_returns_zero` | `None` → 0.0 |
| `test_quality_score_calculation` | Правильное среднее × 100 |
| `test_quality_score_all_passed` | Корректное значение при всех высоких оценках |
| `test_quality_score_missing_column` | Нет колонки `answer_relevancy_score` → 0.0 |

## Структура тестов quality_charts

### Фикстуры

- `sample_df` — DataFrame с 3 записями (2 категории, смешанные оценки)
- `sample_runs` — список из 3 прогонов для тренд-графика

### Тест-кейсы

| Тест | Что проверяет |
|---|---|
| `test_ar_by_category_bar_not_empty` | График не пустой при наличии данных |
| `test_ar_by_category_bar_empty_df` | Корректная обработка пустого DataFrame |
| `test_ar_by_category_bar_no_category_column` | Работает без колонки category |
| `test_ar_by_category_bar_categories_in_data` | Все категории присутствуют на графике |
| `test_ar_distribution_histogram` | Гистограмма строится без ошибок |
| `test_ar_distribution_histogram_with_category` | Фильтрация по категории работает |
| `test_ar_distribution_histogram_empty_df` | Корректная обработка пустого DataFrame |
| `test_quality_trend_line_empty` | Пустой список → корректный пустой график |
| `test_quality_trend_line_with_data` | График с двумя трейсами (AR + pass rate) |
| `test_quality_trend_line_single_run` | Работает с одним прогоном |
| `test_faithfulness_vs_relevancy_scatter` | Scatter строится при наличии данных |
| `test_faithfulness_vs_relevancy_scatter_no_faithfulness` | Корректно обрабатывает отсутствие FA данных |
| `test_faithfulness_vs_relevancy_scatter_empty_df` | Корректная обработка пустого DataFrame |

## Запуск всех тестов проекта

```bash
python -m pytest tests/ -v
```

## Ручное тестирование pipeline

```bash
# Создать тестовый входной файл
python -c "
import json
data = [
  {
    'session_id': 'test-1',
    'category': 'demo',
    'user_query': 'What is Python?',
    'actual_answer': 'Python is a programming language.',
    'expected_answer': 'Python is a high-level programming language.',
    'retrieval_context': ['Python is a language created by Guido van Rossum.']
  }
]
with open('/tmp/test_input.json', 'w') as f:
    json.dump(data, f)
print('Created /tmp/test_input.json')
"

# Запустить pipeline (требует настроенного .env)
python eval/scripts/run_eval.py --input /tmp/test_input.json --judge gpt4o-mini-or
```

## Добавление тестов

При добавлении нового судьи или функции:

1. Добавьте фикстуру в соответствующий тестовый файл
2. Проверьте граничные случаи: пустые данные, `None` значения, отсутствующие колонки
3. Запустите `python -m pytest tests/ -v` перед коммитом
