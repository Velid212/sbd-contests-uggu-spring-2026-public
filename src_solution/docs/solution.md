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

Команды самопроверки:

```bash
pytest -q src_solution/tests
pytest -q src_solution/tests --cov=src_solution.abu.tcb --cov=src_solution.abu.tcb.sys.security_monitor --cov-report=term-missing
bash scripts/prepare_certification_bundle_solution.sh
```

## 6. Сквозной сценарий ЦР–АБУ

Решение сохраняет совместимый HTTP API для сквозного сценария ЦР–АБУ: регистрация установки выполняется внешним Digital Mine через `/api/v1/rigs`, после чего миссия передаётся в АБУ через `/api/v1/missions`. АБУ возвращает `accepted=true` и `mission_id`, а дальнейшие тики доступны через `/api/v1/missions/tick`. Это соответствует e2e-сценарию репозитория и не требует изменения корневых тестов.

## 7. Диаграммы

Диаграммы PlantUML добавлены в каталог `src_solution/docs/diagrams/`:

- `src_solution/docs/diagrams/policy_architecture.puml` — диаграмма компонентов и политик;
- `src_solution/docs/diagrams/sequence_functional_domains.puml` — диаграмма последовательности request/response между TCB, monitor и OTHER;
- `src_solution/docs/diagrams/system_ipc_components.puml` — диаграмма IPC-компонентов.

## 8. Сертификация

Пакет решения собирается командой:

```bash
make prepare-cert-bundle-solution
```

Скрипт берёт `src_solution/abu`, `src_solution/tests`, `src_solution/requirements.txt`, `src_solution/requirements-other.txt`, `src_solution/sbom/SBOM_TCB.cdx.json`, `src_solution/sbom/SBOM_OTHER.cdx.json` и формирует `artifacts/abu_certification_bundle.tar.gz`.

Сертификация:

```bash
make certify-abu-solution
```

Ожидаемый эффект: Регулятор считает меньший объём ДВБ и не применяет heavy dependency multiplier к TCB, потому что `numpy` находится в OTHER.

## 9. Таблица критериев C01–C25

| Критерий | Выполнение |
|---|---|
| C01 | Поддержано прохождение тестов решения и совместимость API |
| C02–C04 | Security-тесты находятся в `src_solution/tests/security` и помечены `pytest.mark.security` |
| C05–C07 | Есть SBOM и пакет сертификации решения |
| C08 | API совместим со сценарием ЦР → АБУ |
| C09 | Код оформлен в `src_solution/` |
| C10–C12 | Есть event log, зависимости и тесты, импортирующие `src_solution` |
| C13 | Раздел security-тестов приведён выше |
| C14 | `numpy` вынесен из TCB SBOM в OTHER SBOM |
| C15 | Журнал событий покрыт тестами |
| C16 | ДВБ `src_solution/abu/tcb` покрыта тестами |
| C17 | Отчёт расположен в `src_solution/docs/solution.md` |
| C18 | Есть `security_monitor` и политики |
| C19 | Есть процессная изоляция `DomainProcess` на `multiprocessing.Process` |
| C20–C22 | Экспертная оценка стоимости/качества архитектуры |
| C23 | ДВБ разделена на малые модули |
| C24 | Интерфейс ДВБ ограничен двумя IPC-политиками |
| C25 | Monitor покрыт security-тестами |

## 10. Итог

Главное изменение относительно `src_starting_point`: вычисления с тяжёлыми зависимостями и псевдо-ИИ вынесены из ДВБ в `src_solution/abu/other`, а ДВБ оставлена малой и проверяемой. Все входы из недоверенной зоны проходят через `SecurityMonitor`, а выполнение OTHER-операций идёт через отдельный процесс.
