# 🛡️ DeepThroath — Отчет о безопасности LLM

**Клиент:** {{ client_name }}
**Дата:** {{ generated_at }}
**Тестируемая модель:** `{{ model_version }}`
**Модель-судья:** `{{ judge_version }}`

---

## Индекс безопасности: {{ security_score }}/100
{% if score_delta is not none %}
> Изменение относительно предыдущего замера: **{{ "+" if score_delta > 0 else "" }}{{ score_delta }} пунктов**
{% endif %}

| Метрика | Значение |
|---------|----------|
| Индекс безопасности | **{{ security_score }}/100** |
| Успешность атак (ASR) | **{{ (overall_asr * 100) | round(1) }}%** |
| Всего тестов | **{{ total_tests }}** |
| Провалено тестов | **{{ total_failed }}** |

---

## 1. Резюме для руководства

Данный отчет содержит результаты автоматизированного тестирования (Red Teaming) языковой модели
на соответствие стандартам безопасности **OWASP LLM Top 10**.
{% if total_failed == 0 %}
✅ **Все тесты пройдены успешно.** Модель успешно отразила все симулированные атаки.
{% elif total_failed <= total_tests // 4 %}
⚠️ **Обнаружены отдельные уязвимости** ({{ total_failed }} из {{ total_tests }} тестов провалено). Требуется устранение.
{% else %}
❌ **Критический уровень уязвимостей** ({{ total_failed }} из {{ total_tests }} тестов провалено). Немедленное вмешательство необходимо.
{% endif %}
{% if top_vulnerabilities %}

### Критические находки

| Уязвимость | OWASP | Критичность | ASR |
|-----------|-------|-------------|-----|
{% for v in top_vulnerabilities %}
| {{ v.vulnerability }} | {{ v.owasp_id }} | {{ v.severity }} | **{{ (v.asr * 100) | round(1) }}%** |
{% endfor %}
{% endif %}

---

## 2. Методология и метрики

- **ASR (Attack Success Rate):** процент атак, приведших к небезопасному ответу модели. Чем ниже, тем лучше.
- **Pass Rate:** процент успешно отражённых атак.
- **Индекс безопасности:** взвешенная оценка, где Critical/High уязвимости имеют больший вес.

| Параметр | Значение |
|----------|----------|
| Целевая модель | `{{ model_version }}` |
| Модель-судья | `{{ judge_version }}` |
| Методы атак | {{ methodology.attacks | join(', ') }} |
| Симуляций на тип | {{ methodology.simulations }} |

---

## 3. Результаты по категориям OWASP LLM Top 10

| ID | Категория | Критичность | Защита | ASR |
|----|-----------|-------------|--------|-----|
{% for owasp_id, rows in owasp_results | groupby('owasp_id') %}
{% set worst = rows | max(attribute='asr') %}
| **{{ worst.owasp_id }}** | {{ worst.owasp_name }} | {{ worst.severity }} | {{ "✅ " ~ ((worst.pass_rate * 100) | round(1)) ~ "%" if worst.pass_rate == 1.0 else ("⚠️ " ~ ((worst.pass_rate * 100) | round(1)) ~ "%" if worst.pass_rate >= 0.5 else "❌ " ~ ((worst.pass_rate * 100) | round(1)) ~ "%") }} | {{ "—" if worst.asr == 0 else ("⚠️ " ~ ((worst.asr * 100) | round(1)) ~ "%" if worst.asr <= 0.5 else "❌ " ~ ((worst.asr * 100) | round(1)) ~ "%") }} |
{% endfor %}

---
{% if evidence_dialogs %}

## 4. Примеры успешных атак (Evidence)

Ниже приведены реальные диалоги, в которых защита модели была обойдена.
{% for ev in evidence_dialogs %}

### [{{ ev.owasp_id }}] {{ ev.vulnerability }} ({{ ev.severity }})

**Ввод атакующего:**
```
{{ ev.dialog.input }}
```

**Ответ модели:**
```
{{ ev.dialog.output }}
```

> ⚠️ **ВЕРДИКТ: НЕБЕЗОПАСНО**

---
{% endfor %}
{% else %}

## 4. Примеры успешных атак (Evidence)

✅ Успешных атак не зафиксировано.

---
{% endif %}
{% if recommendations %}

## 5. Рекомендации по устранению
{% for rec in recommendations %}

### {{ rec.owasp_id }} — {{ rec.vulnerability }} ({{ rec.severity }})

{{ rec.remediation }}
{% endfor %}
{% else %}

## 5. Рекомендации по устранению

✅ Рекомендации не требуются — все уязвимости отражены.
{% endif %}

---

*Сгенерировано платформой DeepThroath LLM Security | Конфиденциально*
