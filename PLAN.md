# DeepThroath v2 (Next.js) — План реализации

## Сравнение: Streamlit (v1) → Next.js (v2)

> Анализ выполнен 2026-04-03. Базовый проект: `RedTeaming DeepThroath/`, цель: `RedTeaming DeepThroath v2/web/`.

---

## ✅ Что уже реализовано в v2

### Безопасность (Red Teaming)
- KPI строка: Security Score, ASR, всего тестов, взломано
- Pie chart (Recharts): pass/fail по общему числу тестов
- Bar chart (Recharts): ASR по категориям OWASP
- Trend chart (Recharts, AreaChart): pass_rate во времени
- Сравнение сканов (delta ASR): лучше чем в v1 — 3 счётчика + таблица delta
- Логи атак: таблица с раскрытием диалогов (до 3 на уязвимость)
- Экспорт Markdown: базовый отчёт (только заголовки + ASR, без Evidence и Recommendations)
- Печать PDF через `window.print()`
- Выбор скана из списка (Select)
- Запуск нового скана из UI (кнопка → `/api/run`)

### Качество RAG (Eval)
- KPI: avg AR, avg FA, total, passed
- Аккордеон детальных записей: вопрос, ответ, expected, judge reasoning, context
- Выбор прогона из списка

---

## ❌ Что отсутствует в v2 (нужно реализовать)

---

### БЛОК 1 — Полный Markdown и PDF отчёт (приоритет: КРИТИЧЕСКИЙ)

**Проблема:** В v1 отчёт (generator.py + report.md шаблон) содержал 5 разделов.
В v2 `ExportActions.tsx` генерирует только базовый Markdown без разделов 4 и 5.

**Полный формат отчёта v1 (report.md):**

```
# 🛡️ DeepThroath — Отчёт о безопасности LLM
Клиент / Дата / Модель / Судья / Security Score / дельта от предыдущего

## 1. Резюме для руководства
   Автотекст: ✅/⚠️/❌ в зависимости от failed/total
   Таблица топ-3 Critical/High уязвимостей

## 2. Методология и метрики
   Список методов атак, типов уязвимостей, симуляций на тип

## 3. Результаты по OWASP LLM Top 10
   Таблица сгруппирована по owasp_id, worst ASR через groupby+max

## 4. Примеры успешных атак (Evidence)  ← ОТСУТСТВУЕТ в v2
   Для каждой Critical/High с ASR > 0: input/output/вердикт судьи

## 5. Рекомендации по устранению        ← ОТСУТСТВУЕТ в v2
   Remediation text из OWASP registry для каждой уязвимости с ASR > 0
```

**Что нужно сделать:**

#### 1.1 Расширить `web/src/lib/owasp.ts`
- Добавить поля `description` и `remediation` для каждой категории LLM01-LLM10
  (источник: `src/red_team/severity.py`, поле `OWASPCategory.remediation`)
- Добавить функцию `calculateSecurityScore(scanData)` — вынести из `page.tsx`
- Добавить функцию `calculateScoreDelta(historyTrend, currentScore)` для дельты
- Добавить функцию `getTopVulnerabilities(scanData, n=3)` — топ Critical/High по ASR
- Добавить функцию `getEvidenceDialogs(scanData)` — первый failed диалог на уязвимость
- Добавить функцию `getRecommendations(scanData)` — remediation per OWASP ID

#### 1.2 Обновить `web/src/components/ExportActions.tsx`
Полная структура Markdown с разделами 1-5, включая:
- Evidence: диалоги из `row.conversations` где `score === 1`
- Recommendations: текст `remediation` из owasp.ts

#### 1.3 PDF через print CSS
Файл: `web/src/app/globals.css`
```css
@media print {
  .no-print { display: none !important; }
  body { background: white !important; color: black !important; }
  .glass-card { background: white !important; border: 1px solid #ccc !important; }
}
```

---

### БЛОК 2 — Логи: фильтры и скачивание (приоритет: ВЫСОКИЙ)

Файл: `web/src/components/LogsTable.tsx`

#### 2.1 Фильтры
```tsx
// Добавить над таблицей
const [filterSeverity, setFilterSeverity] = useState("All");
const [filterOwasp, setFilterOwasp] = useState("All");
const [filterSearch, setFilterSearch] = useState("");
```
- `<Select>` фильтр по Severity (All / Critical / High / Medium / Low)
- `<Select>` фильтр по OWASP ID (All / LLM01 / LLM02 / ...)
- `<Input>` текстовый поиск по vulnerability и attack_type

#### 2.2 Кнопки скачивания
```tsx
const downloadCsv = () => { /* Blob CSV без поля conversations */ }
const downloadJson = () => { /* Blob полный JSON с conversations */ }
```

#### 2.3 Показать все диалоги
Сейчас: `convs.slice(0, 3)`. Добавить `<Button>Показать все ({convs.length})</Button>`.

---

### БЛОК 3 — Eval: 4 графика (приоритет: ВЫСОКИЙ)

Новый файл: `web/src/components/EvalCharts.tsx`

В v1 были 4 Plotly-графика. Аналоги на Recharts:

**3.1 Bar chart: Answer Relevancy по категориям**
```tsx
export function ArByCategoryBar({ metrics }: { metrics: any[] })
// groupBy category → mean(answer_relevancy_score) → BarChart
// Цвет: >= 0.7 зелёный, >= 0.5 жёлтый, < 0.5 красный
```

**3.2 Histogram: распределение AR scores**
```tsx
export function ArDistributionHistogram({ metrics }: { metrics: any[] })
// Бины: 0-0.1, 0.1-0.2, ..., 0.9-1.0
// Подсветить бины < 0.7 красным
```

**3.3 Trend line: Quality Score во времени**
```tsx
export function QualityTrendLine({ allScans }: { allScans: any[] })
// Fetch /api/eval?scanFile=X для каждого скана → LineChart
// Две линии: avgAR и passRate%
```

**3.4 Scatter: Faithfulness vs Relevancy**
```tsx
export function FaithfulnessScatter({ metrics }: { metrics: any[] })
// ScatterChart: x=answer_relevancy_score, y=faithfulness_score
// Только записи где faithfulness_score != null
// Вертикальная и горизонтальная опорные линии на 0.7
```

Подключить в `web/src/app/eval/page.tsx` — добавить вкладки:
`Обзор | По категориям | Тренд | Детали записей`

---

### БЛОК 4 — Eval: фильтр по категории + Markdown экспорт (приоритет: СРЕДНИЙ)

Файл: `web/src/app/eval/page.tsx`

**4.1 Фильтр по категории**
```tsx
const [filterCategory, setFilterCategory] = useState("All");
const categories = [...new Set(data.metrics.map(m => m.category).filter(Boolean))];
```

**4.2 Markdown экспорт (формат DeepPulse)**
```
# DeepPulse — Отчёт о качестве RAG
Прогон / Дата / Судья

## Quality Score: XX/100
| Метрика | Среднее | Pass | Fail | Pass% |

## По категориям
| Категория | Кол-во | AR среднее | AR pass% |

## Детальные результаты (только проваленные, AR < 0.7)
### 🔴 Session X — Category
Вопрос / Ответ / Причина судьи
```

---

### БЛОК 5 — Unified сводная страница (приоритет: СРЕДНИЙ)

Файл: `web/src/app/layout.tsx` + новый `web/src/app/overview/page.tsx`

**Навигация в layout (добавить):**
```tsx
<nav>
  <Link href="/">🔐 Безопасность</Link>
  <Link href="/eval">✅ Качество RAG</Link>
  <Link href="/overview">📊 Сводка</Link>
</nav>
```

**Страница /overview:**
- 4-column KPI: Security Score + Quality Score + Security ASR + Quality Pass Rate
- Два графика рядом: Pie (security pass/fail) + AR bar (quality by category)
- Статус-карточки для каждого раздела со ссылкой-кнопкой

---

### БЛОК 6 — OWASP expanders с описанием и remediation (приоритет: НИЗКИЙ)

Файл: `web/src/app/page.tsx` (вкладка OWASP)

В v1 каждая категория имела Accordion с:
- Описанием риска (description)
- Шагами ремедиации (remediation)

В v2 только строка в списке. После добавления `description` и `remediation` в `owasp.ts`
заменить список на `<Accordion>` с этими полями.

---

### БЛОК 7 — Heatmap по severity (приоритет: НИЗКИЙ)

Файл: `web/src/components/DashboardCharts.tsx`

В v1 был `severity_heatmap()` — матрица severity × vulnerability с цветовым градиентом.
Реализовать через Recharts `<ScatterChart>` или кастомную CSS-таблицу.

---

## Порядок реализации

| # | Блок | Файлы | Оценка |
|---|------|-------|--------|
| 1 | Полный Markdown отчёт (Evidence + Recommendations) | `ExportActions.tsx`, `owasp.ts` | ~3ч |
| 2 | PDF print CSS | `globals.css` | ~1ч |
| 3 | Логи: фильтры + CSV/JSON скачивание + show all dialogs | `LogsTable.tsx` | ~2ч |
| 4 | Eval: 4 графика | `EvalCharts.tsx`, `eval/page.tsx` | ~3ч |
| 5 | Eval: фильтр + Markdown экспорт | `eval/page.tsx` | ~2ч |
| 6 | Unified сводная страница | `layout.tsx`, `overview/page.tsx` | ~2ч |
| 7 | OWASP expanders с описанием | `owasp.ts`, `page.tsx` | ~2ч |
| 8 | Heatmap | `DashboardCharts.tsx` | ~1ч |

**Итого:** ~16 часов реализации.

---

## Справочник: ключевые данные из v1 для переноса

### Security Score формула (generator.py → owasp.ts)
```typescript
export function calculateSecurityScore(scanData: any[]): number {
  let scoreNum = 0, weightSum = 0;
  scanData.forEach(row => {
    const cat = getOwaspCategory(row.vulnerability);
    const weight = SEVERITY_WEIGHTS[cat.severity] || 0.1;
    scoreNum += (1.0 - (row.asr || 0)) * weight;
    weightSum += weight;
  });
  return weightSum > 0 ? Math.round((scoreNum / weightSum) * 100) : 0;
}
```

### Evidence dialogs логика (generator.py `_evidence_dialogs`)
```typescript
export function getEvidenceDialogs(scanData: any[]) {
  return scanData
    .filter(row => row.asr > 0 && ['Critical', 'High'].includes(row.severity))
    .map(row => {
      const convs = typeof row.conversations === 'string'
        ? JSON.parse(row.conversations || '[]') : (row.conversations || []);
      const failed = convs.find((c: any) => c.score === 1);
      return failed ? { ...row, dialog: failed } : null;
    })
    .filter(Boolean);
}
```

### Remediation тексты
Источник: `src/red_team/severity.py`, поле `OWASPCategory.remediation` для LLM01-LLM10.
Текущий `owasp.ts` содержит только `id`, `name`, `severity` — нужно добавить `description` и `remediation`.
