# Спецификация API DeepThroath

## Обзор

DeepThroath — это универсальная платформа для тестирования LLM, разработанная для работы с **любой RAG-системой, LLM-ассистентом или conversational AI** независимо от деталей реализации. Этот документ определяет API-контракт, который гарантирует, что DeepThroath может оценивать 30 различных проектов с 30 разными endpoint'ами без проблем совместимости.

## Философия дизайна

### Универсальная совместимость
API-спецификация разработана для покрытия максимально широкого спектра RAG-реализаций:
- Ассистенты на базе знаний (поддержка клиентов, документационные боты)
- Внутренние корпоративные RAG-системы (HR, юридические документы, техническая документация)
- Мультимодальные RAG (текст, изображения, PDF)
- Гибридные поисковые системы (векторный + keyword поиск)
- Агентные системы с вызовом инструментов
- Простые Q&A боты
- Сложные многоходовые conversational AI

### Гибкая схема
- **Обязательные поля** — Минимальный набор для базовой оценки (Answer Relevancy)
- **Рекомендуемые поля** — Открывают продвинутые метрики (Faithfulness, Contextual Precision/Recall)
- **Опциональные поля** — Предоставляют расширенный контекст для оценки и отладки

---

## API-контракт

### Формат запроса

DeepThroath будет отправлять запросы к вашему RAG API endpoint, используя следующую структуру:

```json
{
  "question": "Какая у вас политика возврата?",
  "conversation_id": "optional-session-id",
  "user_id": "optional-user-id",
  "metadata": {
    "source": "deepthroath-eval",
    "run_id": "eval-20260417-001"
  }
}
```

#### Поля запроса

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `question` | string | **Да** | Вопрос или промпт пользователя |
| `conversation_id` | string | Нет | ID сессии для многоходовых диалогов |
| `user_id` | string | Нет | Идентификатор пользователя для персонализированных RAG |
| `metadata` | object | Нет | Дополнительный контекст (source, run_id и т.д.) |

**Примечание:** Ваш API должен принимать как минимум поле `question`. Все остальные поля опциональны и могут быть проигнорированы, если они не применимы к вашей системе.

---

### Формат ответа

Ваш RAG API должен возвращать JSON-ответ со следующей структурой:

#### Минимальный ответ (только обязательные поля)

```json
{
  "answer": "Наша политика возврата позволяет вернуть товар в течение 30 дней с момента покупки."
}
```

#### Полный ответ (рекомендуемый)

```json
{
  "answer": "Наша политика возврата позволяет вернуть товар в течение 30 дней с момента покупки. Вы можете запросить возврат через личный кабинет или обратившись в поддержку support@example.com.",

  "retrieval_context": [
    "Политика возврата: Клиенты могут вернуть товары в течение 30 дней с момента покупки для полного возврата средств.",
    "Чтобы запросить возврат, войдите в свой аккаунт и перейдите в Заказы > Запросить возврат.",
    "Свяжитесь с нашей службой поддержки по адресу support@example.com для помощи с возвратами."
  ],

  "metadata": {
    "model": "gpt-4",
    "confidence_score": 0.92,
    "retrieval_method": "hybrid_search",
    "processing_time_ms": 450
  }
}
```

#### Полный ответ (все поля)

```json
{
  "answer": "Наша политика возврата позволяет вернуть товар в течение 30 дней с момента покупки. Вы можете запросить возврат через личный кабинет или обратившись в поддержку support@example.com.",

  "retrieval_context": [
    "Политика возврата: Клиенты могут вернуть товары в течение 30 дней с момента покупки для полного возврата средств.",
    "Чтобы запросить возврат, войдите в свой аккаунт и перейдите в Заказы > Запросить возврат.",
    "Свяжитесь с нашей службой поддержки по адресу support@example.com для помощи с возвратами."
  ],

  "sources": [
    {
      "document_id": "policy-refunds-v2",
      "title": "Политика возврата",
      "url": "https://docs.example.com/policies/refunds",
      "chunk_id": "chunk-42",
      "score": 0.89
    },
    {
      "document_id": "faq-returns",
      "title": "FAQ по возвратам",
      "url": "https://docs.example.com/faq#returns",
      "chunk_id": "chunk-15",
      "score": 0.85
    }
  ],

  "metadata": {
    "model": "gpt-4",
    "confidence_score": 0.92,
    "retrieval_method": "hybrid_search",
    "top_k": 5,
    "rerank_model": "cohere-rerank-v3",
    "processing_time_ms": 450,
    "tokens_used": {
      "prompt": 320,
      "completion": 45,
      "total": 365
    }
  },

  "conversation_id": "session-abc-123",
  "timestamp": "2026-04-17T10:30:00Z"
}
```

---

### Спецификация полей ответа

#### Обязательные поля

| Поле | Тип | Обязательное | Описание | Открывает метрики |
|------|-----|--------------|----------|-------------------|
| `answer` | string | **Да** | Сгенерированный ответ на вопрос пользователя | Answer Relevancy |

**Критично:** Поле `answer` — это единственное абсолютно обязательное поле. Без него DeepThroath не может выполнить никакую оценку.

---

#### Рекомендуемые поля

| Поле | Тип | Обязательное | Описание | Открывает метрики |
|------|-----|--------------|----------|-------------------|
| `retrieval_context` | array[string] | **Рекомендуется** | Список извлеченных текстовых чанков, использованных для генерации ответа | Faithfulness, Contextual Precision, Contextual Recall |

**Почему это важно:**
- Без `retrieval_context` доступна только метрика **Answer Relevancy**
- С `retrieval_context` становятся доступны все **4 ключевые метрики**:
  - Answer Relevancy (AR) — Релевантность ответа
  - Faithfulness (FA) — Обнаружение галлюцинаций
  - Contextual Precision (CP) — Качество ранжирования
  - Contextual Recall (CR) — Полнота извлечения

**Формат:**
```json
"retrieval_context": [
  "Первый извлеченный чанк текста...",
  "Второй извлеченный чанк текста...",
  "Третий извлеченный чанк текста..."
]
```

**Лучшие практики:**
- Включайте 3-10 чанков (top_k результатов из вашего retriever)
- Упорядочивайте чанки по релевантности (самый релевантный первым)
- Каждый чанк должен быть 100-500 токенов для оптимальной оценки
- Включайте только текстовое содержимое, без метаданных

---

#### Опциональные поля (расширенная оценка)

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `sources` | array[object] | Нет | Детальные метаданные об извлеченных документах |
| `metadata` | object | Нет | Дополнительная системная информация (модель, уверенность, время) |
| `conversation_id` | string | Нет | Идентификатор сессии для отслеживания многоходовых диалогов |
| `timestamp` | string (ISO 8601) | Нет | Временная метка генерации ответа |

##### Структура объекта `sources`

```json
"sources": [
  {
    "document_id": "unique-doc-id",
    "title": "Название документа",
    "url": "https://example.com/doc",
    "chunk_id": "chunk-identifier",
    "score": 0.89,
    "page_number": 5,
    "section": "Глава 3: Политики"
  }
]
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | string | Уникальный идентификатор исходного документа |
| `title` | string | Читаемое название документа |
| `url` | string | Ссылка на исходный документ (если доступно) |
| `chunk_id` | string | Идентификатор конкретного чанка внутри документа |
| `score` | float | Оценка релевантности (0.0 - 1.0) |
| `page_number` | integer | Номер страницы в оригинальном документе (для PDF) |
| `section` | string | Заголовок раздела/главы |

**Применение:**
- Отладка качества извлечения
- Предоставление цитат конечным пользователям
- Анализ наиболее часто извлекаемых документов
- Выявление пробелов в базе знаний

##### Структура объекта `metadata`

```json
"metadata": {
  "model": "gpt-4",
  "confidence_score": 0.92,
  "retrieval_method": "hybrid_search",
  "top_k": 5,
  "rerank_model": "cohere-rerank-v3",
  "processing_time_ms": 450,
  "tokens_used": {
    "prompt": 320,
    "completion": 45,
    "total": 365
  },
  "embedding_model": "text-embedding-3-large",
  "vector_db": "pinecone",
  "filters_applied": ["category:support", "language:ru"]
}
```

**Распространенные поля метаданных:**

| Поле | Тип | Описание |
|------|-----|----------|
| `model` | string | LLM-модель, использованная для генерации (например, "gpt-4", "claude-3") |
| `confidence_score` | float | Уверенность модели в ответе (0.0 - 1.0) |
| `retrieval_method` | string | Стратегия поиска ("vector", "keyword", "hybrid_search") |
| `top_k` | integer | Количество извлеченных чанков |
| `rerank_model` | string | Использованная модель ранжирования (если есть) |
| `processing_time_ms` | integer | Общее время обработки в миллисекундах |
| `tokens_used` | object | Детализация потребления токенов |
| `embedding_model` | string | Модель эмбеддингов для извлечения |
| `vector_db` | string | Использованная векторная БД ("pinecone", "weaviate", "qdrant") |
| `filters_applied` | array[string] | Метаданные-фильтры, примененные при извлечении |

---

## Обработка ошибок

Ваш API должен возвращать соответствующие HTTP-коды состояния и сообщения об ошибках:

### Успешный ответ
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "answer": "Ответ на ваш вопрос...",
  "retrieval_context": [...]
}
```

### Ответы с ошибками

#### 400 Bad Request
```json
{
  "error": "invalid_request",
  "message": "Отсутствует обязательное поле: question",
  "details": {
    "field": "question",
    "expected_type": "string"
  }
}
```

#### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "Не удалось извлечь релевантные документы",
  "details": {
    "component": "retriever",
    "trace_id": "abc-123-def"
  }
}
```

#### 503 Service Unavailable
```json
{
  "error": "service_unavailable",
  "message": "Превышен лимит запросов к LLM провайдеру",
  "retry_after": 60
}
```

---

## Соответствие метрик оценки

### Доступные метрики по полям ответа

| Метрика | Необходимые поля | Описание |
|---------|------------------|----------|
| **Answer Relevancy (AR)** | `answer`, `question` | Соответствует ли ответ вопросу? |
| **Faithfulness (FA)** | `answer`, `retrieval_context` | Основан ли ответ на извлеченном контексте? |
| **Contextual Precision (CP)** | `answer`, `retrieval_context`, `question` | Ранжированы ли релевантные чанки выше? |
| **Contextual Recall (CR)** | `retrieval_context`, ground truth | Были ли извлечены все необходимые чанки? |

### Процесс оценки

```
┌─────────────────┐
│ Ваш RAG API     │
│ Возвращает:     │
│ - answer        │ ──────> Answer Relevancy ✓
│                 │
│ + retrieval_    │
│   context       │ ──────> Faithfulness ✓
│                 │         Contextual Precision ✓
│                 │         Contextual Recall ✓
└─────────────────┘
```

**Ключевой вывод:**
- **Минимальная реализация** (только `answer`) → 1 доступная метрика
- **Рекомендуемая реализация** (`answer` + `retrieval_context`) → 4 доступные метрики
- **Полная реализация** (все поля) → 4 метрики + расширенные данные для отладки

---

## Примеры интеграции

### Пример 1: Простой FAQ-бот (минимальный)

**Ваша реализация API:**
```python
@app.post("/api/query")
def query(request: QueryRequest):
    answer = generate_answer(request.question)
    return {"answer": answer}
```

**Оценка DeepThroath:**
- ✓ Answer Relevancy
- ✗ Faithfulness (нет контекста)
- ✗ Contextual Precision (нет контекста)
- ✗ Contextual Recall (нет контекста)

---

### Пример 2: Документационный бот (рекомендуемый)

**Ваша реализация API:**
```python
@app.post("/api/query")
def query(request: QueryRequest):
    # Извлекаем релевантные чанки
    chunks = retriever.search(request.question, top_k=5)

    # Генерируем ответ
    answer = llm.generate(
        question=request.question,
        context=chunks
    )

    return {
        "answer": answer,
        "retrieval_context": [chunk.text for chunk in chunks]
    }
```

**Оценка DeepThroath:**
- ✓ Answer Relevancy
- ✓ Faithfulness
- ✓ Contextual Precision
- ✓ Contextual Recall

---

### Пример 3: Корпоративный RAG (полный)

**Ваша реализация API:**
```python
@app.post("/api/query")
def query(request: QueryRequest):
    start_time = time.time()

    # Извлекаем и переранжируем
    chunks = retriever.search(request.question, top_k=20)
    chunks = reranker.rerank(chunks, request.question, top_k=5)

    # Генерируем ответ
    answer = llm.generate(
        question=request.question,
        context=chunks,
        model="gpt-4"
    )

    processing_time = (time.time() - start_time) * 1000

    return {
        "answer": answer,
        "retrieval_context": [chunk.text for chunk in chunks],
        "sources": [
            {
                "document_id": chunk.metadata.get("doc_id"),
                "title": chunk.metadata.get("title"),
                "url": chunk.metadata.get("url"),
                "score": chunk.score
            }
            for chunk in chunks
        ],
        "metadata": {
            "model": "gpt-4",
            "retrieval_method": "hybrid_search",
            "rerank_model": "cohere-rerank-v3",
            "processing_time_ms": processing_time,
            "top_k": 5
        }
    }
```

**Оценка DeepThroath:**
- ✓ Answer Relevancy
- ✓ Faithfulness
- ✓ Contextual Precision
- ✓ Contextual Recall
- ✓ Расширенные метаданные для отладки
- ✓ Цитаты источников
- ✓ Отслеживание производительности

---

## Поддержка распространенных RAG-архитектур

Гибкая API-спецификация DeepThroath поддерживает все распространенные RAG-паттерны:

### ✓ Базовый RAG
- Векторный поиск → Генерация через LLM
- **Требуемый ответ:** `answer`, `retrieval_context`

### ✓ Продвинутый RAG
- Гибридный поиск (векторный + keyword) → Ранжирование → Генерация
- **Требуемый ответ:** `answer`, `retrieval_context`
- **Рекомендуется:** `sources` со scores, `metadata.rerank_model`

### ✓ Агентный RAG
- Планирование запроса → Многошаговое извлечение → Использование инструментов → Генерация
- **Требуемый ответ:** `answer`
- **Рекомендуется:** `retrieval_context` (агрегация всех извлеченных чанков)
- **Опционально:** `metadata.tools_used`, `metadata.query_plan`

### ✓ Мультимодальный RAG
- Извлечение изображений/PDF → OCR/Vision → Генерация
- **Требуемый ответ:** `answer`
- **Рекомендуется:** `retrieval_context` (текст, извлеченный из изображений/PDF)
- **Опционально:** `sources` с `source_type: "image"` или `"pdf"`

### ✓ Диалоговый RAG
- История диалога → Переписывание запроса → Извлечение → Генерация
- **Требуемый ответ:** `answer`
- **Рекомендуется:** `retrieval_context`, `conversation_id`
- **Опционально:** `metadata.query_rewrite`, `metadata.history_turns`

---

## Тестирование вашей интеграции

### Шаг 1: Тест минимального ответа

```bash
curl -X POST https://your-api.com/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Какая у вас политика возврата?"}'
```

**Ожидаемый ответ:**
```json
{
  "answer": "Наша политика возврата позволяет..."
}
```

✓ DeepThroath может оценить **Answer Relevancy**

---

### Шаг 2: Тест рекомендуемого ответа

```bash
curl -X POST https://your-api.com/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Какая у вас политика возврата?"}'
```

**Ожидаемый ответ:**
```json
{
  "answer": "Наша политика возврата позволяет...",
  "retrieval_context": [
    "Текст чанка 1...",
    "Текст чанка 2...",
    "Текст чанка 3..."
  ]
}
```

✓ DeepThroath может оценить **все 4 метрики**

---

### Шаг 3: Валидация с DeepThroath

1. Откройте дашборд DeepThroath по адресу `http://localhost:3000`
2. Перейдите на вкладку **API Runner**
3. Введите URL вашего endpoint
4. Загрузите тестовый датасет
5. Нажмите **Start Runner**
6. Проверьте результаты:
   - ✓ Все запросы выполнены успешно
   - ✓ Ответы соответствуют ожидаемой схеме
   - ✓ Метрики рассчитаны корректно

---

## Руководство по миграции

### Если у вас уже есть RAG API

#### Сценарий A: Ваш API уже возвращает `answer`
✓ **Вы готовы!** Никаких изменений не требуется для базовой оценки.

**Рекомендуемый следующий шаг:** Добавьте `retrieval_context` для разблокировки всех 4 метрик.

---

#### Сценарий B: Ваш API возвращает другие названия полей

**Ваш текущий ответ:**
```json
{
  "response": "Ответ...",
  "chunks": ["chunk1", "chunk2"]
}
```

**Вариант 1: Добавить endpoint-обертку**
```python
@app.post("/api/deepthroath/query")
def deepthroath_query(request):
    result = your_existing_api(request)
    return {
        "answer": result["response"],
        "retrieval_context": result["chunks"]
    }
```

**Вариант 2: Настроить маппинг полей в DeepThroath**
DeepThroath поддерживает кастомный маппинг полей:
```yaml
field_mapping:
  answer: "response"
  retrieval_context: "chunks"
```

---

#### Сценарий C: Ваш API возвращает чанки как объекты

**Ваш текущий ответ:**
```json
{
  "answer": "Ответ...",
  "chunks": [
    {"text": "chunk1", "score": 0.9},
    {"text": "chunk2", "score": 0.8}
  ]
}
```

**Решение: Преобразовать чанки в строки**
```python
return {
    "answer": answer,
    "retrieval_context": [chunk["text"] for chunk in chunks]
}
```

---

## Лучшие практики

### 1. Всегда включайте `retrieval_context` когда возможно
- Разблокирует все 4 метрики оценки
- Включает обнаружение галлюцинаций
- Обеспечивает видимость для отладки

### 2. Упорядочивайте чанки по релевантности
- Самые релевантные чанки должны идти первыми
- Улучшает оценки Contextual Precision
- Помогает выявить проблемы с ранжированием

### 3. Возвращайте 3-10 чанков
- Слишком мало чанков (< 3): Может пропустить важный контекст
- Слишком много чанков (> 10): Размывает сигнал, увеличивает стоимость оценки
- Оптимальное количество: 5 чанков

### 4. Включайте чистый текст в чанках
- Удаляйте HTML-теги, markdown-форматирование
- Обрезайте избыточные пробелы
- Держите длину чанка 100-500 токенов

### 5. Используйте `sources` для отладки
- Помогает выявить проблемные документы
- Включает оценку на основе цитат
- Поддерживает анализ первопричин

### 6. Добавляйте `metadata` для мониторинга
- Отслеживайте производительность (`processing_time_ms`)
- Мониторьте затраты (`tokens_used`)
- Сравнивайте конфигурации (`model`, `rerank_model`)

---

## Поддержка

По вопросам или проблемам с интеграцией API:
- GitHub Issues: https://github.com/InfernYaCr/DeepThroath/issues
- Документация: http://localhost:3000/faq
- Примеры интеграций: директория `/examples` в репозитории

---

## История версий

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-04-17 | Первоначальная спецификация API |

---

**Последнее обновление:** 17 апреля 2026
**Поддерживается:** Командой DeepThroath
