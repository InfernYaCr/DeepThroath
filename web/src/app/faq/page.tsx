'use client'

import { useState } from 'react'

type FAQItem = {
  question: string
  answer: string | string[]
}

type FAQSection = {
  title: string
  icon: React.ReactNode
  items: FAQItem[]
}

export default function FAQPage() {
  const [openIndex, setOpenIndex] = useState<string | null>(null)

  const toggleFAQ = (index: string) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  const faqSections: FAQSection[] = [
    {
      title: 'Общие вопросы',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      items: [
        {
          question: 'Что такое DeepThroath?',
          answer: [
            'DeepThroath — это платформа для тестирования безопасности и качества LLM-систем.',
            'Платформа объединяет три ключевых инструмента:',
            '• Red Teaming — тестирование безопасности и устойчивости к атакам',
            '• Evaluate RAG — оценка качества RAG-систем',
            '• API Runner — универсальный инструмент для тестирования любых LLM API'
          ]
        },
        {
          question: 'Для кого предназначен DeepThroath?',
          answer: [
            'DeepThroath создан для команд, работающих с LLM:',
            '• Инженеры по ML/AI — для тестирования и оценки моделей',
            '• DevOps и QA — для автоматизированного тестирования',
            '• Security-специалисты — для проверки безопасности LLM',
            '• Product-менеджеры — для мониторинга качества продукта'
          ]
        },
        {
          question: 'Какие преимущества API-first подхода?',
          answer: [
            'API-first архитектура позволяет:',
            '• Интеграцию с любыми LLM-провайдерами (OpenAI, Anthropic, локальные модели)',
            '• Единый интерфейс для всех типов тестирования',
            '• Простое подключение внутренних корпоративных API',
            '• Гибкую настройку под специфику проекта'
          ]
        }
      ]
    },
    {
      title: 'Red Teaming',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      items: [
        {
          question: 'Что такое Red Teaming для LLM?',
          answer: [
            'Red Teaming — это процесс проактивного тестирования LLM на устойчивость к атакам.',
            'Включает проверку на:',
            '• Prompt injection — инъекции в промпты',
            '• Jailbreaking — обход системных ограничений',
            '• Data leakage — утечку конфиденциальных данных',
            '• Adversarial attacks — состязательные атаки',
            '• Bias detection — выявление предвзятости'
          ]
        },
        {
          question: 'Как работает Red Teaming в DeepThroath?',
          answer: [
            '1. Выбор категории атаки (injection, jailbreak, toxicity и т.д.)',
            '2. Настройка параметров тестирования (количество запросов, severity level)',
            '3. Автоматическая генерация adversarial промптов',
            '4. Отправка запросов к вашему API',
            '5. Анализ ответов и классификация уязвимостей',
            '6. Формирование отчёта с рекомендациями'
          ]
        },
        {
          question: 'Какие типы атак поддерживаются?',
          answer: [
            'Текущая версия включает:',
            '• Prompt Injection — инъекции команд в промпт',
            '• Jailbreak — попытки обхода этических ограничений',
            '• PII Extraction — извлечение персональных данных',
            '• Toxicity Testing — проверка на генерацию токсичного контента',
            '• Context Manipulation — манипуляции с контекстом',
            'Планируется добавление новых векторов атак.'
          ]
        },
        {
          question: 'Как интерпретировать результаты Red Teaming?',
          answer: [
            'Результаты включают:',
            '• Severity Score (0-100) — общая оценка уязвимости',
            '• Success Rate — процент успешных атак',
            '• Categorized Failures — группировка уязвимостей по типам',
            '• Attack Vectors — конкретные промпты, вызвавшие проблемы',
            '• Recommendations — рекомендации по усилению защиты'
          ]
        }
      ]
    },
    {
      title: 'Evaluate RAG',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      items: [
        {
          question: 'Что такое RAG и зачем его оценивать?',
          answer: [
            'RAG (Retrieval-Augmented Generation) — архитектура, где LLM использует внешние знания из базы данных.',
            'Оценка RAG критична, потому что:',
            '• Качество ответов зависит от релевантности найденных документов',
            '• Неправильный retrieval приводит к галлюцинациям',
            '• Важно измерять точность, полноту и релевантность',
            '• Необходим мониторинг качества в продакшене'
          ]
        },
        {
          question: 'Какие метрики используются для оценки RAG?',
          answer: [
            'DeepThroath оценивает RAG по следующим метрикам:',
            '• Context Relevance — релевантность извлечённых документов к вопросу',
            '• Answer Relevance — релевантность ответа к вопросу',
            '• Faithfulness — соответствие ответа контексту (отсутствие галлюцинаций)',
            '• Context Precision — точность ранжирования документов',
            '• Context Recall — полнота извлечения релевантной информации',
            '• Answer Correctness — корректность итогового ответа'
          ]
        },
        {
          question: 'Как подготовить датасет для оценки RAG?',
          answer: [
            'Датасет должен содержать:',
            '1. Questions — реальные вопросы пользователей',
            '2. Ground Truth Answers (опционально) — эталонные ответы',
            '3. Expected Context (опционально) — ожидаемые документы',
            'Форматы:',
            '• JSON: [{"question": "...", "ground_truth": "...", "context": "..."}]',
            '• CSV: question,ground_truth,expected_context',
            'Рекомендуется минимум 50-100 примеров для статистически значимых результатов.'
          ]
        },
        {
          question: 'Можно ли использовать Evaluate RAG для A/B тестирования?',
          answer: [
            'Да! Evaluate RAG идеален для A/B тестирования:',
            '• Сравнение разных embedding моделей',
            '• Тестирование различных retrieval стратегий',
            '• Оценка влияния chunk size и overlap',
            '• Сравнение векторных БД (Pinecone vs Qdrant vs Weaviate)',
            'Запустите оценку для каждой версии и сравните метрики.'
          ]
        }
      ]
    },
    {
      title: 'API Runner',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      items: [
        {
          question: 'Что такое API Runner?',
          answer: [
            'API Runner — универсальный инструмент для тестирования любых LLM API.',
            'Основные возможности:',
            '• Загрузка датасетов (CSV, JSON, TXT)',
            '• Пакетная отправка запросов к API',
            '• Мониторинг прогресса в реальном времени',
            '• Сбор метрик (latency, tokens, errors)',
            '• Экспорт результатов для анализа'
          ]
        },
        {
          question: 'Какие API поддерживаются?',
          answer: [
            'API Runner работает с любыми HTTP API, включая:',
            '• OpenAI API (GPT-4, GPT-3.5)',
            '• Anthropic Claude API',
            '• Google Gemini API',
            '• Hugging Face Inference API',
            '• Локальные модели (Ollama, vLLM, LocalAI)',
            '• Кастомные корпоративные API',
            'Достаточно указать endpoint и формат запроса.'
          ]
        },
        {
          question: 'Как работает пакетная обработка?',
          answer: [
            '1. Загружаете датасет (файл с промптами/вопросами)',
            '2. Настраиваете параметры:',
            '   • API endpoint',
            '   • Headers (API ключи)',
            '   • Request body template',
            '   • Concurrency (количество параллельных запросов)',
            '3. Запускаете обработку',
            '4. Система отправляет запросы партиями',
            '5. Собирает ответы и метрики',
            '6. Формирует итоговый отчёт'
          ]
        },
        {
          question: 'Как настроить rate limiting?',
          answer: [
            'API Runner поддерживает гибкую настройку лимитов:',
            '• Requests per second (RPS) — ограничение на скорость отправки',
            '• Concurrency — максимум параллельных запросов',
            '• Batch size — размер пакета',
            '• Retry strategy — стратегия повторных попыток при ошибках',
            'Это защищает от превышения квот провайдера и rate limit ошибок.'
          ]
        },
        {
          question: 'Какие метрики собирает API Runner?',
          answer: [
            'Для каждого запроса собираются:',
            '• Latency — время ответа (ms)',
            '• Token usage — использованные токены (prompt + completion)',
            '• Cost estimation — примерная стоимость (на основе тарифов)',
            '• HTTP status — статус ответа',
            '• Error rate — процент ошибок',
            'Агрегированная статистика:',
            '• p50, p95, p99 latency',
            '• Throughput (requests/sec)',
            '• Total cost',
            '• Success rate'
          ]
        }
      ]
    },
    {
      title: 'Интеграция и развёртывание',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      items: [
        {
          question: 'Как развернуть DeepThroath?',
          answer: [
            'DeepThroath состоит из двух компонентов:',
            '1. Frontend (Next.js):',
            '   • npm install && npm run dev',
            '   • Или Docker: docker build -t deepthroath-web .',
            '2. Backend (FastAPI):',
            '   • pip install -r requirements.txt',
            '   • uvicorn app:app --reload',
            'Для продакшена рекомендуется:',
            '• Docker Compose для оркестрации',
            '• Nginx как reverse proxy',
            '• PostgreSQL для хранения результатов (опционально)'
          ]
        },
        {
          question: 'Как подключить собственный API?',
          answer: [
            'В API Runner:',
            '1. Укажите ваш endpoint URL',
            '2. Добавьте необходимые headers (API keys, auth tokens)',
            '3. Настройте request body template:',
            '   {',
            '     "model": "your-model",',
            '     "messages": [{"role": "user", "content": "{{prompt}}"}]',
            '   }',
            '4. Используйте {{prompt}} как плейсхолдер для вопросов из датасета',
            '5. Запустите тест'
          ]
        },
        {
          question: 'Поддерживается ли CI/CD интеграция?',
          answer: [
            'Да! DeepThroath можно интегрировать в CI/CD:',
            '• CLI режим для запуска тестов в пайплайнах',
            '• REST API для автоматизации',
            '• Webhooks для нотификаций',
            '• Экспорт результатов в JSON/CSV',
            'Пример GitHub Actions:',
            '- name: Run Red Team Tests',
            '  run: deepthroath redteam --config config.yml --fail-on-severity high'
          ]
        },
        {
          question: 'Как хранятся результаты тестов?',
          answer: [
            'Результаты могут храниться:',
            '• Локально — в файловой системе (JSON/CSV)',
            '• PostgreSQL — для long-term хранения и аналитики',
            '• S3-compatible storage — для облачного развёртывания',
            '• Встроенная история — последние 100 запусков в UI',
            'Конфигурируется через переменные окружения или config файл.'
          ]
        }
      ]
    },
    {
      title: 'Безопасность и приватность',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      items: [
        {
          question: 'Безопасно ли отправлять данные через DeepThroath?',
          answer: [
            'DeepThroath не хранит ваши API ключи и промпты на внешних серверах:',
            '• Все запросы идут напрямую с вашего инстанса к вашему API',
            '• API ключи хранятся только в вашем .env или памяти браузера',
            '• Нет телеметрии или отправки данных третьим лицам',
            '• Self-hosted развёртывание полностью под вашим контролем'
          ]
        },
        {
          question: 'Как защитить API ключи?',
          answer: [
            'Рекомендации по безопасности:',
            '• Используйте .env файлы (не коммитьте в Git)',
            '• Настройте RBAC если развёртываете для команды',
            '• Используйте ротацию ключей',
            '• Ограничьте scope API ключей (read-only где возможно)',
            '• Используйте secrets management (Vault, AWS Secrets Manager)'
          ]
        },
        {
          question: 'Можно ли использовать DeepThroath с конфиденциальными данными?',
          answer: [
            'Да, при условии self-hosted развёртывания:',
            '• Разверните на своей инфраструктуре (on-premise или private cloud)',
            '• Используйте VPN/private network для изоляции',
            '• Включите шифрование at-rest и in-transit',
            '• Настройте audit logging',
            '• Следуйте вашей корпоративной security policy'
          ]
        }
      ]
    }
  ]

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-[#181e25] mb-4" style={{ fontFamily: "var(--font-outfit, Outfit)" }}>
          FAQ & Документация
        </h1>
        <p className="text-lg text-[#45515e]">
          Подробные ответы на частые вопросы о DeepThroath — платформе для тестирования безопасности и качества LLM-систем
        </p>
      </div>

      <div className="space-y-8">
        {faqSections.map((section, sectionIdx) => (
          <div key={sectionIdx} className="bg-white border border-[#e5e7eb] rounded-xl overflow-hidden">
            <div className="bg-gradient-to-r from-[#1456f0]/5 to-[#1456f0]/10 px-6 py-4 border-b border-[#e5e7eb]">
              <div className="flex items-center gap-3">
                <div className="text-[#1456f0]">
                  {section.icon}
                </div>
                <h2 className="text-2xl font-semibold text-[#181e25]" style={{ fontFamily: "var(--font-outfit, Outfit)" }}>
                  {section.title}
                </h2>
              </div>
            </div>

            <div className="divide-y divide-[#e5e7eb]">
              {section.items.map((item, itemIdx) => {
                const itemId = `${sectionIdx}-${itemIdx}`
                const isOpen = openIndex === itemId

                return (
                  <div key={itemIdx}>
                    <button
                      onClick={() => toggleFAQ(itemId)}
                      className="w-full px-6 py-4 flex items-start justify-between gap-4 hover:bg-[#f8f9fa] transition-colors text-left"
                    >
                      <span className="text-[#181e25] font-medium text-lg flex-1">
                        {item.question}
                      </span>
                      <svg
                        className={`w-5 h-5 text-[#1456f0] flex-shrink-0 transition-transform mt-1 ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {isOpen && (
                      <div className="px-6 pb-6 pt-2">
                        <div className="text-[#45515e] leading-relaxed space-y-2">
                          {Array.isArray(item.answer) ? (
                            item.answer.map((line, lineIdx) => (
                              <p key={lineIdx} className={line.startsWith('•') || line.startsWith('-') ? 'ml-4' : ''}>
                                {line}
                              </p>
                            ))
                          ) : (
                            <p>{item.answer}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 bg-gradient-to-r from-[#1456f0]/10 to-[#7c3aed]/10 border border-[#1456f0]/20 rounded-xl p-8">
        <h3 className="text-2xl font-semibold text-[#181e25] mb-4" style={{ fontFamily: "var(--font-outfit, Outfit)" }}>
          Не нашли ответ?
        </h3>
        <p className="text-[#45515e] mb-6">
          Если у вас остались вопросы или нужна помощь с настройкой DeepThroath, свяжитесь с нами:
        </p>
        <div className="flex flex-wrap gap-4">
          <a
            href="https://github.com/InfernYaCr/DeepThroath"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#181e25] text-white rounded-lg hover:bg-[#181e25]/90 transition-colors font-medium"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            GitHub Repository
          </a>
          <a
            href="https://github.com/InfernYaCr/DeepThroath/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-white border border-[#e5e7eb] text-[#181e25] rounded-lg hover:bg-[#f8f9fa] transition-colors font-medium"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Report an Issue
          </a>
        </div>
      </div>
    </div>
  )
}
