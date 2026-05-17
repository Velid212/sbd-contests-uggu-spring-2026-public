# Отчёт о решении АБУ: разделение ДВБ, политики, SBOM и тесты

## 1. Архитектура решения

Решение размещено в `src_solution/` и отделяет доверенную вычислительную базу от недоверенных вычислительных доменов.

- `src_solution/abu/tcb/` — ДВБ: безопасные инварианты, лимиты глубины/RPM, классификация риска, журнал событий, reference monitor.
- `src_solution/abu/tcb/sys/security_monitor.py` — монитор междоменных запросов request/response.
- `src_solution/abu/tcb/sys/ipc_policies.json` — статические политики IPC: разрешены только операции `suggest_regime`, `anomaly_vibration`, `smooth_vibration` от `tcb_controller` к недоверенным доменам.
- `src_solution/abu/other/` — недоверенная зона: псевдо-ИИ, numpy-сглаживание, процессная изоляция `DomainProcess` на `multiprocessing.Process`.
- `src_solution/abu/app.py` — HTTP API АБУ. API остаётся совместимым со стартовой точкой, но обращается к недоверенным вычислениям только через монитор и процессную границу.

Граница доверия построена так: ДВБ хранит состояние миссии и принимает финальные решения, а недоверенная зона возвращает только рекомендации/числовые оценки. Возврат из OTHER не изменяет состояние напрямую.

## 2. ДВБ и недоверенные домены

ДВБ минимизирована: тяжёлая зависимость `numpy` удалена из `src_solution/abu/tcb` и вынесена в `src_solution/abu/other/numpy_workflow.py`. В SBOM это отражено так:

- `src_solution/sbom/SBOM_TCB.cdx.json` — нет `numpy`; содержит контроллер ДВБ и лёгкие зависимости.
- `src_solution/sbom/SBOM_OTHER.cdx.json` — содержит `numpy`, FastAPI/uvicorn/httpx и недоверенный домен.
- `src_solution/sbom/sbom_manifest.json` — исходный манифест для генерации CycloneDX.

## 3. Политики и security monitor

Политики находятся в `src_solution/abu/tcb/sys/ipc_policies.json`. Интерфейс ДВБ малый: две разрешающие политики и три операции. Все остальные операции запрещаются.

`src_solution/abu/tcb/sys/security_monitor.py` проверяет:

- допустимость пары доменов `from -> to`;
- допустимость операции;
- ограничения payload, например глубина не больше 200 м и ограничение размера массива вибраций.

Нарушения записываются в `src_solution/abu/tcb/event_log.py` как события уровня `WARNING` или `ERROR`.

## 4. Журнал событий

Журнал реализован в `src_solution/abu/tcb/event_log.py`:

- кольцевой буфер на 10 событий;
- полный файл `var/abu_solution_logs/abu_events_full.log`;
- hash-chain для каждой записи;
- безопасная деградация при read-only файловой системе.

API журналов доступен через:

- `/api/v1/events/ring`;
- `/api/v1/events/full`.

## 5. Тесты безопасности

Тесты решения находятся только в `src_solution/tests/`:

| Файл | Что проверяет |
|---|---|
| `src_solution/tests/test_app.py` | health, миссия, tick, AI suggest, ABU_MAX_RPM |
| `src_solution/tests/test_event_log.py` | ring-buffer, full log, hash-chain |
| `src_solution/tests/test_tcb_safety.py` | лимиты ДВБ, risk flag, emergency stop |
| `src_solution/tests/security/test_security_monitor.py` | allow/deny политики, payload guard |
| `src_solution/tests/security/test_domain_process.py` | request/response через multiprocessing-процесс |
| `src_solution/tests/security/test_policies_and_sbom.py` | малый интерфейс IPC и перенос numpy в OTHER SBOM |
| `src_solution/tests/security/test_solution_app.py` | security/coverage тесты API, журналов, wrappers, DomainProcess и emergency-веток.|

## 6. Сквозной сценарий ЦР–АБУ

Решение сохраняет совместимый HTTP API для сквозного сценария ЦР–АБУ: регистрация установки выполняется внешним Digital Mine через `/api/v1/rigs`, после чего миссия передаётся в АБУ через `/api/v1/missions`. АБУ возвращает `accepted=true` и `mission_id`, а дальнейшие тики доступны через `/api/v1/missions/tick`. Это соответствует e2e-сценарию репозитория и не требует изменения корневых тестов.

## 7. Сертификация

Результат сертификации: успешно
Стоимость (усл. ед.): 1295.90
ДВБ: строк кода abu=290, суммарная цикломатика=57
Сертификат (SHA-256 пакета): a44b52fc1d05d2ccb7f40db130c5982ad00f2b33a5d05a0260359ca13716af2e
@Velid212 ➜ /workspaces/sbd-contests-uggu-spring-2026-public (main) $ 

## 8. Таблица критериев C01–C25

  C01: Все тесты репозитория (включая тесты решения) завершаются успешно: 3.0  (OK)
  C02: Все тесты решения находятся в подкаталогах src_solution/tests: 3.0  (все тесты решения (8) находятся в src_solution/tests/**)
  C03: Маркер security в pytest.ini и использование в тестах: 3.0  (маркер security используется (8 файлов))
  C04: Покрытие тестами event_log / журнал: 3.0  (14 тестовых функций)
  C05: Пример sga.json: 3.0  (валидный JSON, несколько ключей)
  C06: SBOM TCB / OTHER в примерах: 3.0  (CycloneDX валиден)
  C07: Успешное выполнение сертификации (пакет + ответ Регулятора): 3.0  (сертификация успешна)
  C08: Сквозной автотест ЦР–АБУ (основной сценарий): 3.0  (pytest OK; e2e покрывает регистрацию, допуск и выдачу миссии)
  C09: Оформление кода в src_solution (flake8, PEP8): 0.0  (52 замечаний)
  C10: Решение: журнал событий / event_log в src_solution: 3.0  (модуль event_log в дереве)
  C11: Решение: зависимости (requirements / pyproject в src_solution): 0.0  (тяжёлые зависимости в requirements.txt: fastapi)
  C12: Тесты репозитория импортируют код из src_solution (AST): 3.0  (файлов с import src_solution: 8)
  C13: Раздел тестов безопасности в src_solution/docs/solution.md: 3.0  (раздел есть, явные пути (37))
  C14: numpy в SBOM решения (SBOM_TCB vs SBOM_OTHER): 3.0  (numpy только в SBOM_OTHER, SBOM валидны)
  C15: Тесты: журнал event_log и решение (импорты из src_solution + event_log): 3.0  (файлов: 3)
  C16: Покрытие ДВБ решения (src_solution/abu/tcb) тестами: 2.0  (70.0% (60–79%))
  C17: Отчёт о решении (приоритет `src_solution/docs/solution.md`): 3.0  (архитектура, политики, сквозные и security-тесты, сертификация, диаграммы)
  C18: security_monitor, policies в src_solution; тесты политик: 3.0  (monitor, policies, тесты≈2)
  C19: домены и монитор; разнесение по процессам (не только каталоги tcb/other): 3.0  (процессы(multiprocessing/subprocess/DomainProcess), domains, monitor, request/response)
  C20: Стоимость сертификации — место в рейтинге (жюри: 3 / 2 / 1 / 0): 0.0  (автоматика 0; жюри после сравнения всех участников)
  C21: Экспертно — соответствие политик архитектуре АБУ (жюри): 0.0  (автоматика 0; заполняет жюри)
  C22: Экспертно — полнота отчёта и воспроизводимость (жюри): 0.0  (автоматика 0; заполняет жюри)
  C23: Размер доменов ДВБ (максимальный LOC одного домена): 3.0  (максимум security_monitor=66 LOC (<100))
  C24: Количество интерфейсов домена ДВБ (разрешающие IPC-политики): 3.0  (максимум tcb_controller=2 политики)
  C25: Наличие security_monitor, security-тесты и покрытие monitor-кода: 2.0  (coverage security_monitor=0.0% (<60%))

Сумма (raw): 58.0 / 75

Сертификация (ответ Регулятора): успех=True, стоимость≈1295.90 усл. ед.

## 9. Итог

Главное изменение относительно `src_starting_point`: вычисления с тяжёлыми зависимостями вынесены из ДВБ в `src_solution/abu/other`, а ДВБ оставлена малой и проверяемой. Все входы из недоверенной зоны проходят через `SecurityMonitor`, а выполнение OTHER-операций идёт через отдельный процесс.
