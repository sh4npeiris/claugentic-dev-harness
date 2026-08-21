---
# ── Module contract (copied from _TEMPLATE.md) ──
module: product-ux
title: Product & UX
status: draft
iso_25010: [interaction-capability]
load_scope:
  keywords: [ui, ux, component, page, screen, design, frontend, button, form, layout, accessibility, a11y, responsive]
  globs: ["**/components/**", "**/pages/**", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.css"]
---

# Product & UX — is this a complete, humane, accessible product surface (not just working code)?

> **Loads when:** a change touches a user-facing surface — a component, page, screen, form, layout, styling, or any interactive frontend.
> Method, tags, honesty register: `README.md` → *Reading a module*.
> Judgment is backed by numbers wherever possible — the **objective UX signals** a `ux-reviewer` measures close this module.

---

## Information architecture & navigation

- **Auditor checks —** `[J]` nav model consistent across screens (same affordances in the same places). `[J]` every screen answers "where am I / where can I go". `[J]` labels match user language (card-sort/tree-test evidence if available). `[D]` route names/links resolvable — no orphan routes, no broken internal links (link-check in CI).

## Design system & design tokens (single source of truth for look-and-feel)

- **When the system comes from an external source (mechanism-agnostic) —** Build UI to that project's **REAL** components/tokens, never invented ones. The source may be a code component-library, a synced design-system record, **or** a Claude Code `/design-sync` flow (**one option, never required**); the per-project design-language record (`docs/claugentic-PRODUCT.md` → *Per-project design language*) says which. **Invoking any such sync is model-upheld and degrades gracefully** — when unavailable, the record is populated **manually**. The **craft floor applies ON TOP** either way: the external system supplies the *system*, this module supplies the *quality* (the anti-slop `[D]` floor + the motion baseline + the `[J]` craft ceiling in *Aesthetic & motion craft* below).
- **Auditor checks —** `[D]` grep the diff for raw hex/rgb/px literals in component/CSS files where a token exists (`no-hardcoded-design-values` / Stylelint custom rule). `[J]` semantic tokens over primitives at the component layer (intent, not raw value). `[J]` an existing component reused rather than a near-duplicate created. `[J]` the new component consistent with siblings (states, sizes, spacing scale).

## Loading / empty / error states (every async surface has all three)

- **Auditor checks —** `[J]` all three states render for each async call in the diff. `[D]` no data-fetching component lacks a loading/error branch (lint rule / data-layer convention — e.g. query hooks forced to handle `isLoading`/`isError`). `[J]` the empty state is actionable (CTA), not a dead end. `[J]` error messages specific and recoverable (no swallowed errors, no `[object Object]`).

## Optimistic UI & rollback

- **Auditor checks —** `[J]` the mutation updates local state before the server responds where latency would otherwise hurt. `[J]` explicit rollback on error (cache revert / previous-value restore). `[J]` destructive/irreversible actions excluded from optimism (confirmed/pessimistic instead). `[D]` where the library has optimistic APIs (TanStack Query `onMutate`/`onError`), the rollback handler is present.

## Perceived performance & micro-interactions

- **Auditor checks —** `[J]` every actionable element gives instant visual feedback. `[J]` operations >1s show progress, >10s allow cancel. `[D]` `prefers-reduced-motion` honored (media-query present where animation is used — grep/lint). `[J]` motion meaningful (orienting/causal) and short (≈150–300ms), not gratuitous.

## Visual hierarchy, consistency & brand (look-and-feel)

- **Auditor checks —** `[J]` a single clear primary action and a sensible scan order. `[D]` raw design-value lint — the shared Stylelint `no-hardcoded-design-values` gate (see *Design system & tokens*). `[J]` spacing/type/color drawn from the scale with intent (semantic tokens, not literals that happen to match). `[J]` matches the established brand/voice and sibling screens. `[J]` alignment and grouping clean (Gestalt proximity/similarity), with adequate whitespace.

## Aesthetic & motion craft (is it beautiful and does it feel alive — not just usable?)

- **Good looks like —** The surface is **crafted, not merely correct**: a **distinctive voice** rather than a consistent-but-generic template look; interactions **feel alive** (crafted easing, purposeful choreography); there is at least one **signature moment**. Craft is the *ceiling* above the floors set by *Visual hierarchy* (clarity), *Perceived performance* (feedback) and *Accessibility* (reach) — **never instead of them.** Expressive motion may never override `prefers-reduced-motion` and must stay inside the Core-Web-Vitals budget; the floors win every time.
- **Motion baseline (the *shape* of alive-feeling motion; taste stays `[J]`) —**
  - *Easing by intent —* ease-**OUT** for entrances (`power2.out` ≈ the ~90% UI workhorse; `power3.out` for emphasis) · ease-**IN** for exits · `power2.inOut` for menus · `back.out` for playful · **linear ONLY for spinners/progress**, never for spatial movement. **Bounce/elastic are personality-gated** (dated on a corporate/premium surface, fine for playful) — never a default. Industry cubic-béziers: MD3 Standard `(0.2,0,0,1)` · MD3 Emphasized `(0.05,0.7,0.1,1)` · Apple HIG `(0.25,0.1,0.25,1)`.
  - *Durations (ms) —* tooltip 80–120 · button 120–180 · icon 150–250 · card 200–350 · modal 300–400 · page 400–600 · dramatic 600–1200. **Exits ≈ 65–75% of the entrance;** duration scales with travel distance; interaction ceilings **hover <100ms / press <150ms.** (`[D]`-checkable against a diff's transition/animation values.)
  - *Choreography —* stagger 50–100ms (group total <500ms) · one easing family across a group · direction follows meaning · layer motion for depth — three layers (primary 100% · secondary 30–50% at 50–100ms offset · ambient 10–20%) so foreground leads and background settles (a craft reference for how layered motion *feels*, `[J]` — **not** a mechanically-audited ratio) · **≤1/3 of elements in active motion at once** · related elements move together with an offset (follow-through).
  - *Meaning over decoration —* the **property carries the meaning** (position = arrival/direction · scale = importance); **two animated properties is the sweet spot; never opacity-only for an important state change.**
  - *Reduced-motion (extends the `[D]` `prefers-reduced-motion` floor) —* fade instead of slide · cut duration 50%+ · no auto-loops · static (not moving) parallax; avoid vestibular triggers; **never convey critical info via motion alone.**
  - *(Draft baseline — model-asserted pending a promotion-time verification round, per `README.md`. Disney's 12 principles are the principled scaffold.)*
- **Auditor checks —** `[J]` does this surface read as **refined and distinctive**, with viewing-pleasure, or merely consistent-and-WCAG-clean? (a taste critique — the honest verdict is *"refined / generic / cheap-feeling,"* a reviewed bet, **never** a claim it "is beautiful") `[J]` do state-changes and transitions feel **crafted and alive** (intentional easing/choreography), or abrupt/dead? `[J]` is there a **signature moment** worth noticing, or is every surface flat-neutral? `[J]` easing smells — `linear` on **spatial** movement, or bounce/elastic on a **premium/corporate** surface (personality mismatch)? `[J]` is an important state change carried **opacity-only** (no property that carries the meaning)? `[D]` the *floor* craft must not break: `prefers-reduced-motion` honored (grep/lint — see *Perceived performance*) **and** the reduced-motion path degrades safely (fade-not-slide · no auto-loops · static parallax · no critical info by motion alone — HIGH-severity if animation is added without it), **CLS < 0.1 / INP < 200ms** not regressed by added motion (Lighthouse/CWV — see *Objective UX signals*), design values from tokens not literals (`no-hardcoded-design-values`), transition/animation **durations inside the baseline bands** above (out-of-band is a smell to flag, not a hard fail) — these prove motion is **safe, consistent, performant**, never that it is **beautiful**.
- **Anti-slop detectors (enrich the `[D]` FLOOR — each fires "no-slop pattern present/absent," NEVER "is beautiful") —** `[D]` where the adopter has tooling wired, else `[J]`: no **gray-on-color** text (low-contrast label over a colored fill) · no **card-nesting** · no **overused-font monoculture** (one default system/SaaS typeface doing all the work) · no **purple→blue "SaaS-slop" gradient** as the default flourish · no **cramped padding** · no **undersized targets** (the 24×24 floor — see *Accessibility*) · no **skipped heading hierarchy** (h1→h3 with no h2). A detector proves a slop *pattern* is absent — **not** a beauty certificate; distinctiveness stays the `[J]` ceiling.
- **Honesty register —** Satisfaction is irreducibly `[J]` — a reviewed bet, never proven. The `[D]` checks prove only the floor craft must not break. The harness can force the question, check the floor, and route the verdict to a human; it can **never certify "beautiful."**
- **Incident —** A slice can pass **every** existing gate — tests green, accessibility AA, all three async states present, Core Web Vitals in budget — and still ship a surface that is **flat, generic and forgettable**, because nothing in the bar ever asked *"is this crafted / does it feel alive."* Until this dimension, `product-ux.md` scoped itself to *"complete, humane, accessible,"* framed motion only as a **risk to minimize** and named visual polish only as the **negative** — so beauty fell in the **seam** between the `product-designer` agent (which routed all look-and-feel here) and this standard (which checked only functional conformance). Surfaced by the 2026-06-29 experience-craft review; this dimension closes the seam.

## Ethical engagement (habit-forming without dark patterns)

- **Auditor checks —** `[J]` no flow relies on tricking, shaming, or trapping the user to hit a metric. `[J]` cancel/unsubscribe/opt-out as discoverable and easy as the opposite action. `[J]` urgency/scarcity/social-proof cues truthful. `[J]` consent defaults user-favorable (no pre-ticked data sharing). `[D]` cookie/consent flows meet "reject as easy as accept" where regulated (consent-mode/CMP config check).

## User-flow completeness (no dead ends)

- **Auditor checks —** `[J]` trace the flow end-to-end: a way forward AND a way out from every state. `[J]` the success state is explicit with a next action, not a silent close. `[J]` cancel/back non-destructive and predictable. `[J]` an interrupted flow resumes without silent data loss. `[D]` all CTA targets resolve (link/route check — see *Information architecture*).

## Edge-case & resilient UX (offline / slow / flaky network)

- **Auditor checks —** `[J]` an offline/connection-loss path exists (detect + message + recover), not an always-online assumption. `[D]` double-submit prevented (button disabled / request de-duped while pending). `[J]` layout survives extreme content (overflow handled, no clipping/overlap). `[J]` long lists windowed/paginated (no unbounded DOM). `[J]` network timeouts bounded with user-visible retry.

## Accessibility (WCAG 2.2 AA — keyboard, contrast, screen reader, focus)

- **Good looks like —** **WCAG 2.2 Level AA.** Contrast **≥4.5:1** normal text / **≥3:1** large text and UI components. The 2.2-specific criteria, most often missed: **focus not obscured** (2.4.11) · **focus appearance** (2.4.13) · **dragging alternative** (2.5.7) · **target size ≥ 24×24 CSS px** (2.5.8) · **consistent help** (3.2.6) · **redundant entry** avoided (3.3.7) · **accessible authentication** (3.3.8).
- **Auditor checks —** `[D]` automated axe-core / Lighthouse a11y scan passes with zero violations in changed views (CI gate — catches ~30–40% of issues) `[D]` contrast ratios meet AA (token/contrast linter or axe) `[D]` images/icons have alt/accessible names; form controls have associated labels (axe/eslint-plugin-jsx-a11y) `[J]` keyboard-only walkthrough: tab order logical, focus visible & not obscured, no traps, all actions reachable `[J]` screen-reader pass (NVDA/VoiceOver): names/roles/states announced, async changes announced via live regions `[D]` interactive targets ≥ 24×24px (computed-size check) `[J]` no information conveyed by color alone.

## Responsive & cross-device/-browser

- **Good looks like —** Mobile-first and fluid, never fixed-pixel; ≥16px body text on mobile and user zoom respected.
- **Auditor checks —** `[J]` holds at key widths (≈320, 768, 1024, 1440) with no overflow/overlap/clipping. `[D]` content reflows at 320px / 400% zoom without horizontal scroll (WCAG 1.4.10). `[J]` touch targets and hit areas adequate on touch devices. `[J]` tested on the supported browser matrix (no engine-specific breakage). `[D]` viewport meta present, zoom not disabled (`user-scalable=no` forbidden — grep).

## Objective UX signals (what a ux-reviewer measures)

- **Auditor checks —** `[D]` Lighthouse Perf ≥ 90 and A11y ≥ 90 on changed routes (Lighthouse CI gate, mobile profile) `[D]` Core Web Vitals thresholds met — LCP < 2.5s, INP < 200ms, CLS < 0.1 (Lighthouse/PSI lab; web-vitals field at p75) `[D]` axe-core scan = 0 violations (CI — see *Accessibility* dimension) `[J]` Nielsen 10-heuristic critique completed for the changed flow with severities recorded `[J]` keyboard + screen-reader walkthrough notes attached for non-trivial UI.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
