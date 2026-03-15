# Cloud Native URL Shortener

![Status](https://img.shields.io/badge/Status-Work_in_Progress-yellow)
![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Infrastructure](https://img.shields.io/badge/Infrastructure-Kubernetes_(K3s)-blueviolet)

Учебный pet-проект для освоения навыков построения Cloud Native архитектуры, работы с микросервисами, Infrastructure as Code (IaC) и Kubernetes.

## 🎯 О проекте
Это масштабируемый сервис сокращения ссылок с асинхронной аналитикой переходов. Проект спроектирован с учетом высоких нагрузок (Highload) и разворачивается в кластере Kubernetes (K3s) на трех VDS-серверах.

## 🏗 Целевая архитектура

```text
┌─────────────────────────────────────────────────────────────────┐
│                        ИНФРАСТРУКТУРА                           │
│                                                                 │
│  VDS-1 (Master)          VDS-2 (Worker)      VDS-3 (Worker)     │
│  ┌─────────────┐        ┌──────────────┐    ┌──────────────┐    │
│  │ K3s Server  │        │ K3s Agent    │    │ K3s Agent    │    │
│  │ Prometheus  │        │ PostgreSQL   │    │ Redis        │    │
│  │ Grafana     │        │ RabbitMQ     │    │ Metabase     │    │
│  │ Traefik     │        │              │    │              │    │
│  └─────────────┘        └──────────────┘    └──────────────┘    │
│                                                                 │
│                     K3s Cluster (Pods):                         │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────┐    │
│  │ API Gateway  │   │ Shortener    │   │ Analytics Worker  │    │
│  │ (Laravel)    │   │ (Python/     │   │ (Python)          │    │
│  │              │   │  FastAPI)    │   │                   │    │
│  └──────────────┘   └──────────────┘   └───────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠 Технологический стек

* **Backend:** PHP (Laravel), Python (FastAPI)
* **Databases & Queues:** PostgreSQL 16, Redis 7, RabbitMQ
* **Infrastructure:** Docker, Kubernetes (K3s), Terraform, Ansible
* **Observability & BI:** Prometheus, Grafana, Metabase
* **CI/CD:** GitHub Actions

## 📂 Структура репозитория

* `/services` — исходный код микросервисов.
* `/infrastructure` — IaC (Terraform для провиженинга VDS, Ansible для настройки).
* `/k8s` — манифесты Kubernetes и Helm-чарты.
* `/docker` — файлы для локального запуска (docker-compose).
* `/docs` — документация проекта и Architecture Decision Records (ADR).