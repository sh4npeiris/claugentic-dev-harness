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

- **Auditor checks —** Scan log statements for unredacted tokens, passwords, or user data `[J]`; confirm a structured logger (not bare `print`/`console.log`) is used `[D]`; verify ERROR/WARN are reserved for actionable conditions `[J]`.

## Metrics, tracing, and health checks

- **Auditor checks —** Confirm new code paths increment relevant counters or are justified as trivial `[J]`; verify trace-id propagation across async boundaries `[J]`; check that health endpoints exist and test real dependencies `[D]`.

## Alerting hooks

- **Good looks like —** Alerts fire on **SLO thresholds**, not resource proxies (“CPU > 80%”), and page **only when human action is required**. A silenced alert is a deleted alert.
- **Auditor checks —** If new failure modes are introduced, confirm a corresponding alert or runbook reference exists `[J]`; check that alert thresholds are documented and not arbitrary `[J]`.

## 12-factor configuration

- **Auditor checks —** Grep for hardcoded hostnames, ports, or credential strings `[D]`; confirm config validation runs at process startup `[J]`; verify no env-specific branches (`if env == "prod"`) exist in application code `[J]`.

## Environment separation and reproducible builds

- **Auditor checks —** Confirm no shared DB/queue between staging and prod `[J]`; verify image/dependency pins are present `[D]`; check that rollback steps exist in the runbook or CI pipeline `[J]`.

## Feature flags and progressive rollout

- **Auditor checks —** If a change introduces risk that warrants a flag, confirm one exists `[J]`; verify flag cleanup tickets exist to prevent permanent flag accumulation `[J]`.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
