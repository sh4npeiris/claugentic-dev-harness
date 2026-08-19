# 0043 — Close the spec gaps that `/product gap` measured

- **Status:** Draft — the findings are MEASURED; the slicing below is a proposal.
- **Source:** `/product gap` run 2026-08-19 against `docs/claugentic-PRODUCT_SPEC.md`, scripted `engine/audit.js` criteria mode via the Workflow tool. `COMPLETE` — 7/7 criteria swept, 40 agents, 0 errors.
- **Verification:** 25 verified · 7 **refuted and dropped** (the adversarial check working) · `crossModel: False` — **same-model judges**, so treat precision as a weaker signal than recall.
- **Honest scope, from the skill's own contract:** this read the code against the spec — **it did not run the app.** Runtime checking is the QA workflow's job.

> **Why this file exists:** the engine rendered these as a **120,687 B** backlog fence. Writing that into `docs/claugentic-ROADMAP.md` — where `/audit` and `/product gap` are wired to write — would have taken it to **132,200 B against its own 14,000 B cap**. That contradiction is now fixed (CHANGELOG → *Unreleased*), but the lesson stands: **work belongs in a plan, not in a ledger.**

> **THE FINISH LINE IS THIS SPEC, NOT THE AUDIT.** Gap mode is **bounded** — 7 criteria, 24 expectations. Meet them and it returns clean; that is a falsifiable done. `/audit` measures against an ever-growing standards catalog and is **unbounded by design** — never use it as a completion criterion.

---

## The findings, as measured

### Tier 1 — the trust register itself  (7 findings)

- [ ] **[PS-1] Setup's report can say it overwrote nothing on a run that overwrote your files** · `bug`
  - **What:** If you pick "Replace my code map" during setup, or setup rewrites your commit-hook script or appends to .gitignore/.gitattributes, the first line of the report still tells you nothing of yours was changed or overwritten. The honest disclosure sits several paragraphs later, or nowhere. The headline is computed from two narrow report groups instead of from the real question - did we write anything the user owns - so the most-read line says the opposite of what happened. (Merged with the separate 'I changed nothing' finding: same defect, same edit site.)
  - **Where:** `skills/init/SKILL.md:1172-1179` · `skills/init/SKILL.md:1180-1188` · `skills/init/SKILL.md:1273-1276` · `skills/init/SKILL.md:1197-1201`
  - **Cost:** High impact - the report's most-read line can be flatly false, on the two paths that touch user-owned files. Low effort - one branch condition in skills/init/SKILL.md:1172-1188, computed from a 'wrote nothing at all this run' predicate.

- [ ] **[PS-2] The product backlog never says the check never ran your app - and calls a clean run "sound"** · `bug`
  - **What:** The promise is that gap mode always states it read the code statically and did not run the product. It says so only in the chat message at the end; the backlog written into your ROADMAP - the thing you actually read weeks later - never says it. Worse, a clean run prints "Sound on the audited dimensions", which reads as "your product matches its spec" from a check that never executed a line of the product.
  - **Where:** `engine/audit.js:1076` · `engine/audit.js:149` · `engine/audit.js:156` · `engine/audit.js:1011`
  - **Cost:** High impact - a durable, unqualified soundness claim from a static-only check. Low effort - one constant plus a gap-mode branch in the fence renderer, and the same clause in the skill-owned heading.

- [ ] **[PS-3] Answering "keep all" can write a finding you already dismissed back into your backlog** · `bug`
  - **What:** Findings you dismissed are correctly hidden from the checklist you are shown, but the "keep all" answer routes to writing the engine's original, unfiltered backlog text - which still contains them. So the documented guarantee that a dropped finding stays dropped breaks precisely on the runs where the dismissal memory did its job. Nothing in the skill flags this as a case that needs the re-render path.
  - **Where:** `skills/audit/SKILL.md:325` · `skills/audit/SKILL.md:331` · `docs/claugentic-WORKFLOW.md:221` · `engine/audit.js:1228`
  - **Cost:** High impact - breaks a headline guarantee and quietly undoes the user's own decision. Low effort - one routing clause in the SELECT phase of the audit skill, mirrored in the workflow doc.

- [ ] **[PS-3] The backlog never prints the stable id that resuming and dismissing both depend on** · `bug`
  - **What:** When a run stops early and you re-run it, the engine carries forward already-confirmed findings only if each one has its internal key - and the rendered backlog never writes that key out. So a re-run either drops findings that were already confirmed, or the orchestrator invents a key from the title and produces a duplicate; an already-verified verdict can also silently downgrade to "not yet verified". The same missing key is why the dismissal memory has to match on model-rewritten titles, so a slight wording change resurrects something you dismissed. (Merged with the separate dismissal-identity finding - one key, one fix.)
  - **Where:** `engine/audit.js:1102` · `engine/audit.js:983` · `skills/audit/SKILL.md:221` · `tests/workflows/audit.test.mjs:1372`
  - **Cost:** High impact - silent loss of verified findings on every resumed run, and unreliable dismissals. Low effort - render the key with each item and add a render-parse-merge round-trip test.

- [ ] **[PS-5] Build asserts the reviewer was the same model on runs where it could not tell** · `bug`
  - **What:** The trust disclosure has three honest states, but the build engine folds them to two: whenever the reviewing model's family cannot be resolved, it states flatly that the reviewer and the builder are the same model family - a fact the run never established. The correct "could not resolve" wording is a dead constant here, and the QA stage's honest version is discarded on the way up. Verify, QA and audit all implement the three states correctly; build is the one that regresses it, and a test currently pins the wrong string.
  - **Where:** `engine/build-item.js:515-524` · `engine/build-item.js:109-116` · `engine/build-item.js:961-971` · `engine/build-item.js:1016-1017`
  - **Cost:** High impact - a false statement in the exact surface built to prevent over-claiming. Low effort - make the fold three-state like its siblings, thread the child tags through, re-point one test.

- [ ] **[PS-5] The QA summary always says findings were dropped by a cross-model re-check** · `bug`
  - **What:** The headline sentence hardcodes "dropped by the cross-model re-check" no matter what the run concluded, so a same-family or unidentifiable run returns that sentence sitting beside its own contradicting disclosure on the same object. The audit engine already solves this by substituting the disclosure for the claim and never emitting both.
  - **Where:** `engine/qa.js:1254` · `engine/qa.js:1241-1245` · `engine/qa.js:1283-1284`
  - **Cost:** High impact - the sentence a user actually reads over-claims the one thing the trust register exists to under-claim. Very low effort - make one clause conditional and add a test that a non-confirmed run never contains the phrase.

- [ ] **[PS-7] A budget grace flag is never removed, so that check can stay switched off for good** · `bug`
  - **What:** A ledger can be let through over budget with a grace flag, and three separate places state that only the condense command clears it. The condense procedure never mentions removing it - and the one line that does mention the flag says to leave it alone. So a graced ledger gets condensed, the flag survives the condition it was granted for, and the next real breach downgrades to a warning and passes silently instead of failing the commit.
  - **Where:** `skills/condense/SKILL.md:151` · `skills/condense/SKILL.md:166` · `scripts/claugentic-check_doc_budgets.py:106` · `scripts/claugentic-check_doc_budgets.py:538`
  - **Cost:** High impact - a mechanically enforced gate silently stops enforcing, permanently and invisibly. Very low effort - one closing step in the condense re-check loop, disambiguated from the cap-bump rung.


### Tier 2 — correctness  (14 findings)

- [ ] **[PS-1] The per-line length limit on the code map is enforced but never explained** · `bug`
  - **What:** Setup does install the check that rejects over-long code-map lines, but its report enumerates only two things that can block a commit and this is not one of them, and the map it generates carries no note of the limit - unlike this repo's own map, whose header states both the working target and the hard ceiling. The first refused commit arrives with no context and nothing in the repo explains the rule.
  - **Where:** `skills/init/SKILL.md:1209-1216` · `skills/init/SKILL.md:336-340` · `scripts/claugentic-check_architecture_tree.py:141` · `scripts/claugentic-check_architecture_tree.py:177-205`
  - **Cost:** Medium impact - a confusing first failure with no in-repo explanation. Low effort - one clause in the report's abort-cause list, one line in the generated map header.

- [ ] **[PS-2] Gap mode never tells you which parts of your spec the code does deliver** · `feature`
  - **What:** The promise is a criterion-by-criterion met / partial / missing report; the engine reports only surviving problems. "Met" is therefore indistinguishable from "the check quietly produced nothing", there is no representation of "partial" at all, and the per-criterion verdict the reviewer already returns is collected and thrown away. The coverage roll-up that would express this exists for the other mode and is explicitly switched off here.
  - **Where:** `engine/audit.js:1501` · `engine/audit.js:1037` · `engine/audit.js:811` · `engine/audit.js:951`
  - **Cost:** High impact - the reader cannot tell checked-and-clean from never-checked, which is the core value of the mode. Medium effort - build a criterion-keyed coverage report reusing the existing coverage renderer rather than forking it.

- [ ] **[PS-2] Spec-gap findings are pruned by a filter written for engineering audits** · `bug`
  - **What:** Before you see them, gap findings pass through a step told to cut "marginal nice-to-haves" and told to add an "establish a test baseline" item. A genuinely promised-but-missing feature can therefore be cut with no trace - and with no per-criterion report, that criterion then simply looks met - while an engineering to-do that maps to no acceptance criterion at all can appear in your product backlog.
  - **Where:** `engine/audit.js:617` · `engine/audit.js:626` · `engine/audit.js:1378` · `engine/audit.js:1399`
  - **Cost:** High impact - true spec gaps can vanish silently and untraceable items can appear. Low effort - branch the synthesis prompt on gap mode: drop the test-baseline injection, replace the right-sizing instruction with a spec-conformance one.

- [ ] **[PS-2] Gap mode spawns the reviewer agent in a mode that agent's own contract does not define** · `bug`
  - **What:** The engine fans out with a "product-gap" instruction, but the reviewer agent documents exactly four modes and this is not one of them - and its own mode-inference rule sends a scope with no named module to the whole-scope red-team posture instead. Its "read your assigned module, its dimensions are your bar" instruction has no referent, and its output shape has no criterion-level verdict, which is also why the met/partial/missing report has nothing to build on.
  - **Where:** `engine/audit.js:1310` · `engine/audit.js:557` · `.claude/agents/lens-reviewer.md:10` · `.claude/agents/lens-reviewer.md:22`
  - **Cost:** Medium-high impact - reviewers can adopt the wrong posture, and the contract mismatch blocks the coverage report. Low effort - document the fifth mode, extend the inference sentence, state the verdict shape.

- [ ] **[PS-3] A run that ran out of budget mid-double-check still reports itself as complete** · `bug`
  - **What:** The complete-versus-partial status is derived only from the search stage. If the budget ran out while re-checking findings, the status line still says COMPLETE, the resume note never fires, and there is nothing in the resume list for a re-run to pick up - while the items themselves carry "re-run to confirm". The engine does compute a "verification incomplete" flag, and it is referenced nowhere else in the repo.
  - **Where:** `engine/audit.js:789` · `engine/audit.js:1508` · `engine/audit.js:1076` · `engine/audit.js:150`
  - **Cost:** Medium-high impact - the run reports a completeness it does not have, and the re-check never happens. Low effort - render an already-computed field, add it to the documented return, widen the resume note.

- [ ] **[PS-4] The build engine's refusal message points at a mode that no longer exists** · `bug`
  - **What:** When the engine refuses an unattended run it tells you to run the item in "checkpoint mode". That control was explicitly replaced by the watched, decision-gated run; the word appears nowhere in the build skill, whose own mapping for the same status says something different. The retired vocabulary also survives in three product docs and in stale cross-references to a numbered step the skill no longer has.
  - **Where:** `engine//build-item.js:776` · `engine//build-item.js:786` · `engine//build-item.js:210` · `engine//build-item.js:767`
  - **Cost:** Medium impact - the user is pointed at a control that does not exist, in a refusal message. Low effort - two string changes plus a vocabulary sweep across the docs and the dangling locators.

- [ ] **[PS-4] "Not green - here is the residual" can be followed by an empty residual** · `bug`
  - **What:** If the review or QA stage crashed rather than finding a problem, the run can end saying the build is not green while listing nothing failing and never mentioning that a stage failed to run. The engine already computes a "stage could not run" list for exactly this case, but the terminal report never passes it through, so an infrastructure failure reaches the user as a mystery instead of a named cause.
  - **Where:** `engine//build-item.js:996` · `engine//build-item.js:1001` · `engine//build-item.js:1028` · `engine//build-item.js:485`
  - **Cost:** Medium-high impact - the one report that must explain a non-green run can explain nothing. Low effort - thread an existing computed value into two call sites plus a unit test.

- [ ] **[PS-4] The build engine claims it never touches git, then tells the implementer to branch and commit** · `bug`
  - **What:** The script itself runs no git command, but the first standing rule it hands the implementer is to work in an isolated worktree and commit on a work branch - and a commit is git history. The narrower claim (never lands, merges or pushes) is true, just as reassuring, and is what the product spec already says. It is the engine's own two shipped strings that over-reach, which this repo's honesty rule forbids.
  - **Where:** `engine//build-item.js:5` · `engine//build-item.js:51` · `engine//build-item.js:602` · `engine//build-item.js:610`
  - **Cost:** Medium impact - an over-claimed guarantee in shipped text, against the repo's own stated standard. Very low effort - reword two strings to what is actually true.

- [ ] **[PS-4] The canned refusal about missing tests cannot describe its most common cause** · `bug`
  - **What:** One unlock condition is "tests that actually assert the behaviour, not tests that merely run the code" - two distinct failure modes. Its fixed sentence can only say "I found no tests exercising this". When tests exist but only smoke-run the touched code, the refusal states something untrue about what was found, in the one message whose entire job is to name the evidence checked. Both sibling conditions already carry a two-way slot.
  - **Where:** `skills//build//SKILL.md:106` · `skills//build//SKILL.md:93`
  - **Cost:** Medium impact - a false evidence statement inside the criterion's own honesty surface. Very low effort - give the line the same two-way slot its siblings have.

- [ ] **[PS-5] The cross-model claim ignores the reviewers that actually threw findings out** · `bug`
  - **What:** The claim is computed only from the reviewers of findings that survived. A reviewer that disproved a finding - including a forced same-model fallback reviewer - changed your backlog and is never counted, so a run can report "cross-model confirmed" when the review that actually decided something was not. The skill states the claim more broadly than the code supports.
  - **Where:** `engine/audit.js:755-777` · `engine/audit.js:1485` · `engine/qa.js:1224-1228` · `engine/qa.js:1170`
  - **Cost:** Medium-high impact - a reachable path to an over-stated trust claim. Medium effort - carry the dropped findings' reviewer self-reports into the fold, or narrow the stated claim to match the computation.

- [ ] **[PS-5] Only the audit run has to tell you its cross-model outcome; verify, QA and build do not** · `feature`
  - **What:** The spec promises every judged run reports its cross-model outcome. Audit bakes the line into the written backlog and instructs the orchestrator to echo it. For verify, QA and build the value is only a field on a result object with no instruction anywhere to say it out loud, so a same-family or unresolved run can be reported to you as a clean pass with the disclosure never reaching a human.
  - **Where:** `skills/build/SKILL.md:143-162` · `docs/claugentic-WORKFLOW.md:122` · `docs/claugentic-WORKFLOW.md:187` · `engine/verify.js:758`
  - **Cost:** Medium-high impact - true at the data layer, unevidenced at the surface a user reads, on three of four pipelines. Low effort - one instruction line in the build skill and two in the workflow doc; no engine change.

- [ ] **[PS-6] Doctor flags things it then gives you no way to choose for fixing** · `bug`
  - **What:** Findings like "a landed plan is still sitting there" or "your commit hook is not wired" are reported with their own flag status, but the step where you pick what to fix presents only warnings, breaches and substantive items. Two of doctor's four just-do-it fixes can only ever come from a flag, so they can never be ticked and therefore never applied - and the enumeration is narrower than the pipeline contract it points at.
  - **Where:** `skills/doctor/SKILL.md:344-347` · `skills/doctor/SKILL.md:330-334` · `skills/doctor/SKILL.md:355-364` · `docs/claugentic-WORKFLOW.md:217`
  - **Cost:** Medium-high impact - a whole documented user action is unreachable. Very low effort - widen one sentence to name the flag class, keeping the two report-only carve-outs the skill already makes.

- [ ] **[PS-7] The over-budget alarm sends people to shave the wrong material** · `bug`
  - **What:** When a ledger blows its cap, the message the developer sees says to merge superseded entries to git history. The condense procedure says the primary target is landed build records and that they must never be preserved, with superseded entries second - and it names "preserve the landed entries, then nibble unrelated live rules" as the classic under-delivery. So the alarm points at the exact inversion the feature exists to prevent, and the same wording is echoed in three other adopter-facing places, one of which also calls the pass content-preserving when it is not.
  - **Where:** `scripts/claugentic-check_doc_budgets.py:168` · `scripts/claugentic-check_doc_budgets.py:169` · `scripts/claugentic-check_doc_budgets.py:7` · `docs/claugentic-WORKFLOW.md:176`
  - **Cost:** Medium-high impact - the trigger surface everyone reads first contradicts the procedure it triggers. Low effort - reword two constants and three echoes, ideally making them procedure-neutral pointers.

- [ ] **[PS-7] The over-budget message never names the command that fixes it** · `bug`
  - **What:** The docs claim a budget signal is a ramp to the condense command and never a dead end, and the skill claims to be what a warning offers you. The message actually printed contains no mention of the command, and the commit-time path prints nothing else - which is the most common place people meet it, and deliberately so. The offer exists only inside a different command's flow.
  - **Where:** `scripts/claugentic-check_doc_budgets.py:168` · `scripts/claugentic-check_doc_budgets.py:169` · `skills/condense/SKILL.md:16` · `docs/claugentic-WORKFLOW.md:177`
  - **Cost:** Medium impact - the promised ramp is missing exactly where the signal fires. Very low effort - append the command to two strings and pin it with a one-line test so it cannot silently drop out.


### Tier 3 — polish  (4 findings)

- [ ] **[PS-2] The proposal reviewer can edit the very spec it is told never to write into** · `refactor`
  - **What:** The rule that a proposal is a question and never spec content until you adopt it is enforced only by asking the agent nicely - it still holds file-write tools, including on the spec. The write capability is genuinely needed by its other mode, not this one, and the folding is the orchestrator's job. Other adversarial roles in this harness are read-only by construction, so this one is the odd exception.
  - **Where:** `.claude/agents/product-designer.md:4` · `.claude/agents/product-designer.md:47` · `.claude/agents/product-designer.md:103` · `skills/product/SKILL.md:89`
  - **Cost:** Low-medium impact - removes a class of accident rather than fixing an observed failure. Low effort - split the agent file, or spawn the review mode with a read-only tool set and say the rule is structural there.

- [ ] **[PS-2] The harness's own ROADMAP says it has no product spec, while the spec sits next to it** · `bug`
  - **What:** The hand-authored placeholder block asserts that no product spec exists for the harness; the spec file exists, is dated, and contains the very criteria this audit ran on. That block is the one place a reader looks to see whether this check has ever run here, and the heading also omits the ownership and signpost clauses the skill prescribes for an inserted block.
  - **Where:** `docs/claugentic-ROADMAP.md:24` · `docs/claugentic-ROADMAP.md:22` · `docs/claugentic-PRODUCT_SPEC.md:1` · `skills/product/SKILL.md:199`
  - **Cost:** Low impact - a self-contradicting dogfood example, no functional consequence. Very low effort - replace the placeholder text and bring the heading to the prescribed form.

- [ ] **[PS-3] On a resumed run the backlog lists more findings than its own tallies count** · `bug`
  - **What:** The summary counts are computed before findings carried over from the earlier pass are merged in, so carried items appear in the list with nothing counting them, and the count of false alarms dropped in the earlier pass resets to zero - erasing part of the trust signal. The numbers at the bottom stop reconciling with the list above them, and this skew is documented nowhere.
  - **Where:** `engine/audit.js:1485` · `engine/audit.js:1493` · `engine/audit.js:1054` · `engine/audit.js:1077`
  - **Cost:** Low-medium impact - resumed runs only, and the direction of the skew is under-counting rather than over-claiming. Low effort - compute the summary after the merge, or add a carried-over term and a cumulative dropped count.

- [ ] **[PS-3] The summary calls disproved findings "couldn't be confirmed", which is what it calls the ones it kept** · `bug`
  - **What:** Findings the re-check actively disproved are reported as dropped because they "couldn't be confirmed", while findings that genuinely could not be confirmed are kept and labelled with nearly the same words in the same block. One phrase means two opposite things in one report, and it understates the rigour that was actually applied.
  - **Where:** `engine/audit.js:1066` · `engine/audit.js:151` · `engine/audit.js:171`
  - **Cost:** Low-medium impact - a wording collision in the trust register, no wrong behaviour. Very low effort - reword one string and pin the new wording in the renderer's tests.


---

## Proposed slicing (NOT approved — Stage 2/3 decides)

1. **The `init` report honesty defect** (PS-1 T1) — the headline says *"I did NOT change any of your code or overwrite your own files"* on the one path that overwrites a user file. Highest severity: most-read line, flagship command, and it is false.
2. **The remaining T1 trust-register defects** (PS-2, PS-3, PS-5, PS-7) — every one is the harness claiming more than it did. This is the product's **stated invariant**, so they outrank everything below.
3. **T2 correctness** — resume/dismiss ids, the prune filter, the refusal messages.
4. **T3 polish** — wording, and one stale self-description.

**Do not batch 1–2 with 3–4.** The trust-register defects are the product's core claim; the rest is quality.
