---
module: internationalization
title: Internationalization
status: draft
iso_25010: [interaction-capability]
load_scope:
  keywords: [i18n, l10n, locale, timezone, translation, encoding, currency, rtl]
  globs: ["**/locales/**", "**/i18n/**"]
---

# Internationalization — correct behaviour across locales, timezones, and scripts

> **Loads when:** changes touch locale handling, date/number/currency formatting, string translation pipelines, timezone logic, character encoding, or RTL layout.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **Accessibility** (WCAG, keyboard nav, contrast, screen reader) is `product-ux.md`'s — cross-reference it; **do not duplicate those standards here.**

---

## Character encoding

- **Auditor checks —** Confirm source files and DB columns are UTF-8 `[D]`; check that file/stream open calls do not omit an explicit encoding `[J]`; verify no `latin-1`/`ascii` assumptions in string manipulation `[J]`.

## Locale-aware date, time, and number formatting

- **Auditor checks —** Confirm display formatting passes a locale/format parameter `[J]`; verify wire formats use ISO 8601 for dates and integers/decimals for numbers `[D]`; check that no locale-dependent `parseInt`/`parseFloat` or `strptime` calls lack explicit locale handling `[J]`.

## Timezone handling

- **Auditor checks —** Confirm DB timestamps are UTC-typed (timestamptz or equivalent) `[D]`; verify no raw `+offset` arithmetic in business logic — use `pytz`/`dateutil`/`Intl.DateTimeFormat`/`Temporal` `[J]`; check that user timezone is read from a preference, not inferred from server locale `[J]`.

## Translatable strings

- **Auditor checks —** Grep for hardcoded user-visible string literals outside translation files `[D]`; verify concatenations use named parameters (`{name} joined` not `"Welcome " + name`) `[J]`; check plural handling uses a plural-aware library `[J]`.

## RTL and bidirectional text layout

- **Good looks like —** **Logical** (start/end) rather than physical (left/right) CSS properties. *Not relevant where RTL is not a target market — a per-change judgment, never a permanent N/A.*
- **Auditor checks —** If the product targets RTL markets, verify logical CSS properties (`margin-inline-start` not `margin-left`) are used `[J]`; check that icon/image assets mirror correctly in RTL mode `[J]`.

## Locale-dependent parsing bugs

- **Auditor checks —** Flag `sort()`/`.toLowerCase()` on user-visible text without locale param `[J]`; check regex word-boundary assertions (`\b`) against non-Latin input requirements `[J]`.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
