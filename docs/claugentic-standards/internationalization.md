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

- **Auditor checks —** `[D]` source files and DB columns are UTF-8 · `[J]` file/stream open calls pass an explicit encoding · `[J]` no `latin-1`/`ascii` assumption in string manipulation.

## Locale-aware date, time, and number formatting

- **Auditor checks —** `[D]` wire formats are ISO 8601 for dates and integers/decimals for numbers · `[J]` display formatting passes a locale/format parameter · `[J]` no locale-dependent `parseInt`/`parseFloat`/`strptime` without explicit locale handling.

## Timezone handling

- **Auditor checks —** `[D]` DB timestamps UTC-typed (`timestamptz` or equivalent) · `[J]` no raw `+offset` arithmetic in business logic — use `pytz`/`dateutil`/`Intl.DateTimeFormat`/`Temporal` · `[J]` user timezone read from a preference, not inferred from server locale.

## Translatable strings

- **Auditor checks —** `[D]` grep hardcoded user-visible string literals outside translation files · `[J]` interpolation uses named parameters (`{name} joined`, not `"Welcome " + name`) · `[J]` plurals handled by a plural-aware library.

## RTL and bidirectional text layout

- **Good looks like —** **Logical** (start/end) rather than physical (left/right) CSS properties. *Not relevant where RTL is not a target market — a per-change judgment, never a permanent N/A.*
- **Auditor checks —** `[J]` logical CSS properties (`margin-inline-start`, not `margin-left`) where the product targets RTL · `[J]` icon/image assets mirror correctly in RTL mode.

## Locale-dependent parsing bugs

- **Auditor checks —** `[J]` no `sort()`/`.toLowerCase()` on user-visible text without a locale param · `[J]` regex word boundaries (`\b`) checked against non-Latin input requirements.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
