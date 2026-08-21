#!/usr/bin/env python3
"""Resolve every inbound SECTION citation into a set of target docs — a dead anchor is exit 1.

Deterministic dev-side gate (no LLM), built for the leanness passes: when a cut deletes or
renames a `##` section, every other file that cited that section by name silently becomes a
liar. This scans the whole tracked corpus for citations that NAME a target file AND a section
inside it, resolves each against the target's LIVE headings, and fails loud on the ones that
no longer land.

    python scripts/check_standards_anchors.py                    # default: docs/claugentic-standards
    python scripts/check_standards_anchors.py --list             # ...and print every resolved citation
    python scripts/check_standards_anchors.py --targets docs/claugentic-WORKFLOW.md

HARNESS-SELF, run-gate, not hook-wired (like `scripts/check_versions_synced.py`): it reasons
about THIS repo's docs, so it is stripped from the release payload and never delivered to an
adopter. Run it in the Definition-of-Done gate suite of any slice that cuts prose.
See docs/claugentic-WORKFLOW.md -> Definition of Done.

WHAT IT RECOGNIZES (the parseable forms — precision over reach, deliberately):
  * `target.md#section-slug`                    — the anchor-link form
  * `target.md` -> *Section name*               — either arrow glyph, any delimiter or none
  * `target.md` -> "Section name"               — quoted (this is how engine/*.js cites)
  * wrapped across lines, in prose, in a Markdown table cell, in a Python docstring, in a
    `//` comment, in YAML frontmatter — line breaks plus one leading list/comment/quote
    marker are normalized to a space BEFORE matching, so a citation that wraps mid-name
    still resolves.

WHAT IT DOES NOT RECOGNIZE — the honest scope, so a zero is never misread as proof:
  * a section named in prose with NO arrow and NO anchor ("the module's Reading a module
    section"). Measured on this repo before the rule was written: admitting the no-arrow
    emphasized/quoted form produced 51 candidates, essentially all noise (code string
    literals, architecture-tree descriptions), so it is refused — a gate that cries wolf
    gets ignored.
  * a file referenced without its `.md` ("the WORKFLOW's DoD"), an abbreviation, or any
    paraphrase. These are invisible here BY CONSTRUCTION.
  * a bare basename that is ambiguous across the repo and is not a sibling of the citing
    file: attributing it would be a guess, so it is SKIPPED — and every skip is PRINTED,
    never swallowed.
  * a landmark that is not an ATX heading. Sections are `#`-headings here; a citation of a
    BOLD sub-anchor (`docs/claugentic-WORKFLOW.md` -> *The escape-valve ladder*, a `**bold**`
    label inside Definition of Done) reports as dead against that target, correctly saying
    "not a heading there". That is a real limit when this gate is pointed at WORKFLOW —
    measured on 2026-08-20: 9 of its inbound citations name bold landmarks, not headings.
    Resolving bold landmarks is a separate feature; it is deliberately not built.
  This is why the plan calls the anchor sweep a named manual pass ASSISTED by this script:
  the script owns the mechanical forms, a reader owns the paraphrases.

WHY A SELF-TEST RUNS ON EVERY INVOCATION. A scanner whose pattern silently stops matching
reports a clean zero — the worst failure mode a gate has, because it looks like success.
So every run first re-proves the scanner against KNOWN_POSITIVES: two real citations of one
real section, in the two hardest forms (an `#anchor` link in Markdown, an ASCII arrow inside
a Python docstring). If either probe stops resolving, this gate fails EVEN IF the sweep it
was asked for is clean, and says which probe died. The probes are repo-facts, not config:
they are the canary, and making them tunable would let a future edit quietly disarm it.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TARGETS = ("docs/claugentic-standards",)

# The self-test canary (see the module docstring). Each tuple is
# (citing file, cited target, section that must resolve, form) — all four verified live.
KNOWN_POSITIVES = (
    ("docs/RELEASE_CHECKLIST.md", "docs/claugentic-WORKFLOW.md", "Definition of Done", "anchor"),
    (
        "scripts/claugentic-check_doc_budgets.py",
        "docs/claugentic-WORKFLOW.md",
        "Definition of Done",
        "arrow",
    ),
)
PROBE_TARGET = "docs/claugentic-WORKFLOW.md"

# A line break plus at most ONE leading list/comment/quote marker (the marker must be followed
# by a space, so a continuation line opening with `*emphasis*` keeps its delimiter) collapses
# to a single space. This is what makes a citation that wraps mid-section-name resolvable.
_WRAP = re.compile(r"\n[ \t]*(?:(?:[-*>+]|//|\#{1,6}|\d+\.)[ \t]+)?[ \t]*")

# Both arrow glyphs, after at most a short run of closing punctuation/backticks.
_ARROW = re.compile("[\\s`*_\"'\u201c\u201d\\)\\],:;\u00b7\u2014]{0,12}(?:\u2192|->)[ \t]*")
_ANCHOR = re.compile(r"#([A-Za-z0-9][A-Za-z0-9\-_]*)")

# How far past the arrow a section name may run before we stop looking.
MAX_SECTION_CHARS = 120
# Openers that delimit a section name, mapped to their closers.
_DELIMS = (("**", "**"), ("*", "*"), ("`", "`"), ('"', '"'), ("\u201c", "\u201d"), ("_", "_"))
# Where an UNDELIMITED section name ends.
_BARE_END = re.compile("[.,;:!?()\\[\\]{}|]|\\s\u2014\\s|\\s--\\s|\\s\u00b7\\s")


class ScanError(RuntimeError):
    """A precondition the scan cannot proceed without (fail loud, never a silent pass)."""


@dataclass(frozen=True)
class Citation:
    source: str
    line: int
    target: str
    section: str
    form: str
    kind: str = "exact"


@dataclass
class ScanResult:
    citations: list[Citation] = field(default_factory=list)
    dead: list[tuple[Citation, list[str]]] = field(default_factory=list)
    ambiguous: list[tuple[str, int, str]] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    sources: set[str] = field(default_factory=set)


def _repo_root() -> Path:
    """The repo root, derived from THIS file's location — never the caller's CWD."""
    return Path(__file__).resolve().parent.parent


def _tracked_files(root: Path) -> list[str]:
    """Every tracked path, from git. Fails loud: no git, no repo, or an empty corpus."""
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:  # git missing or not executable
        raise ScanError(f"could not run `git ls-files` in {root} ({exc}) — is git installed?") from exc
    if proc.returncode != 0:
        raise ScanError(f"`git ls-files` failed in {root}: {proc.stderr.strip() or 'no output'}")
    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not files:
        raise ScanError(f"`git ls-files` listed nothing in {root} — the corpus cannot be empty.")
    return files


def resolve_targets(root: Path, specs: list[str]) -> list[str]:
    """Expand each --targets spec (file, directory, or glob) to repo-relative target paths.

    A spec that matches nothing is an error, not an empty sweep: a typo'd path must never
    read as "zero dead citations".
    """
    out: list[str] = []
    for raw in specs:
        spec = raw.replace("\\", "/").rstrip("/")
        path = root / spec
        if path.is_dir():
            found = sorted(p.relative_to(root).as_posix() for p in path.glob("*.md"))
        elif path.is_file():
            found = [Path(spec).as_posix()]
        else:
            found = sorted(p.relative_to(root).as_posix() for p in root.glob(spec) if p.is_file())
        if not found:
            raise ScanError(f"--targets {raw!r} matched no file under {root}.")
        out.extend(found)
    return sorted(dict.fromkeys(out))


def _read(root: Path, rel: str) -> str | None:
    """Text of a tracked file, or None if it is not UTF-8 text (binary — counted, not hidden)."""
    try:
        return (root / rel).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError as exc:
        raise ScanError(f"{rel} could not be read ({exc}).") from exc


def _slug(heading: str) -> str:
    """GitHub-style anchor slug for a heading."""
    text = re.sub(r"[`*_]", "", heading).strip().lower()
    text = re.sub(r"[^a-z0-9 \-]", "", text)
    return re.sub(r"\s+", "-", text).strip("-")


def _norm_name(text: str) -> str:
    """Canonical form of a section NAME for comparison (case, emphasis, quotes, punctuation)."""
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub("[`*_\"]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" .,;:!?-\u2014").lower()


def headings(text: str) -> list[str]:
    """Every ATX heading in `text`, skipping fenced code blocks."""
    out: list[str] = []
    fence: str | None = None
    for raw in text.split("\n"):
        stripped = raw.strip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            continue
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        match = re.match(r"#{1,6}\s+(.*\S)\s*$", raw)
        if match:
            out.append(match.group(1))
    return out


def name_variants(head: str) -> set[str]:
    """Every spelling one heading is legitimately cited by, canonicalized.

    Three real conventions in this repo: the full text; without a leading stage number
    ("9. The learning loop" cited as "The learning loop"); and without a trailing
    ` — clause` / ` (parenthetical)` gloss.
    """
    forms = {head.strip(), re.sub(r"^\d+[a-zA-Z]?[.)]\s*", "", head.strip())}
    for form in list(forms):
        forms.add(re.split("\\s\u2014\\s|\\s--\\s|\\s\\(", form, maxsplit=1)[0])
    return {n for n in (_norm_name(f) for f in forms) if n}


def heading_index(text: str) -> tuple[set[str], set[str]]:
    """(citable name forms, anchor slugs) for one target's live headings."""
    names: set[str] = set()
    slugs: set[str] = set()
    for head in headings(text):
        slugs.add(_slug(head))
        names |= name_variants(head)
    slugs.discard("")
    return names, slugs


def normalize_wraps(text: str) -> tuple[str, list[int]]:
    """Collapse line-wraps to spaces; return (normalized text, 1-based source line per char)."""
    out: list[str] = []
    lines: list[int] = []
    line = 1
    i = 0
    end = len(text)
    while i < end:
        if text[i] == "\n":
            match = _WRAP.match(text, i)
            span_end = match.end() if match else i + 1
            out.append(" ")
            lines.append(line)
            line += text.count("\n", i, span_end)
            i = span_end
            continue
        out.append(text[i])
        lines.append(line)
        i += 1
    return "".join(out), lines


def extract_section(norm: str, pos: int) -> tuple[str, str, bool] | None:
    """(form, section name, delimited?) cited right after a filename ending at `pos`, or None.

    `delimited` says the author marked the name's end (emphasis, backticks, quotes) — the
    resolver is stricter with those, because an UNdelimited name runs into the sentence
    around it and has to be trimmed back to a heading.
    """
    anchor = _ANCHOR.match(norm, pos)
    if anchor:
        return ("anchor", anchor.group(1), True)
    arrow = _ARROW.match(norm, pos)
    if not arrow:
        return None
    rest = norm[arrow.end() : arrow.end() + MAX_SECTION_CHARS]
    for opener, closer in _DELIMS:
        if rest.startswith(opener):
            shut = rest.find(closer, len(opener))
            if shut > len(opener):
                return ("arrow", rest[len(opener) : shut], True)
    stop = _BARE_END.search(rest)
    name = (rest[: stop.start()] if stop else rest).strip()
    name = name.strip("*`_\"'")
    return ("arrow", name, False) if name else None


def _name_pattern(targets: list[str]) -> re.Pattern[str]:
    """One alternation over every citable spelling of every target — longest (path) first."""
    spellings: list[str] = []
    for rel in targets:
        spellings.append(rel)
        spellings.append(rel.rsplit("/", 1)[-1])
    ordered = sorted(dict.fromkeys(spellings), key=len, reverse=True)
    body = "|".join(re.escape(s) for s in ordered)
    return re.compile(rf"(?<![A-Za-z0-9_\-/])({body})")


def _edge(longer: str, shorter: str) -> bool:
    """True when `longer` starts with `shorter` AND breaks on a word boundary there."""
    return longer.startswith(shorter) and not longer[len(shorter) : len(shorter) + 1].isalnum()


def _match_kind(probe: str, pool: set[str], allow_prefix: bool, delimited: bool) -> str | None:
    """How a cited name lands on the live headings: "exact", "prefix", "bare", or None (dead).

    PREFIX (heading longer than the citation) is admitted for PROSE citations only, because
    this repo really does cite the leading clause of a long heading (`testing.md` -> *Code
    the suite cannot EXECUTE*, whose heading continues ", pinned as text"). BARE (citation
    longer than the heading) is admitted only for an UNdelimited name, which by construction
    runs on into its sentence ("-> Definition of Done carries the obligation"): a live
    heading at its head is the citation. Both break on a WORD boundary, so a cut that
    shortens the cited part still goes red, and both are counted separately in the summary
    rather than passed off as exact. An `#anchor` link must be EXACT — a prefix navigates
    nowhere.
    """
    if not probe:
        return None
    if probe in pool:
        return "exact"
    if allow_prefix and any(_edge(live, probe) for live in pool):
        return "prefix"
    if not delimited and any(_edge(probe, live) for live in pool):
        return "bare"
    return None


def _suffix_match(spelled: str, targets: set[str]) -> str | None:
    hits = [rel for rel in targets if rel.endswith(spelled)]
    return hits[0] if len(hits) == 1 else None


def _attribute(
    spelled: str, source: str, targets: set[str], by_basename: dict[str, list[str]]
) -> str | None:
    """Which file a citation's spelling names — or None when only a guess would answer.

    The path form wins outright. A bare basename resolves to a SIBLING of the citing file
    first (how every standards module cites its README), else to the one tracked file that
    carries that basename. An ambiguous bare basename is refused, never guessed.
    """
    if "/" in spelled:
        return spelled if spelled in targets else _suffix_match(spelled, targets)
    owners = by_basename.get(spelled, [])
    sibling = source.rsplit("/", 1)[0] + "/" + spelled if "/" in source else spelled
    if sibling in owners:
        return sibling
    if len(owners) == 1:
        return owners[0]
    if not owners:
        hits = [rel for rel in targets if rel.rsplit("/", 1)[-1] == spelled]
        return hits[0] if len(hits) == 1 else None
    return None


def scan(root: Path, targets: list[str], corpus: list[str]) -> ScanResult:
    """Resolve every recognized section citation into `targets` across `corpus`."""
    target_text = {rel: _read(root, rel) for rel in targets}
    missing = sorted(rel for rel, text in target_text.items() if text is None)
    if missing:
        raise ScanError(f"target file(s) unreadable as UTF-8 text: {', '.join(missing)}")
    index = {rel: heading_index(text) for rel, text in target_text.items() if text is not None}
    by_basename: dict[str, list[str]] = {}
    for rel in corpus:
        by_basename.setdefault(rel.rsplit("/", 1)[-1], []).append(rel)
    pattern = _name_pattern(targets)
    target_set = set(targets)

    result = ScanResult()
    for rel in corpus:
        text = _read(root, rel)
        if text is None:
            result.unreadable.append(rel)
            continue
        if not pattern.search(text.replace("\n", " ")):
            continue
        norm, line_of = normalize_wraps(text)
        for match in pattern.finditer(norm):
            spelled = match.group(1)
            found = extract_section(norm, match.end())
            if found is None:
                continue
            form, section, delimited = found
            line = line_of[match.start()]
            target = _attribute(spelled, rel, target_set, by_basename)
            if target is None:
                result.ambiguous.append((rel, line, f"`{spelled}` -> {section!r}"))
                continue
            if target not in target_set:
                continue
            names, slugs = index[target]
            pool = slugs if form == "anchor" else names
            probe = _slug(section) if form == "anchor" else _norm_name(section)
            kind = _match_kind(probe, pool, form != "anchor", delimited)
            cite = Citation(rel, line, target, section, form, kind or "dead")
            if kind:
                result.citations.append(cite)
            else:
                near = difflib.get_close_matches(probe, sorted(pool), n=3, cutoff=0.5)
                result.dead.append((cite, near))
            result.sources.add(rel)
    return result


def self_test(root: Path, corpus: list[str]) -> list[str]:
    """Re-prove the scanner against KNOWN_POSITIVES. Returns problem lines (empty = healthy)."""
    try:
        result = scan(root, [PROBE_TARGET], corpus)
    except ScanError as exc:
        return [f"SELF-TEST BROKEN: the probe scan could not run ({exc})."]
    problems: list[str] = []
    for src, target, section, form in KNOWN_POSITIVES:
        # An anchor citation spells the section as a SLUG, an arrow citation as prose — compare
        # each in its own alphabet, or the probe fails on a citation that in fact resolved.
        same = (lambda a, b: _slug(a) == _slug(b)) if form == "anchor" else (
            lambda a, b: _norm_name(a) == _norm_name(b)
        )
        landed = any(
            c.source == src and c.target == target and c.form == form and same(c.section, section)
            for c in result.citations
        )
        if not landed:
            problems.append(
                f"SELF-TEST BROKEN: the {form} probe no longer resolves — {src} cites "
                f"{target} -> {section}. Either that citation moved (repoint the probe in "
                "KNOWN_POSITIVES) or the scanner stopped matching its form (fix the scanner). "
                "Until then NO result from this gate can be trusted, including a clean one."
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail loud on inbound section citations that no longer resolve."
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=list(DEFAULT_TARGETS),
        metavar="PATH",
        help="files, directories, or globs to check citations INTO (default: %(default)s)",
    )
    parser.add_argument(
        "--list", action="store_true", help="print every resolved citation, not just problems"
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    try:
        corpus = _tracked_files(root)
        targets = resolve_targets(root, args.targets)
        probe_problems = self_test(root, corpus)
        result = scan(root, targets, corpus)
    except ScanError as exc:
        print(f"PROBLEM: {exc}")
        return 1

    for rel, line, what in result.ambiguous:
        print(f"SKIPPED (ambiguous basename — attribute by hand): {rel}:{line} {what}")
    if result.unreadable:
        print(f"note: {len(result.unreadable)} tracked file(s) skipped as non-UTF-8 (binary).")
    if args.list:
        for cite in sorted(result.citations, key=lambda c: (c.target, c.source, c.line)):
            print(
                f"  {cite.source}:{cite.line} -> {cite.target} :: {cite.section}"
                f"  [{cite.form}/{cite.kind}]"
            )

    for problem in probe_problems:
        print(f"PROBLEM: {problem}")
    for cite, near in result.dead:
        hint = f" Closest live heading(s): {', '.join(near)}." if near else " No close heading."
        print(
            f"PROBLEM: {cite.source}:{cite.line} cites {cite.target} -> {cite.section!r}, "
            f"which is not a heading there.{hint}"
        )

    loose = sum(1 for c in result.citations if c.kind != "exact")
    print(
        f"{len(result.citations)} section citation(s) into {len(targets)} target file(s) "
        f"from {len(result.sources)} source file(s); {loose} resolved on a word-boundary "
        f"partial (prefix/bare); {len(result.dead)} dead."
    )
    if probe_problems or result.dead:
        return 1
    print("OK: every recognized inbound section citation resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
