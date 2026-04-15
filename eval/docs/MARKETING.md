# DeepPulse — Marketing Strategy

## Positioning Statement

**DeepPulse** — это pipeline непрерывной оценки качества RAG-систем, который автоматически измеряет релевантность и точность ответов после каждого обновления базы знаний и генерирует детальные отчёты по категориям вопросов.

**Для кого:** AI-команды в компаниях, которые строят продукты на базе RAG и хотят знать, насколько хорошо их система отвечает на вопросы пользователей.

**Отличие от конкурентов:** единственное решение, которое объединяет автоматическую оценку RAG, русскоязычные объяснения судьи, и единый дашборд с безопасностью (DeepThroath) в одном CI/CD-совместимом пайплайне.

---

## Core Value Propositions

### 1. "Числа, а не ощущения"
Команды говорят "ответы стали лучше" после обновления KB. DeepPulse говорит: "Quality Score вырос с 74 до 82. Категория 'юридические вопросы': Faithfulness упала с 0.91 до 0.73."

> *"Quality Score 82/100. 500 диалогов. Faithfulness 0.89 по 8 категориям."*

### 2. "Качество + безопасность в одном окне"
Разрозненные инструменты дают разрозненные данные. DeepPulse и DeepThroath работают на едином дашборде — полная картина AI-системы без переключения контекста.

> *"Security Score 87. Quality Score 82. Всё в норме — можно деплоить."*

### 3. "Объяснения на языке команды"
Судья пишет причины оценок на русском. Не "low coherence score" — а "Ответ не соответствует контексту из базы знаний: модель добавила информацию, которой нет в извлечённых документах."

---

## Messaging по сегментам

### ML Engineering Teams
**Pain:** "Мы не знаем, стало ли лучше после того, как переработали чанкинг."
**Message:** "Запустите DeepPulse до и после. Точное число: насколько изменились AR и Faithfulness по каждой категории."

### Product Management
**Pain:** "Клиенты жалуются на качество ответов, но непонятно, что именно чинить."
**Message:** "Quality Score по категориям показывает точно, где провал. Не 'в целом плохо', а 'категория Х: pass rate 43%'."

### QA / Data Teams
**Pain:** "Проверять 500 диалогов руками после каждого обновления — невозможно."
**Message:** "10 минут машинного времени вместо 2 дней ручной работы. Полный отчёт с примерами плохих ответов и объяснениями."

### Compliance / Legal
**Pain:** "Нужна документация, что AI-система отвечает корректно и только на основе KB."
**Message:** "Faithfulness metric измеряет именно это: процент ответов, подтверждённых извлечёнными документами. Отчёт — готовая основа для аудита."

---

## Go-to-Market Channels

### Phase 1 — Community & Developer (месяцы 1–3)
- Open-source часть как дополнение к DeepThroath
- Статья: "Как мы автоматизировали оценку 500 RAG-диалогов за 10 минут"
- Demo: unified dashboard (безопасность + качество) за 5 минут
- Telegram-каналы по AI/ML разработке на русском

### Phase 2 — Content Marketing (месяцы 3–6)
- Серия статей: "Answer Relevancy vs Faithfulness — в чём разница и зачем обе"
- Case study: "Как мы нашли деградацию Faithfulness в конкретной категории за 10 минут"
- Сравнение судей: GPT-4o mini vs GigaChat — точность оценок RAG на русских диалогах
- YouTube: полный workflow от загрузки JSON до отчёта

### Phase 3 — Enterprise Sales (месяцы 6+)
- Direct outreach в компании с RAG-чат-ботами
- Партнёрство с RAG-платформами (интеграция как eval-слой)
- Freemium → paid: бесплатно self-hosted, платно за SaaS + командные функции

---

## Key Messages для разных каналов

### GitHub README (developer-first)
```
Automated RAG quality evaluation pipeline.
- Answer Relevancy + Faithfulness metrics (DeepEval)
- OpenRouter, OpenAI, GigaChat judges
- YAML judge configuration (mirrors DeepThroath)
- Unified dashboard: quality + security in one place
```

### Telegram / Habr (RU community)
> Обновили базу знаний RAG-чат-бота. Откуда знать, стало ли лучше?
> DeepPulse считает Answer Relevancy и Faithfulness по каждой категории вопросов.
> Quality Score. Разбивка по интентам. Примеры плохих ответов с объяснением на русском.

### Conference pitch (30 секунд)
> "У вас есть RAG-чат-бот. Вы знаете его Quality Score — число от 0 до 100 — с разбивкой по категориям вопросов и конкретными примерами, где модель галлюцинирует? DeepPulse считает это автоматически после каждого обновления базы знаний."

---

## Competitive Differentiation

| Критерий | RAGAS | TruLens | LangSmith | DeepPulse |
|---------|-------|---------|-----------|-----------|
| Answer Relevancy | ✅ | ✅ | ⚠️ | ✅ |
| Faithfulness | ✅ | ✅ | ⚠️ | ✅ |
| GigaChat judge | ❌ | ❌ | ❌ | ✅ |
| Русский язык (причины) | ❌ | ❌ | ❌ | ✅ |
| Checkpoint recovery | ❌ | ❌ | ❌ | ✅ |
| Unified Security+Quality | ❌ | ❌ | ❌ | ✅ |
| YAML judge config | ❌ | ❌ | ❌ | ✅ |
| Без LangChain | ✅ | ⚠️ | ❌ | ✅ |
| Open-source | ✅ | ✅ | ❌ | ✅ |

---

## Pricing Model (будущий)

| Tier | Цена | Возможности |
|------|------|-------------|
| **Open Source** | $0 | Self-hosted, все метрики, community support |
| **Team** | $199/мес | История 90 дней, командный дашборд, брендированные отчёты |
| **Business** | $699/мес | Кастомные метрики, Slack алерты, SSO, приоритетная поддержка |
| **Enterprise** | Custom | On-premise, SaaS + API, compliance пакет |
