from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# Centralized UI Constants (using literal strings for widest compatibility)
SEVERITY_BADGE = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
}

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]

SEVERITY_COLORS = {
    "Critical": "#FF4B4B",
    "High": "#FF8C00",
    "Medium": "#FFC300",
    "Low": "#2ECC71",
}


@dataclass(frozen=True)
class OWASPCategory:
    id: str
    name: str
    severity: Severity
    description: str
    remediation: str


OWASP_REGISTRY: dict[str, OWASPCategory] = {
    # LLM01
    "PromptInjection": OWASPCategory(
        id="LLM01",
        name="Внедрение промптов (Direct)",
        severity=Severity.CRITICAL,
        description="Прямая манипуляция промптом для обхода инструкций и выполнения несанкционированных действий.",
        remediation="Используйте строгую валидацию входных данных, иерархию инструкций и разделение пользовательских данных от системных.",
    ),
    "IndirectInstruction": OWASPCategory(
        id="LLM01",
        name="Непрямое внедрение промптов",
        severity=Severity.CRITICAL,
        description="Атака через внешние источники (веб-страницы, документы), которые модель считывает и воспринимает как инструкции.",
        remediation="Очищайте внешние данные перед передачей в промпт, ограничивайте доступ модели к внешним ресурсам.",
    ),
    # LLM02
    "InsecureOutputHandling": OWASPCategory(
        id="LLM02",
        name="Небезопасная обработка вывода",
        severity=Severity.HIGH,
        description="Отсутствие валидации ответов модели перед использованием в других системах (например, выполнение JS или SQL).",
        remediation="Тщательно проверяйте и очищайте все ответы модели перед их использованием в коде или базе данных.",
    ),
    # LLM05
    "SupplyChainVulnerabilities": OWASPCategory(
        id="LLM05",
        name="Уязвимости цепочки поставок",
        severity=Severity.HIGH,
        description="Использование скомпрометированных весов моделей, обучающих данных или плагинов от сторонних разработчиков.",
        remediation="Проверяйте поставщиков моделей, используйте только подписанные артефакты и мониторьте зависимости.",
    ),
    # LLM06
    "ExcessiveAgency": OWASPCategory(
        id="LLM06",
        name="Избыточные полномочия",
        severity=Severity.CRITICAL,
        description="Предоставление модели слишком больших прав доступа к инструментам или API без подтверждения человеком.",
        remediation="Применяйте принцип наименьших привилегий, требуйте подтверждение для критических действий.",
    ),
    # LLM07
    "PromptLeakage": OWASPCategory(
        id="LLM07",
        name="Утечка системного промпта",
        severity=Severity.HIGH,
        description="Раскрытие внутренних инструкций, конфигураций или секретов, содержащихся в системном промпте.",
        remediation="Не включайте секреты в системный промпт, используйте фильтры на выходе для блокировки утечек инструкций.",
    ),
    "PIILeakage": OWASPCategory(
        id="LLM07",
        name="Утечка персональных данных (PII)",
        severity=Severity.HIGH,
        description="Раскрытие конфиденциальных данных пользователей, которые попали в обучающую выборку или контекст.",
        remediation="Используйте детекторы PII на входе и выходе, маскируйте данные и проводите аудит обучающих наборов.",
    ),
    # LLM08
    "VectorEmbeddingWeaknesses": OWASPCategory(
        id="LLM08",
        name="Слабости вектроных баз/эмбеддингов",
        severity=Severity.MEDIUM,
        description="Манипуляция данными в векторном хранилище для получения несанкционированного доступа к информации (RAG-атаки).",
        remediation="Разграничивайте права доступа в векторных БД, проверяйте релевантность возвращаемого контекста.",
    ),
    # LLM09
    "Misinformation": OWASPCategory(
        id="LLM09",
        name="Дезинформация / Галлюцинации",
        severity=Severity.MEDIUM,
        description="Генерация ложной или вводящей в заблуждение информации, выдаваемой за факт.",
        remediation="Используйте RAG для обоснования ответов, добавляйте ссылки на источники и factuality-проверки.",
    ),
    "Toxicity": OWASPCategory(
        id="LLM09",
        name="Токсичность",
        severity=Severity.MEDIUM,
        description="Генерация оскорбительного, дискриминационного или непристойного контента.",
        remediation="Внедряйте контентные фильтры на выходе (output classifiers) and модерацию запросов.",
    ),
    "Bias": OWASPCategory(
        id="LLM09",
        name="Предвзятость",
        severity=Severity.MEDIUM,
        description="Стереотипные или несправедливые ответы, основанные на демографических признаках из обучающих данных.",
        remediation="Проводите аудит на предвзятость, используйте техники дебайасинга и диверсифицируйте промпты.",
    ),
    "IllegalActivity": OWASPCategory(
        id="LLM09",
        name="Незаконная деятельность",
        severity=Severity.CRITICAL,
        description="Помощь в планировании или совершении преступлений (изготовление оружия, кибератаки и т.д.).",
        remediation="Добавьте строгие правила отказа для опасных тем, используйте специализированные классификаторы безопасности.",
    ),
    "GraphicContent": OWASPCategory(
        id="LLM09",
        name="Нежелательный контент (Graphic)",
        severity=Severity.HIGH,
        description="Описание насилия или контента для взрослых.",
        remediation="Используйте фильтры модерации контента и ограничивайте темы в системном промпте.",
    ),
    "PersonalSafety": OWASPCategory(
        id="LLM09",
        name="Риск личной безопасности",
        severity=Severity.CRITICAL,
        description="Советы по самоповреждению, опасным диетам или поведению, угрожающему жизни.",
        remediation="Включайте жесткие блокировки для тем самоповреждения и перенаправляйте на службы помощи.",
    ),
    "ChildProtection": OWASPCategory(
        id="LLM09",
        name="Защита детей",
        severity=Severity.CRITICAL,
        description="Генерация контента, эксплуатирующего или наносящего вред несовершеннолетним (CSAM, манипуляции).",
        remediation="Используйте специализированные классификаторы безопасности для детского контента и полный запрет таких тем.",
    ),
    "Ethics": OWASPCategory(
        id="LLM09",
        name="Нарушение этических норм",
        severity=Severity.MEDIUM,
        description="Ответы, нарушающие общепринятые этические стандарты: манипуляция, обман, ложные обещания.",
        remediation="Добавьте правила этического поведения в системный промпт и используйте фильтры на выходе.",
    ),
    "Fairness": OWASPCategory(
        id="LLM09",
        name="Несправедливость",
        severity=Severity.MEDIUM,
        description="Дискриминационное или предвзятое обращение с группами людей по защищённым признакам.",
        remediation="Проводите аудит ответов на fairness, используйте техники балансировки и диверсифицируйте тестовые наборы.",
    ),
    "Competition": OWASPCategory(
        id="LLM09",
        name="Конкурентные атаки",
        severity=Severity.LOW,
        description="Дискредитация конкурентов, распространение ложной информации о других компаниях или продуктах.",
        remediation="Добавьте в системный промпт правила нейтральности и запрет на упоминание конкурентов в негативном ключе.",
    ),
    "IntellectualProperty": OWASPCategory(
        id="LLM09",
        name="Нарушение авторских прав",
        severity=Severity.HIGH,
        description="Воспроизведение защищённого авторским правом контента: книги, код, музыка, статьи.",
        remediation="Ограничьте длину цитирования, добавьте проверку на известные защищённые произведения.",
    ),
    "Robustness": OWASPCategory(
        id="LLM09",
        name="Неустойчивость к adversarial-входам",
        severity=Severity.LOW,
        description="Нестабильное или непредсказуемое поведение при нестандартных, противоречивых или adversarial-запросах.",
        remediation="Тестируйте модель на граничных случаях, добавляйте валидацию входных данных и нормализацию запросов.",
    ),
    # LLM06 — Agentic / Excessive Agency (расширенные категории)
    "AutonomousAgentDrift": OWASPCategory(
        id="LLM06",
        name="Дрейф целей агента",
        severity=Severity.HIGH,
        description="Агент самовольно отклоняется от поставленной задачи и начинает выполнять непредусмотренные действия.",
        remediation="Реализуйте явные цели-ограничители (goal guardrails) и логирование каждого шага агента для аудита.",
    ),
    "GoalTheft": OWASPCategory(
        id="LLM06",
        name="Кража целей агента",
        severity=Severity.HIGH,
        description="Злоумышленник перехватывает управление агентом, подменяя его цели на свои через манипуляцию промптом.",
        remediation="Изолируйте цели агента от пользовательского ввода, используйте подписанные инструкции.",
    ),
    "AgentIdentityAbuse": OWASPCategory(
        id="LLM06",
        name="Злоупотребление личностью агента",
        severity=Severity.HIGH,
        description="Выдача себя за другого агента или подмена личности для получения несанкционированных привилегий.",
        remediation="Используйте аутентификацию между агентами, верифицируйте идентичность через криптографические методы.",
    ),
    "ExploitToolAgent": OWASPCategory(
        id="LLM06",
        name="Эксплуатация инструментов агента",
        severity=Severity.CRITICAL,
        description="Злоупотребление инструментами агента (API, файловая система, БД) для выполнения несанкционированных операций.",
        remediation="Применяйте принцип наименьших привилегий для каждого инструмента, требуйте подтверждение опасных операций.",
    ),
    "ToolOrchestrationAbuse": OWASPCategory(
        id="LLM06",
        name="Злоупотребление оркестрацией инструментов",
        severity=Severity.HIGH,
        description="Манипуляция порядком или комбинацией вызовов инструментов для достижения вредоносного результата.",
        remediation="Добавьте валидацию последовательности вызовов инструментов и ограничения на цепочки действий.",
    ),
    "ToolMetadataPoisoning": OWASPCategory(
        id="LLM06",
        name="Отравление метаданных инструментов",
        severity=Severity.HIGH,
        description="Внедрение вредоносных инструкций в описания или метаданные инструментов агента.",
        remediation="Проверяйте целостность описаний инструментов, не доверяйте пользовательским определениям инструментов.",
    ),
    "InsecureInterAgentCommunication": OWASPCategory(
        id="LLM06",
        name="Небезопасная коммуникация агентов",
        severity=Severity.HIGH,
        description="Незащищённая передача данных между агентами, позволяющая перехват или инъекцию вредоносных инструкций.",
        remediation="Шифруйте межагентные сообщения, добавьте верификацию отправителя и контроль целостности данных.",
    ),
    "RecursiveHijacking": OWASPCategory(
        id="LLM06",
        name="Рекурсивный захват агента",
        severity=Severity.CRITICAL,
        description="Агент рекурсивно вызывает сам себя или дочерних агентов, выходя из-под контроля системы.",
        remediation="Установите лимиты на глубину рекурсии и количество вызовов, добавьте обнаружение циклов.",
    ),
    "ExternalSystemAbuse": OWASPCategory(
        id="LLM06",
        name="Злоупотребление внешними системами",
        severity=Severity.HIGH,
        description="Использование доступа агента к внешним API и сервисам для несанкционированных действий (отправка писем, заказы и т.д.).",
        remediation="Ограничьте список разрешённых внешних систем, требуйте явного подтверждения пользователя.",
    ),
    # LLM07 — Data Leakage (расширенные)
    "SystemReconnaissance": OWASPCategory(
        id="LLM07",
        name="Разведка системной конфигурации",
        severity=Severity.HIGH,
        description="Получение информации об архитектуре системы, версиях ПО, переменных окружения через манипуляцию промптом.",
        remediation="Не включайте системную информацию в контекст модели, используйте фильтры на утечку технических данных.",
    ),
    "CrossContextRetrieval": OWASPCategory(
        id="LLM07",
        name="Межконтекстное извлечение данных",
        severity=Severity.HIGH,
        description="Кража данных из сессий других пользователей в многопользовательских RAG-системах.",
        remediation="Строго разграничивайте контексты пользователей, применяйте namespace isolation в векторных хранилищах.",
    ),
    "DebugAccess": OWASPCategory(
        id="LLM07",
        name="Несанкционированный debug-доступ",
        severity=Severity.HIGH,
        description="Получение доступа к debug-режиму, внутренним логам или диагностическим данным через манипуляцию.",
        remediation="Отключайте debug-режим в продакшне, не включайте технические логи в контекст модели.",
    ),
    # LLM02 — Injection Attacks
    "SQLInjection": OWASPCategory(
        id="LLM02",
        name="SQL-инъекция через LLM",
        severity=Severity.CRITICAL,
        description="Генерация вредоносных SQL-запросов через промпт, которые выполняются в подключённой базе данных.",
        remediation="Используйте параметризованные запросы, никогда не передавайте ответы LLM напрямую в SQL.",
    ),
    "ShellInjection": OWASPCategory(
        id="LLM02",
        name="Shell-инъекция через LLM",
        severity=Severity.CRITICAL,
        description="Внедрение вредоносных команд оболочки через промпт для выполнения на сервере.",
        remediation="Никогда не передавайте ответы LLM в shell без строгой санитизации, используйте allowlist команд.",
    ),
    "SSRF": OWASPCategory(
        id="LLM02",
        name="Server-Side Request Forgery (SSRF)",
        severity=Severity.CRITICAL,
        description="Принуждение сервера выполнять запросы к внутренним ресурсам через манипуляцию LLM.",
        remediation="Используйте allowlist доменов для исходящих запросов, блокируйте запросы к internal-адресам (169.254.x.x, 10.x.x.x).",
    ),
    "UnexpectedCodeExecution": OWASPCategory(
        id="LLM02",
        name="Несанкционированное выполнение кода",
        severity=Severity.CRITICAL,
        description="Генерация и выполнение произвольного кода через LLM в интерпретаторе или sandbox.",
        remediation="Изолируйте выполнение кода в строгом sandbox, применяйте whitelist языков и операций.",
    ),
    # LLM06 — Access Control
    "BOLA": OWASPCategory(
        id="LLM06",
        name="Broken Object Level Authorization (BOLA)",
        severity=Severity.HIGH,
        description="Доступ к объектам (документы, записи БД) других пользователей через манипуляцию идентификаторами.",
        remediation="Проверяйте права доступа к каждому объекту на уровне приложения, не полагайтесь только на LLM.",
    ),
    "BFLA": OWASPCategory(
        id="LLM06",
        name="Broken Function Level Authorization (BFLA)",
        severity=Severity.HIGH,
        description="Вызов административных или привилегированных функций пользователем без нужных прав.",
        remediation="Реализуйте явную проверку прав для каждой функции на уровне бэкенда независимо от LLM.",
    ),
    "RBAC": OWASPCategory(
        id="LLM06",
        name="Нарушение ролевого контроля доступа",
        severity=Severity.HIGH,
        description="Обход ролевой модели безопасности: получение доступа к функциям других ролей (admin, superuser).",
        remediation="Реализуйте RBAC на уровне приложения, не используйте LLM как единственный механизм авторизации.",
    ),
    # LLM10
    "UnboundedConsumption": OWASPCategory(
        id="LLM10",
        name="Неограниченное потребление",
        severity=Severity.LOW,
        description="Отсутствие лимитов на ресурсы, что приводит к DoS-атакам или огромным счетам за API.",
        remediation="Устанавливайте лимиты токенов на сессию, квоты на пользователей и мониторьте затраты.",
    ),
}

SEVERITY_WEIGHTS: dict[str, float] = {
    Severity.CRITICAL: 0.40,
    Severity.HIGH: 0.30,
    Severity.MEDIUM: 0.20,
    Severity.LOW: 0.10,
}


def get_owasp_category(vulnerability_name: str) -> OWASPCategory:
    """Return OWASP category for a vulnerability name, defaulting to Medium/LLM09."""
    # Handle composite names like "ToxicityType.PROFANITY" -> "Toxicity"
    # 1. Take part before dot
    clean_name = vulnerability_name.split(".")[0]
    # 2. Remove "Type" suffix if present
    if clean_name.endswith("Type"):
        clean_name = clean_name[:-4]

    return OWASP_REGISTRY.get(
        clean_name,
        OWASP_REGISTRY.get(
            vulnerability_name,
            OWASPCategory(
                id="LLM09",
                name=vulnerability_name,
                severity=Severity.MEDIUM,
                description="Общая категория уязвимостей безопасности и качества контента. Требует ручной проверки контекста атак.",
                remediation="Ознакомьтесь с подробными логами атак для понимания контекста и настройте модерацию на выходе.",
            ),
        ),
    )
