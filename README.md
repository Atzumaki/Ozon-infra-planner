# Infrastructure Capacity Planner

Портфолио-проект по предиктивной аналитике IT-инфраструктуры: прогнозирует
потребление CPU/RAM, рассчитывает необходимый резерв и подбирает целочисленный
набор серверов с минимальной совокупной стоимостью владения (CAPEX + OPEX).

> Проект не связан с Ozon и использует только синтетические данные.

## Почему этот проект

Он воспроизводит полный путь аналитического решения, а не только обучение модели:

- временной ряд с трендом, недельной сезонностью, backtesting и 95% интервалом;
- математическая оптимизация серверного парка с помощью MILP;
- явный расчет CAPEX, OPEX, резерва и уже имеющихся мощностей;
- мультиагентный pipeline: Forecast Agent → Budget Agent → Risk Agent;
- типизированный REST API, CLI, Docker, Kubernetes manifest и CI;
- unit- и integration-тесты.

## Архитектура

```text
observations + hardware catalog
              │
       Forecast Agent
      trend + seasonality
              │ demand + uncertainty
        Budget Agent
       MILP / minimum TCO
              │ capacity plan
          Risk Agent
              │
        typed API response
```

Агенты здесь — независимые компоненты с узкой ответственностью и типизированными
handoff-объектами. Это делает оркестрацию тестируемой и позволяет позже заменить
`RiskAgent` на LLM-агента с tool calling, не передавая модели сам расчет бюджета.

## Быстрый старт

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Запустить готовый сценарий на воспроизводимых синтетических данных:

```bash
infra-planner
```

Запустить API:

```bash
uvicorn infra_planner.api:app --reload
```

Swagger UI будет доступен на `http://127.0.0.1:8000/docs`. Основной endpoint:

```bash
curl -X POST http://127.0.0.1:8000/v1/plan \
  -H "Content-Type: application/json" \
  --data @request.json
```

Схему `request.json` можно посмотреть в Swagger. Без входного файла CLI запускает
демо, а собственный JSON принимает так: `infra-planner --input request.json`.

## Математика

Для каждого ресурса строится прозрачный baseline:

```text
y(t) = β₀ + β₁t + β₂t² + β₃sin(2πt/7) + β₄cos(2πt/7) + ε
```

Плановая нагрузка — максимум верхней границы прогноза плюс operational reserve.
Оптимизатор выбирает целые количества серверов `xᵢ`:

```text
min Σ xᵢ · (CAPEXᵢ + months · OPEXᵢ)
s.t. Σ xᵢ · CPUᵢ ≥ required CPU
     Σ xᵢ · RAMᵢ ≥ required RAM
     0 ≤ xᵢ ≤ availableᵢ, xᵢ ∈ ℤ
```

## Проверка качества

```bash
ruff check .
pytest
docker build -t infra-capacity-planner .
```

В тестах проверяются временной порядок и интервалы прогноза, точность на holdout,
оптимальность простого серверного набора, infeasible-сценарий и HTTP-контракт.

## Что развивать дальше

- rolling-origin cross-validation и сравнение с LightGBM/Prophet;
- несколько дата-центров, lead time поставки и staged procurement;
- chance constraints вместо фиксированного резерва;
- мониторинг drift и фактической экономии в Prometheus/Grafana;
- LLM-агент для объяснения отклонений с безопасными read-only tools.

