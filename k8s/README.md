# Kubernetes Manifests

Здесь хранятся манифесты для деплоя приложений и инфраструктурных компонентов в кластер K3s.

## Структура
* **`/manifests`** — Deployments, Services и Ingress для микросервисов (Gateway, Redirector, Analytics Worker).
* **`/stateful`** — StatefulSets и PersistentVolumeClaims (PVC) для баз данных и очередей (PostgreSQL, Redis, RabbitMQ).
* **`/monitoring`** — конфигурации для Prometheus, Grafana и других инструментов Observability.