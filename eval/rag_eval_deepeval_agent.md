# RAG Eval — DeepEval Test Agent

## Задача агента

Написать DeepEval-тесты для эндпоинта `POST /api/v1/eval/rag`.
Данные берутся из JSON-датасета. Каждый кейс прогоняется через реальный HTTP-запрос к API,
ответ разбирается и оценивается метриками DeepEval.

---

## Архитектура потока

```
dataset.json
    |
    | читаем каждый test case
    v
[pytest parametrize]
    |
    | POST /api/v1/eval/rag
    |   body: { question, category, session_id? }
    v
[API Response]
    {
      question, category, answer,
      retrieved_chunks: [{content, source}],
      chunks_count
    }
    |
    | собираем LLMTestCase
    v
[DeepEval]
    - AnswerRelevancyMetric    (answer vs question)
    - FaithfulnessMetric       (answer vs retrieved_chunks)
    - ContextualPrecisionMetric (chunks vs expected_output)
    - ContextualRecallMetric   (chunks vs expected_output)
    |
    v
assert_test(test_case, metrics)
```

---

## Интенты (category)

Допустимые значения поля `category` в запросе:

| Значение      | Описание          |
|---------------|-------------------|
| `booking`     | Проживание        |
| `dining`      | Питание           |
| `spa`         | СПА               |
| `kids_complex`| Детский комплекс  |
| `ski_zones`   | Лыжные зоны       |
| `transfers`   | Трансферы         |

Источник: `src/core/constants/intent_types.py` → `IntentType` enum.

Валидация происходит в `EvalRagRequest.validate_category()` (`src/core/schemas/eval.py:34-47`).
Невалидная категория → HTTP 422 от FastAPI ещё до попадания в хендлер.

---

## Схема запроса и ответа

### Request — `POST /api/v1/eval/rag`

```json
{
  "question":   "string — вопрос пользователя (обязательно)",
  "category":   "string — один из 6 интентов (обязательно)",
  "session_id": "UUID   — опционально, для привязки к сессии"
}
```

### Response — `200 OK`

```json
{
  "question":         "string — зеркало вопроса из запроса",
  "category":         "string — зеркало категории",
  "answer":           "string — ответ RAG-пайплайна",
  "retrieved_chunks": [
    {
      "content": "string — текст чанка из Qdrant",
      "source":  "string — источник/имя документа"
    }
  ],
  "chunks_count": 0
}
```

### Коды ошибок

| Код | Причина |
|-----|---------|
| 422 | Невалидный `category` или отсутствует `question` |
| 500 | RAG-пайплайн упал или вернул пустой `answer` |

---

## Формат датасета (dataset.json)

Каждый элемент массива — один тест-кейс.
`expected_output` — эталонный ответ (используется DeepEval для контекстных метрик).

```json
[
  {
    "id": "TC-001",
    "category": "kids_complex",
    "question": "Какие есть семейные развлечения в курорте?",
    "expected_output": "В детском комплексе есть горки, батуты и анимация для детей.",
    "session_id": null
  },
  {
    "id": "TC-002",
    "category": "dining",
    "question": "Какие рестораны работают на курорте?",
    "expected_output": "На курорте работают несколько ресторанов с русской и европейской кухней.",
    "session_id": null
  },
  {
    "id": "TC-003",
    "category": "spa",
    "question": "Что входит в SPA-пакет?",
    "expected_output": "В SPA-пакет входят сауна, бассейн и массаж.",
    "session_id": null
  },
  {
    "id": "TC-004",
    "category": "ski_zones",
    "question": "Какие трассы доступны для начинающих?",
    "expected_output": "Для начинающих есть зелёные трассы с инструктором.",
    "session_id": null
  },
  {
    "id": "TC-005",
    "category": "transfers",
    "question": "Как добраться до курорта из аэропорта?",
    "expected_output": "Трансфер от аэропорта до курорта занимает около 2 часов.",
    "session_id": null
  },
  {
    "id": "TC-006",
    "category": "booking",
    "question": "Можно ли забронировать номер на выходные?",
    "expected_output": "Да, бронирование на выходные доступно через сайт или по телефону.",
    "session_id": null
  },
  {
    "id": "TC-EDGE-001",
    "category": "dining",
    "question": "???",
    "expected_output": "",
    "session_id": null,
    "_note": "edge case: бессмысленный запрос — ожидаем пустой или fallback ответ"
  },
  {
    "id": "TC-EDGE-002",
    "category": "spa",
    "question": "Есть ли у вас квантовая запутанность в меню?",
    "expected_output": "",
    "session_id": null,
    "_note": "edge case: вопрос вне контекста базы — chunks_count должен быть 0 или ответ без галлюцинаций"
  }
]
```

---

## Как агент должен написать тесты

### Структура файлов

```
tests/
└── eval/
    ├── __init__.py
    ├── conftest.py          # httpx клиент, загрузка датасета
    ├── dataset.json         # тест-кейсы выше
    └── test_rag_deepeval.py # сами тесты
```

### conftest.py

```python
import json
import pytest
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"
DATASET_PATH = Path(__file__).parent / "dataset.json"


@pytest.fixture(scope="session")
def dataset() -> list[dict]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30.0)
```

### test_rag_deepeval.py — что агент должен сгенерировать

```python
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
)


def call_eval_rag(client, question: str, category: str, session_id=None) -> dict:
    """
    POST /api/v1/eval/rag и вернуть тело ответа.
    Бросает AssertionError если статус не 200.
    """
    payload = {"question": question, "category": category}
    if session_id:
        payload["session_id"] = session_id

    response = client.post("/api/v1/eval/rag", json=payload)
    assert response.status_code == 200, (
        f"[{category}] '{question}' -> HTTP {response.status_code}: {response.text}"
    )
    return response.json()


# --- Happy path: все 6 интентов ---

@pytest.mark.parametrize("case", [
    c for c in pytest.lazy_fixture("dataset")  # noqa
    if not c["id"].startswith("TC-EDGE")
])
def test_rag_answer_relevancy(http_client, case):
    """Answer Relevancy: ответ релевантен вопросу."""
    data = call_eval_rag(http_client, case["question"], case["category"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=data["answer"],
        expected_output=case["expected_output"],
        retrieval_context=[c["content"] for c in data["retrieved_chunks"]],
    )
    assert_test(test_case, [AnswerRelevancyMetric(threshold=0.7)])


@pytest.mark.parametrize("case", [
    c for c in pytest.lazy_fixture("dataset")
    if not c["id"].startswith("TC-EDGE")
])
def test_rag_faithfulness(http_client, case):
    """Faithfulness: ответ заземлён на retrieved_chunks, не галлюцинирует."""
    data = call_eval_rag(http_client, case["question"], case["category"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=data["answer"],
        retrieval_context=[c["content"] for c in data["retrieved_chunks"]],
    )
    assert_test(test_case, [FaithfulnessMetric(threshold=0.8)])


@pytest.mark.parametrize("case", [
    c for c in pytest.lazy_fixture("dataset")
    if not c["id"].startswith("TC-EDGE")
])
def test_rag_contextual_precision(http_client, case):
    """Contextual Precision: чанки из Qdrant действительно релевантны вопросу."""
    data = call_eval_rag(http_client, case["question"], case["category"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=data["answer"],
        expected_output=case["expected_output"],
        retrieval_context=[c["content"] for c in data["retrieved_chunks"]],
    )
    assert_test(test_case, [ContextualPrecisionMetric(threshold=0.7)])


# --- Структура ответа ---

@pytest.mark.parametrize("case", pytest.lazy_fixture("dataset"))
def test_response_schema(http_client, case):
    """Ответ содержит все поля схемы EvalRagResponse."""
    if case["id"].startswith("TC-EDGE"):
        pytest.skip("edge cases могут вернуть 500 — тестируем отдельно")

    data = call_eval_rag(http_client, case["question"], case["category"])

    assert "question" in data
    assert "category" in data
    assert "answer" in data and data["answer"]
    assert isinstance(data["retrieved_chunks"], list)
    assert data["chunks_count"] == len(data["retrieved_chunks"])
    assert data["category"] == case["category"]


# --- Edge cases ---

def test_invalid_category_returns_422(http_client):
    """Невалидный category → HTTP 422."""
    response = http_client.post(
        "/api/v1/eval/rag",
        json={"question": "тест", "category": "unknown_intent"},
    )
    assert response.status_code == 422


def test_empty_question_returns_error(http_client):
    """Пустой question → либо 422, либо 500 (пайплайн вернёт пустой ответ)."""
    response = http_client.post(
        "/api/v1/eval/rag",
        json={"question": "", "category": "dining"},
    )
    assert response.status_code in (422, 500)


def test_out_of_context_question_no_hallucination(http_client, dataset):
    """Вопрос вне базы: ответ не должен содержать выдуманных фактов."""
    case = next(c for c in dataset if c["id"] == "TC-EDGE-002")
    response = http_client.post(
        "/api/v1/eval/rag",
        json={"question": case["question"], "category": case["category"]},
    )
    if response.status_code == 500:
        pytest.skip("Пайплайн вернул пустой ответ — ожидаемо для out-of-context")

    data = response.json()
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=data["answer"],
        retrieval_context=[c["content"] for c in data["retrieved_chunks"]],
    )
    assert_test(test_case, [FaithfulnessMetric(threshold=0.9)])
```

---

## Зависимости для установки

```bash
pip install deepeval httpx pytest pytest-asyncio
```

Или добавить в `setup.py` extras:

```python
"eval": [
    "deepeval>=0.21.0",
    "httpx>=0.28.0",
]
```

Установка: `pip install -e ".[eval,testing]"`

---

## Запуск

```bash
# запустить только eval-тесты
pytest tests/eval/ -v

# запустить с отчётом DeepEval (Confident AI)
deepeval test run tests/eval/test_rag_deepeval.py

# запустить конкретный интент
pytest tests/eval/ -v -k "kids_complex"

# нагрузить все 6 интентов параллельно
pytest tests/eval/ -v -n 6  # requires pytest-xdist
```

---

## Пороги метрик

| Метрика                 | Порог | Обоснование |
|-------------------------|-------|-------------|
| AnswerRelevancy         | 0.7   | Ответ должен быть по теме вопроса |
| Faithfulness            | 0.8   | Низкая толерантность к галлюцинациям |
| ContextualPrecision     | 0.7   | Чанки из Qdrant должны быть релевантны |
| ContextualRecall        | 0.6   | Допускаем неполный охват (RAG-специфика) |

---

## Что агент делает шаг за шагом

1. Читает `dataset.json` из той же директории что и тесты
2. Для каждого `test_case` делает `POST /api/v1/eval/rag` через `httpx.Client`
3. Из ответа берет: `answer` → `actual_output`, `retrieved_chunks[].content` → `retrieval_context`
4. Из датасета берет: `question` → `input`, `expected_output` → `expected_output`
5. Собирает `LLMTestCase` и прогоняет через `assert_test(test_case, metrics)`
6. Edge-кейсы (`TC-EDGE-*`) тестируются отдельно без DeepEval-метрик (только HTTP-статус и schema)

---

## Что нагружается через один запрос к /api/v1/eval/rag

Один вызов эндпоинта последовательно бьёт по трём системам. Вот полный граф нагрузки:

```
POST /api/v1/eval/rag
        |
        |-- если session_id передан
        |       |
        |       v
        |   [PostgreSQL]
        |   - UserRepository.upsert(eval-rag-user)
        |   - IntentRepository.get_by_key(category)
        |   - SessionRepository.create / get (session lookup)
        |
        v
[RAGIntentService.answer_question()]
        |
        v
[LangGraph RAG pipeline]
        |
        |-- узел retrieval
        |       |
        |       v
        |   [Qdrant]
        |   - vector search по коллекции интента
        |   - top_k чанков (обычно 5-20)
        |   - фильтрация по payload (category/intent)
        |
        |-- узел generation
                |
                v
            [LLM (GigaChat)]
            - prompt = system + retrieved_chunks + question
            - генерация answer
            - structured output / plain text
```

### Таблица: какая система нагружается и чем

| Система    | Что происходит                                      | Когда нагружается           |
|------------|-----------------------------------------------------|-----------------------------|
| PostgreSQL | upsert user, get intent, create/lookup session      | только если передан session_id |
| Qdrant     | vector similarity search, payload filter по интенту | каждый запрос               |
| LLM        | генерация ответа по retrieved_chunks                | каждый запрос               |
| Redis      | LangGraph checkpointer (состояние graph по thread_id) | каждый запрос              |

### Вывод для нагрузочного тестирования

- **Без `session_id`** — нагружаешь только Qdrant + LLM + Redis. PostgreSQL не трогается.
- **С `session_id`** — нагружаешь все 4 системы. Первый запрос с новым UUID создаёт сессию в PG, повторный — только lookup (дешевле).
- **Параллельные запросы с разными `session_id`** — максимальная нагрузка на все системы одновременно.
- **Разные `category`** — разные Qdrant-коллекции / фильтры, можно проверить равномерность нагрузки по интентам.

### Стратегия нагрузки через dataset.json

```
Сценарий A — только RAG (Qdrant + LLM):
  session_id: null во всех кейсах
  цель: измерить latency Qdrant search + LLM generation

Сценарий B — полный стек (все 4 системы):
  session_id: уникальный UUID в каждом кейсе
  цель: нагрузить PG session creation + Qdrant + LLM

Сценарий C — прогрев кэша (Redis checkpointer):
  session_id: один и тот же UUID повторяется
  цель: повторные запросы с тем же thread_id — LangGraph тянет состояние из Redis
```

### Пример нагрузочного скрипта (locust)

```python
from locust import HttpUser, task, between
import json
from pathlib import Path
import uuid

DATASET = json.loads((Path(__file__).parent / "dataset.json").read_text())


class RagEvalUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def eval_no_session(self):
        """Сценарий A: только Qdrant + LLM."""
        case = random.choice(DATASET)
        self.client.post("/api/v1/eval/rag", json={
            "question": case["question"],
            "category": case["category"],
        })

    @task(1)
    def eval_with_session(self):
        """Сценарий B: полный стек включая PG."""
        case = random.choice(DATASET)
        self.client.post("/api/v1/eval/rag", json={
            "question": case["question"],
            "category": case["category"],
            "session_id": str(uuid.uuid4()),
        })
```

```bash
locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5
```

---

## Вариативность датасетов под каждый профиль

Каждый профиль — отдельный JSON-файл. Разница только в `session_id` и структуре вопросов.

---

### dataset_a_rag_only.json — чистый RAG, без истории, без PG

**Цель:** изолированно нагрузить Qdrant + LLM. PostgreSQL не трогается вообще.

**Правило:** `session_id: null` во всех кейсах. Каждый запрос — новый `thread_id` (генерится в роутере через `uuid4()`).

**Что нагружается:** Qdrant (vector search) + LLM (generation) + Redis (новый checkpoint на каждый запрос).

**Что НЕ нагружается:** PostgreSQL.

```json
[
  { "id": "A-001", "category": "dining",       "question": "Какие рестораны работают на курорте?",              "session_id": null },
  { "id": "A-002", "category": "spa",          "question": "Что входит в SPA-пакет?",                          "session_id": null },
  { "id": "A-003", "category": "kids_complex", "question": "Какие развлечения есть для детей?",                 "session_id": null },
  { "id": "A-004", "category": "ski_zones",    "question": "Какие трассы открыты сегодня?",                    "session_id": null },
  { "id": "A-005", "category": "transfers",    "question": "Как добраться до курорта из Москвы?",              "session_id": null },
  { "id": "A-006", "category": "booking",      "question": "Можно ли забронировать номер на одну ночь?",       "session_id": null },
  { "id": "A-007", "category": "dining",       "question": "Есть ли вегетарианское меню?",                     "session_id": null },
  { "id": "A-008", "category": "spa",          "question": "Нужна ли запись на массаж заранее?",               "session_id": null },
  { "id": "A-009", "category": "ski_zones",    "question": "Где взять напрокат лыжи?",                        "session_id": null },
  { "id": "A-010", "category": "booking",      "question": "Какие типы номеров доступны?",                    "session_id": null }
]
```

---

### dataset_b_full_stack.json — полный стек, новая сессия на каждый запрос

**Цель:** нагрузить все 4 системы. Каждый запрос создаёт новую запись в PostgreSQL.

**Правило:** `session_id` — уникальный UUID у каждого кейса (генерить перед прогоном). PG: upsert user + get intent + create session на каждый запрос.

**Что нагружается:** PostgreSQL (write) + Qdrant + LLM + Redis.

**Когда использовать:** стресс-тест на запись в PG и полный E2E.

```json
[
  { "id": "B-001", "category": "dining",       "question": "Какие рестораны работают на курорте?",        "session_id": "11111111-0000-0000-0000-000000000001" },
  { "id": "B-002", "category": "spa",          "question": "Что входит в SPA-пакет?",                    "session_id": "11111111-0000-0000-0000-000000000002" },
  { "id": "B-003", "category": "kids_complex", "question": "Какие развлечения есть для детей?",           "session_id": "11111111-0000-0000-0000-000000000003" },
  { "id": "B-004", "category": "ski_zones",    "question": "Какие трассы открыты сегодня?",              "session_id": "11111111-0000-0000-0000-000000000004" },
  { "id": "B-005", "category": "transfers",    "question": "Как добраться до курорта из Москвы?",        "session_id": "11111111-0000-0000-0000-000000000005" },
  { "id": "B-006", "category": "booking",      "question": "Можно ли забронировать номер на одну ночь?", "session_id": "11111111-0000-0000-0000-000000000006" }
]
```

> Перед прогоном заменить UUID на реальные: `python -c "import uuid,json; ..."`
> или генерить прямо в locust/pytest через `uuid.uuid4()`.

---

### dataset_c_chat_history.json — один чат, история накапливается

**Цель:** нагрузить Redis (растущий checkpoint) и LLM (растущий контекст истории). Проверить деградацию latency по мере роста истории.

**Правило:** все кейсы используют **один и тот же `session_id`**. Вопросы внутри одной категории — связные, как диалог.

**Что нагружается:** Redis (checkpoint растёт) + LLM (prompt растёт с каждым туром) + Qdrant. PG: только первый запрос создаёт сессию, дальше — lookup.

**Что проверяем:** latency запроса №10 vs запроса №1 — если LLM начинает тормозить, история съедает контекстное окно.

```json
[
  { "id": "C-001", "category": "spa", "question": "Что входит в SPA-пакет?",                           "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-002", "category": "spa", "question": "А массаж входит в пакет или оплачивается отдельно?", "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-003", "category": "spa", "question": "Сколько стоит дополнительный сеанс массажа?",        "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-004", "category": "spa", "question": "Нужна ли запись заранее или можно прийти в любое время?", "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-005", "category": "spa", "question": "Есть ли скидки для гостей отеля?",                  "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-006", "category": "spa", "question": "До какого времени работает SPA?",                   "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-007", "category": "spa", "question": "Можно ли взять гостевой браслет для бассейна?",     "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" },
  { "id": "C-008", "category": "spa", "question": "А дети допускаются в бассейн?",                     "session_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" }
]
```

> Кейсы ДОЛЖНЫ выполняться строго последовательно (не параллельно), иначе история перемешается.
> В pytest: без `-n`, в locust: `weight=1` и один виртуальный пользователь.

---

### dataset_d_cross_intent.json — переключение интентов внутри одного чата

**Цель:** проверить изоляцию контекста между интентами. LangGraph использует один `thread_id` но разные Qdrant-коллекции/фильтры. Проверяем что ответ по `spa` не "просачивается" в `ski_zones`.

**Правило:** один `session_id`, категории чередуются намеренно.

```json
[
  { "id": "D-001", "category": "dining",       "question": "Какие рестораны открыты вечером?",     "session_id": "dddddddd-0000-0000-0000-000000000001" },
  { "id": "D-002", "category": "spa",          "question": "Что входит в SPA-пакет?",              "session_id": "dddddddd-0000-0000-0000-000000000001" },
  { "id": "D-003", "category": "ski_zones",    "question": "Какие трассы доступны новичкам?",      "session_id": "dddddddd-0000-0000-0000-000000000001" },
  { "id": "D-004", "category": "dining",       "question": "Есть ли доставка еды в номер?",        "session_id": "dddddddd-0000-0000-0000-000000000001" },
  { "id": "D-005", "category": "kids_complex", "question": "С какого возраста принимают детей?",   "session_id": "dddddddd-0000-0000-0000-000000000001" },
  { "id": "D-006", "category": "transfers",    "question": "Есть ли трансфер до ближайшего города?", "session_id": "dddddddd-0000-0000-0000-000000000001" }
]
```

---

### Сводная таблица датасетов

| Файл                        | session_id       | PG   | Qdrant | LLM | Redis         | Порядок выполнения |
|-----------------------------|------------------|------|--------|-----|---------------|--------------------|
| dataset_a_rag_only.json     | null (нет)       | нет  | да     | да  | новый каждый раз | параллельно OK  |
| dataset_b_full_stack.json   | уникальный UUID  | write| да     | да  | новый каждый раз | параллельно OK  |
| dataset_c_chat_history.json | один UUID        | lookup | да   | да (растёт) | накапливается | строго последовательно |
| dataset_d_cross_intent.json | один UUID        | lookup | да (разные фильтры) | да | накапливается | строго последовательно |
