---
module: observability-ops
title: Observability & Ops
status: draft
iso_25010: [reliability]
load_scope:
  keywords: [log, logging, trace, metric, monitor, alert, config, env, deploy, feature-flag, rollback]
  globs: ["src/**", "**/*config*"]
---

# Observability & Ops — structured signals, safe config, and operable deployments

> **Loads when:** changes touch logging, metrics, tracing, alerting, health checks, environment config, deployment pipelines, feature flags, or rollback paths.
> Method, tags, honesty register: `README.md` → *Reading a module*.

---

## Structured logging

- **Auditor checks —** `[D]` a structured logger, not bare `print`/`console.log` · `[J]` ERROR/WARN reserved for actionable conditions.

## Metrics, tracing, and health checks

- **Auditor checks —** `[D]` health endpoints exist and test **real dependencies** · `[J]` trace-id propagates across async boundaries.

## Alerting hooks

- **Good looks like —** Alerts fire on **SLO thresholds**, not resource proxies ("CPU > 80%"), and page **only when human action is required**. A silenced alert is a deleted alert.
- **Auditor checks —** `[J]` new failure modes have a corresponding alert or runbook reference, with documented thresholds.

## 12-factor configuration

- **Auditor checks —** `[D]` grep hardcoded hostnames, ports or credential strings · `[J]` config validated at process startup · `[J]` no env-specific branch (`if env == "prod"`) in application code.

## Environment separation and reproducible builds

- **Auditor checks —** `[D]` image/dependency pins present · `[J]` no shared DB/queue between staging and prod · `[J]` rollback steps exist in the runbook or CI pipeline.

## Feature flags and progressive rollout

- **Auditor checks —** `[J]` a change carrying rollout risk has a flag · `[J]` flag cleanup tracked, so flags don't accumulate permanently.
