---
module: docs-traceability
title: Docs & Traceability
version: 0.1.1
status: draft
iso_25010: [maintainability]
load_scope:
  keywords: [docs, readme, comment, docstring, adr, architecture-tree]
  globs: ["docs/**", "**/*.md"]
last_reviewed: 2026-06-22
---

# Docs & Traceability — the change is explainable, the architecture is navigable

> **Loads when:** changes add, move, or remove files (ARCHITECTURE_TREE.md); introduce non-trivial decisions (DECISIONS.md); modify public APIs or non-obvious logic (docstrings/comments); or touch onboarding/runbook documentation.
> **ISO/IEC 25010:** maintainability · **Status:** draft · **v0.1.1**

Each entry below is one **auditable dimension**. Per change, the reviewer applies the
*relevant* ones **fully** (select-don't-skip), right-sized to the change — never
gold-plating an irrelevant one, never skipping a relevant one.

---

## Architecture-tree index currency

- **Good looks like —** `docs/claugentic-ARCHITECTURE_TREE.md` reflects the actual file layout with a one-line description per file. Every file add, move, or delete within scope triggers an update to the tree in the same commit.
- **Auditor checks —** If the architecture-tree gate is wired, run it (`python` / `python3` / `py` — `scripts/claugentic-check_architecture_tree.py`) and confirm exit 0 `[D]`; otherwise verify the tree by eye `[J]`. Either way, confirm any new file added in this change has a description entry `[J]`. `[J]` Does the entry — or any ledger line this change touches — RESTATE a value the file itself owns (a cap, a version, an enum list, a threshold)? An index entry is a **LOCATOR**; a restated value is an ungated second source of truth, and the honest measure is *how many places one change to that value must touch.* **The one exception, stated not silent:** a count that is genuine reader-value in *pitch* copy ("9 specialist agents") may stay — but it is kept **deliberately, with the drift risk accepted on the record**, never left standing by default; in an INDEX or a ledger it is always replaced by a locator.
- **Confidence —** `mixed`
- **Tradeoff (plain English) —** A current ARCHITECTURE_TREE means a new agent (or team member) can navigate the codebase without reading every file; the cost is updating one line per file change. A stale tree wastes agent context and misdirects exploration.
- **Sources —** the claugentic-dev-harness architecture-tree discipline (a first-class harness rule); Grady Booch "Object-Oriented Analysis and Design" on the value of navigable architecture documentation.
- **Motivating incident —** Plan 0041 Slice 4 (2026-08-13): a user-approved cap bump on one ledger had to be applied in **five** places — the config that owns the value, a byte-exact test pin, the architecture-tree entry, a decisions-ledger line that restated the number, and the dated record of *why* — while the same slice's own copy claimed a bump was "the same one-line edit." Nothing compared the restatements to the source. Trimming the tree entry to a locator ("the file IS the list — no values restated here") and replacing the ledger's restated numbers with a pointer took it to three; the copy was corrected to name the one remaining harness-self extra (a deliberate drift-detection pin, which stays).

---

## Decision traceability (DECISIONS.md)

- **Good looks like —** Every non-trivial choice (library selection, pattern choice, schema decision, API contract) is recorded as a dated one-liner in `docs/claugentic-DECISIONS.md` in the same commit that introduces the decision. Future agents consult it before re-litigating a past choice.
- **Auditor checks —** Review the diff for non-trivial decisions not yet recorded `[J]`; confirm `claugentic-DECISIONS.md` entry is dated and includes the rationale, not just the choice `[J]`.
- **Confidence —** `judgment` — what counts as "non-trivial" is a reviewer call.
- **Tradeoff (plain English) —** A decisions log prevents the same debate from happening three times with three different outcomes; it costs 30 seconds per decision. Without it, future agents re-open closed decisions and introduce inconsistency.
- **Sources —** Michael Nygard "Documenting Architecture Decisions" (https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — the original ADR essay; CLAUDE.md harness discipline.

---

## Load-bearing invariant traceability (INVARIANTS.md)

- **Good looks like —** A constraint that *must stay true or something breaks* — and whose rationale is non-obvious from the code — is recorded in `docs/claugentic-INVARIANTS.md` as a standing entry: the **invariant** (what must hold), the **why** (the rationale / blast radius if violated), and **dated provenance** (when, and what failure or near-miss, motivated it). The file is **lazily created** — it exists only once a repo has its first load-bearing invariant to record (an empty repo has none, and that is correct). It is **user-owned documentation, not a gate**: nothing mechanically verifies the invariants hold — the value is that the *next* change near a constraint reads *why before touching it*. Distinct from `docs/claugentic-DECISIONS.md` (a historical "what we chose and why," read when revisiting a choice): an invariant is **live** — read every time code in its blast radius changes.
- **Auditor checks —** `[J]` Did this change establish a non-obvious constraint that future code could silently violate (an ordering dependency, a "these two values must move together," an assumption a caller relies on) — and if so, is it captured in `docs/claugentic-INVARIANTS.md` with its why + dated provenance? `[J]` Did this change *touch the blast radius of an existing recorded invariant* — and if so, does it still hold (and is the entry still accurate)? `[J]` Is each entry genuinely load-bearing (a real "or it breaks"), not a restatement of a style preference or a decision that belongs in `claugentic-DECISIONS.md`?
- **Confidence —** `judgment` — there is no gate; whether a constraint is load-bearing, and whether a change threatens one, is a reviewer call. (Deliberately ungated: a stale or missing invariant entry is a documentation gap, not a build failure — wiring a check here would over-engineer a doc into machinery.)
- **Tradeoff (plain English) —** Writing down the handful of "this must stay true or X breaks" rules — with the story of the failure that taught you each one — means the next person (or agent) reads the landmine *before* stepping on it, instead of re-discovering it in production. The cost is a few lines per genuine invariant; the file stays tiny because most code carries none. Over-record it and it becomes noise nobody trusts — only truly load-bearing constraints earn an entry.
- **Sources —** the claugentic-dev-harness invariants discipline (independently converged on by multiple adopter projects); D. Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules" (the assumptions a module's clients rely on are exactly its load-bearing invariants); M. Nygard, "Documenting Architecture Decisions" (the sibling ADR practice this complements).
- **Motivating incident —** load-bearing constraints (e.g. the two version manifests that must move together) were caught only by eye or in production, because the "or it breaks" rationale lived in nobody's head but the original author's; the next change near the constraint re-discovered the landmine instead of reading it. Multiple adopter projects independently started a constraints log for exactly this.

---

## Docstrings and inline comments

- **Good looks like —** Public APIs, non-obvious algorithms, and "why not the obvious approach" reasoning carry docstrings or inline comments. Comments explain *why*, not *what* (the code says what). Trivial getters and self-evident code are not commented (noise reduction).
- **Auditor checks —** Confirm public functions/classes have docstrings `[D]` (enforced by lint where available); flag complex or counterintuitive logic that has no explanatory comment `[J]`; flag comments that merely restate the code `[J]`.
- **Confidence —** `mixed`
- **Tradeoff (plain English) —** Good docstrings let the next developer understand intent without running a debugger; the cost is a few extra lines. "Clean code reads like prose" is aspirational — reality has edge cases worth narrating. Over-commenting creates noise that ages badly.
- **Sources —** Robert C. Martin "Clean Code" ch. 4 "Comments"; Google Python Style Guide §3.8 "Comments and Docstrings" (https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

---

## Forward promises in prose — future tense, a named owner, and a falsifier

- **Good looks like —** Any sentence describing a capability a **later change** will wire — in a docstring, a comment, skill/README copy, an index entry, a ledger line, or an approval-gate summary — rides the **future tense**, **names the change that makes it true**, and is backed by a **mechanical falsifier** (`testing.md` → *Forward promises need a tripwire* owns that half: the strict expected-failure that fires when the promise is KEPT). Two halves of one rule — the tense protects today's reader, the tripwire protects tomorrow's author. A promise that is **abandoned** gets the same treatment as one that is kept: the sentence is rewritten, never left standing.
- **Auditor checks —** `[D]` Grep the diff's *prose* (docstrings, comments, `.md` copy, index entries, plan/approval text) for present-tense capability verbs — *is wired · consults · fires · surfaces · is visible at every …* — and for each ask: is it true **at the moment this change lands**, in a fresh clone? `[J]` If not, is it future-tense **and** does it name the change that wires it? `[D]` Does a falsifier exist for it? `[J]` **One correctly-hedged site is a signal, not a clean bill** — when a change hedges one forward reference, sweep every sibling that says the same thing.
- **Confidence —** `mixed` — the grep is mechanical; whether a sentence is true *today* is a reviewer call.
- **Tradeoff (plain English) —** Writing "once the next change lands, X is visible" instead of "X is visible" costs six words and keeps the document honest on the day it ships. The alternative is copy that is true only on the author's roadmap: every reader between now and then is misinformed, and if the later change is dropped, the sentence never becomes true at all.
- **Incident that motivated this (delete this rule once its cause is gone) —** Plan 0041, three consecutive slices (S3 · S4 · S5, 2026-08-13/14). Each slice's brand-new copy described a mechanism a **later slice of the same plan** would wire, in the present tense: a nudge's compensating control that did not exist; four sibling registrations beside one correctly-hedged one; and a gate docstring plus an approval-gate summary claiming a warning "is visible at every commit" when nothing had yet chained that gate. The review side caught it all three times — the reviewer bar item existed and still fired — which is precisely the evidence that the missing rule was an **authoring** rule, not a review one. It is filed here, in a module the implementer self-applies before handing off.
- **Sources —** cross-ref `testing.md` → *Forward promises need a tripwire* (the mechanical half of this rule) and *Decision traceability* above; the harness's honesty bar (never state a planned mechanism in the present tense).

---

## Reach, not residence — where a capability LIVES is not where it is USABLE

- **Good looks like —** Every instruction to run, import or invoke something is scoped to where that thing actually is **in the reader's world**, not where it lives in yours. **Distribution membership and repo-local presence are two facts** — in the package/image/payload/monorepo vs on disk in the reading project — and both are stated wherever the difference is actionable. A command that only resolves after a later delivery step rides the future-tense + falsifier rule (*Forward promises* above); the axis here is **location, not tense**, so a sentence can be perfectly present-tense-true about the payload and false for every reader. **Corollary — never invite a reader to substitute the tool's own copy.** A tool that resolves its subject from its own install location (`__file__`, `argv[0]`, the image workdir) measures **its** tree, not theirs; the honest output is "not present here", the honest design takes the subject as an explicit argument, and the honest verdict **names the subject it measured**.
- **Auditor checks —** `[D]` For every run/import instruction in reader-facing or shipped text, resolve the path **from a fresh clone of the reader's project** — does it exist there? `[J]` Are payload membership and repo-local presence stated as two facts wherever a reader could act on the difference? `[J]` Does any copy suggest pointing the tool's own copy at another tree? `[J]` Is a stated failure **symptom** the one the reader's deployment shape produces (installed vs dev checkout vs CI), or only the one measured in the author's checkout? `[D]` A correction applied "at all N sites" is a **class, not a count** — re-derive the site list by grep after the fix and quote it. **Wrapped lines hide members from a line-scoped grep — normalize before matching** (join the wrap markers: blockquote `> ` and list continuations, e.g. `` `\s*\n\s*(?:>\s*|[-*]\s+)?` `` → one space) and adjudicate the hits by hand. That normalization is a **SWEEP you read, never a gate**: as a standing mechanical predicate over prose, the paragraph-scoped window it needs fires on honest copy — measure the false-positive rate before proposing one, and record the refutation so it is not re-proposed. `[J]` Resolve every **deictic** in shipped instruction text — both the *person* kind (*this repo*, *here*, *your*, *ours*, *the current*) and the *spatial* kind (*above*, *below*, *the next section*, *just before this*) — in the **reader's** frame — an agent executing the file binds it to the reader's project, not yours. Name the subject explicitly ("the harness's own load profile — not measurements of your repo") wherever the two differ. **A block that MOVES carries its spatial deictics with it, and they are not verbatim-safe:** a relocation instruction that says both *"move it verbatim"* and *"place it after X"* is jointly unsatisfiable the moment the block points at X, so the spec states which wins and what the internal words become. *(0041 S9: an adopter note reading "a few references below resolve to the installed plugin" was moved above the very two lines it was written to correct — the diff was byte-faithful and the sentence became false; resolved by authorizing one word, "below" → "in this doc".)*
- **Confidence —** `mixed` — the path resolution is mechanical; which shape the reader is in is a judgment.
- **Tradeoff (plain English) —** Twelve words ("it ships in the plugin; a copy reaches your project when X lands; run it wherever the script is present") keep the sentence true for both audiences on the day it ships. The alternative is an instruction that errors for every reader, or worse a **green about someone else's project** — the one failure that reads as success.
- **Incident that motivated this (delete this rule once its cause is gone) —** Plan 0041 Slice 6 (2026-08-14/15). A gate script was reclassified to ship in the release payload, and **eight** shipped sentences then told adopters to run it. Measured in a scratch adopter project: the shipped command exited **2, `can't open file`** (nothing copies the script into a project yet — that is a later change), and the plugin's own copy, run from that project, returned a verdict **about the plugin's own tree**. The slice had faithfully implemented a spec line that was itself wrong, so a spec-conformant diff was no defense. The corollary earned its own correction one day later: the shipped symptom ("prints a green about the harness's ledgers") was only reproducible **in a dev checkout** — a real install has its config stripped, so its copy prints a *not configured* no-op — and the sweep that fixed "all four sites" left two more standing, both found by grep afterwards.
- **Sources —** cross-ref *Forward promises in prose* above (the tense half of the same honesty bar) and `testing.md` → *Forward promises need a tripwire*; the harness's release/init contract (what a distribution contains vs what a project receives).

---

## Onboarding and runbook documentation

- **Good looks like —** A new developer can clone and run the project by following `docs/SETUP.md` without asking anyone. Operational procedures (deploy, rollback, incident response, cron management) have a runbook reference. The README explains the project's purpose and entry points.
- **Auditor checks —** If setup steps changed, confirm `docs/SETUP.md` is updated in this commit `[J]`; verify any new operational procedure (cron, migration, flag toggle) has a runbook reference `[J]`.
- **Confidence —** `judgment` — completeness of onboarding docs is a reviewer call.
- **Tradeoff (plain English) —** Current setup docs cut onboarding from days to hours and enable incident response without the original author present; the cost is updating docs alongside the code change. Stale setup docs are worse than none — they actively mislead.
- **Sources —** Thoughtworks "Documentation" in "Building Microservices" (Sam Newman); Google SRE Book ch. 32 "The Evolving SRE Engagement Model" on runbook quality.

---

## Change explainability (commit and PR narrative)

- **Good looks like —** Commits follow Conventional Commits style (`feat:`, `fix:`, `chore:`, etc.) and the message explains *why*, not just *what*. PRs include a summary, test plan, and link to the relevant spec/issue. The change can be understood from its git history without reading the code.
- **Auditor checks —** Confirm commit messages are conventional and explain motivation `[J]`; verify PR description covers what changed, why, and how to test it `[J]`.
- **Confidence —** `judgment` — message quality is a reviewer call.
- **Tradeoff (plain English) —** Good commit messages make `git blame` a first-class debugging tool and turn code review into a narrative rather than a puzzle; the cost is two extra sentences per commit. A repo with poor commit history forces every future change to reverse-engineer intent from code alone.
- **Sources —** Conventional Commits specification v1.0.0 (https://www.conventionalcommits.org/); Chris Beams "How to Write a Git Commit Message" (https://cbea.ms/git-commit/).

---

## Authoring rules (the catalog meta-rules — do not delete)

- **Additive floor:** add dimensions as you discover them; **never delete** one. This catalog is meant to become "every standard we can think of."
- **Right-size:** apply only *relevant* dimensions per change (`KISS`/`YAGNI`); never skip a relevant one. Relevance is a per-change judgment — see `README.md`.
- **Novel patterns allowed** when they add clear value — justify (problem → why existing patterns fall short → benefit) and record in `claugentic-DECISIONS.md`. Unconventional ≠ wrong.
- **Every dimension carries a Confidence tag** so the harness can separate what it *proved* (deterministic gates) from what it *asserts* (judgment). Trust the oracle, not the model's word.
