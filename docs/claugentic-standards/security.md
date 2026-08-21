---
# ── Module contract: every docs/claugentic-standards/ module copies this frontmatter ──
module: security
title: Security & Privacy
status: draft
iso_25010: [security]
load_scope:
  keywords: [auth, authz, login, token, password, secret, crypto, session, encryption, pii, injection, csrf, ssrf, cors, dependency]
  globs: ["**/auth/**", "**/*login*", "**/middleware/**", "**/*.env*", "**/security/**"]
---

# Security & Privacy — keep untrusted input, attackers, and regulators from turning code into a breach

> **Loads when:** a change touches authentication/authorization, sessions/tokens, secrets or crypto, input handling or query/command construction, cross-origin/redirect/outbound-fetch behavior, deserialization, dependencies, or any personal/regulated data (PII, student, health, payment).
> Method, tags, honesty register: `README.md` → *Reading a module*.
> **Relevance here is threat-driven** — set by what the change **exposes** (a new endpoint, a new sink, a new data field), never by how big the diff is. A one-line change can be in scope.

---

## Authentication (proving who the caller is)

- **Good looks like —** A memory-hard salted KDF (Argon2id / scrypt / bcrypt); minimum length **≥12, target ≥15** for single-factor; **no arbitrary composition rules**; a **breached-password blocklist** check (NIST SP 800-63B). Nothing about the credential in the URL, query string, or logs.
- **Auditor checks —** `[D]` grep for weak hash calls (`md5`, `sha1(`, `hashlib.sha256(password`), hardcoded credential literals, and passwords logged. `[D]` a dependency/secrets scan flags committed credentials. `[J]` is authN delegated to a vetted lib/IdP rather than hand-rolled? `[J]` are reset tokens single-use + expiring? `[J]` is the failure path uniform (no user-enumeration via message or timing)? `[J]` is throttling present on auth endpoints?

## Authorization, least privilege & object-level access (IDOR / BOLA)

- **Auditor checks —** `[J]` for each new endpoint/handler, is there an authZ check *and* an ownership/tenant check before the resource is read or mutated? `[J]` can changing an `id` in the request reach another user's/tenant's row? `[D]` grep for routes/handlers added without passing through the auth middleware/decorator (where the framework makes that greppable). `[J]` are roles least-privilege, not "admin for convenience"? `[J]` are authZ checks server-side (not just hidden UI)?

## Session & token management

- **Auditor checks —** `[D]` grep cookie set-calls for missing `HttpOnly`/`Secure`/`SameSite`; grep JWT verify calls for unpinned/`none` algorithms or skipped verification. `[J]` are sessions rotated on login and killed on logout/password-change? `[J]` are token claims (`exp`,`aud`,`iss`) actually validated, not just decoded? `[J]` is token lifetime short with revocation possible?

## Secrets management

- **Auditor checks —** `[D]` secret-scanner (gitleaks / trufflehog / detect-secrets) over the diff **and** history is clean; `.gitignore` covers `.env*`/keys. `[D]` grep for high-entropy strings, `AKIA`, `-----BEGIN ... PRIVATE KEY-----`, `password=`, `api_key=` in tracked files. `[J]` are secrets sourced from a manager/env rather than literals? `[J]` is rotation possible and per-env separation real?

## Input validation at trust boundaries

- **Good looks like —** **Canonicalize before validating.** Allowlist, server-side, fail-closed — never silently coerced. Uploads store outside the web root under generated, non-executable names.
- **Auditor checks —** `[J]` is there a schema/validator at each new boundary, and is it allowlist-based? `[D]` where a schema lib is used (pydantic/zod/JSON-Schema/bean-validation), grep confirms new DTOs/endpoints are typed/validated rather than reading raw `request.body`/`params` directly. `[J]` is invalid input rejected (not silently defaulted/truncated)? `[J]` are uploads constrained and stored safely?

## Injection prevention (SQL/NoSQL · command · path · XSS · template/LDAP)

- **Auditor checks —** `[D]` grep for the danger sinks: f-string/`+`/`%`/`.format` building SQL, `os.system`/`subprocess(... shell=True)`/`eval`/`exec` with variable input, `innerHTML`/`dangerouslySetInnerHTML`/`v-html`, `Path`/`open` joined to raw user input. `[D]` SAST (semgrep / CodeQL / Bandit) on the diff shows no injection findings. `[J]` for each flagged sink, is the input trusted or properly parameterized/encoded/sanitized? `[J]` is encoding correct for the *output context*?

## CSRF, CORS, clickjacking & cross-origin posture

- **Good looks like —** On cookie-authenticated apps CSRF protection is a token **and** `SameSite` — **SameSite alone is not sufficient.** A token-/header-authenticated API **documents** why CSRF tokens are unnecessary.
- **Auditor checks —** `[D]` grep CORS config for wildcard origin, `Origin` reflection, or `*` + credentials; grep for missing CSP/HSTS/frame-ancestors where a server config exists. `[J]` do new state-changing routes have CSRF protection (or a justified exemption for header-auth APIs)? `[J]` is the CORS origin list specific and intentional?

## SSRF & outbound-request safety

- **Good looks like —** Deny-by-default allowlist of hosts/schemes; block private/loopback/link-local/metadata ranges (`127.0.0.0/8`, `169.254.169.254`, `10/172.16/192.168`, IPv6 ULA/`::1`); validate the **resolved IP after DNS** (DNS-rebinding); disable or constrain redirects; never echo raw upstream responses.
- **Auditor checks —** `[J]` does any new code fetch a URL derived from user input? If so, is there an allowlist + private-range block + redirect control? `[D]` grep for HTTP clients (`requests.get`, `fetch(`, `urllib`, `httpx`) taking a variable URL near request input. `[J]` is the post-resolution IP validated (rebinding-safe), not just the string?

## Safe deserialization & dynamic execution

- **Auditor checks —** `[D]` grep for `pickle.load`, `yaml.load(` without `SafeLoader`, `eval(`, `exec(`, `BinaryFormatter`, `unserialize(`, `node-serialize` on any externally-sourced data. `[J]` is the deserialized data's origin trusted/signed, or is a safe loader + schema in place?

## Dependency & supply-chain hygiene

- **Auditor checks —** `[D]` lockfile present and updated with the change; dependency-audit gate is green (no unaddressed critical/high). `[D]` CI runs an SCA scan. `[J]` is each newly-added dependency justified (real need, maintained, reasonable footprint, acceptable license)? `[J]` are pins exact, not floating `latest`?

## Build & release pipeline authorization (who may publish, and with what token)

- **Good looks like —** Workflow-level permissions **read-only by default**, the write/publish grant scoped to the single publishing job. Releasability is checked, not assumed: the published ref is an **ancestor of trunk** and **the tag matches the manifest version**. Publishing runs the **one tested build path**, never a re-implementation in YAML.
- **Auditor checks —** `[J]` Does any job hold more authorization than its work needs — in particular, does the job running tests or installing dependencies hold the publish credential? `[D]` Grep for workflow-level write `permissions:` and job-level overrides. `[J]` Is there a check that the ref being published actually landed on the trunk? A *reverse* guard ("trunk ⊆ HEAD") does **not** establish it. `[D]` Does the publish job `needs:` the gate job? `[J]` Does the workflow re-implement build/publish logic the repo already has tested code for? `[J]` Are floating `@vN` / `install -g` dependencies inside the credentialed job named as an accepted risk, or silently assumed pinned?
- **Incident —** 0041 S2 (2026-08-12): the **spec itself** prescribed `permissions: contents: write` at *workflow* level and the implementation matched it faithfully — arming the gates job (full suite + an unpinned global npm install) with a write-capable token. The security lens refuted the **spec**, not the diff. Two more findings sat in the same hole: the base-ancestry guard was *reverse* inclusion, so a never-merged descendant could be tagged and published (fixed with `git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/main`), and a floating `npm install -g` ran inside the credentialed publish job, documented nowhere. The verdict's own words: *"dimension the spec missed: tag-commit authorization — no gate covered it."*

## Secure defaults & misconfiguration

- **Auditor checks —** `[D]` grep for `DEBUG = True`, `app.run(debug=True)`, stack-trace-to-client handlers, disabled CSRF (`CSRF_ENABLED=False` or equivalent), `chmod 777`, container `USER root`. `[J]` are errors generic to the client while detailed server-side? `[J]` are admin endpoints protected and unused features off? `[J]` is TLS enforced end-to-end? (Disabled-TLS-verification grep — `verify=False`/`rejectUnauthorized:false` — see Cryptography correctness dimension.)

## Cryptography correctness

- **Good looks like —** Authenticated symmetric ciphers (AES-GCM / ChaCha20-Poly1305), TLS 1.2+, SHA-256+, a password KDF for passwords — via standard libraries, never home-grown. CSPRNG only (`secrets`, `crypto.randomBytes`, `SecureRandom`). Keys managed and purpose-separated; constant-time comparison for secrets/MACs.
- **Auditor checks —** `[D]` grep for `MD5`/`SHA1`/`DES`/`RC4`/`ECB`, `Math.random()` used for security tokens, `verify=False`/`rejectUnauthorized:false`/disabled cert checks, hardcoded keys/IVs. `[J]` is an authenticated cipher used and is the construction standard (right mode, fresh IV, CSPRNG)? `[J]` are keys managed and comparisons constant-time?

## PII minimization & data classification

- **Auditor checks —** `[J]` does the change collect/store/transmit new personal data, and is each field actually needed for the feature? `[J]` is sensitive data minimized, masked where displayed/exported, and not duplicated into logs/caches/analytics? `[J]` is the most-sensitive data avoided unless essential and specially handled?

## Encryption in transit & at rest

- **Auditor checks —** `[D]` grep for `http://` to sensitive endpoints, disabled TLS verification, sensitive columns/files written without encryption where the platform expects it. `[J]` is at-rest encryption enabled for the new data store/field and are backups covered? `[J]` are keys managed/rotated (not embedded), and is the most-regulated data handled per its standard?

## Retention, deletion & data-subject rights

- **Auditor checks —** `[J]` does new persisted data have a retention/deletion story, or is it written somewhere it can never be removed? `[J]` does an erasure request reach this data everywhere it lands (replicas, backups, logs, indexes, third parties)? `[J]` is there a hard-delete path, not only soft-delete, for regulated data?

## Consent, lawful basis & purpose limitation

- **Auditor checks —** `[J]` does new processing/sharing have a lawful basis, and where consent applies, is it opt-in, granular, recorded, and revocable? `[J]` is data being used only for its original purpose (no scope creep into new analytics/ML/marketing)? `[J]` do trackers/third-party shares respect consent state?

## Regulatory compliance mapping (GDPR · FERPA · HIPAA · PCI DSS)

- **Good looks like —** Where a regime applies its controls are **met rather than assumed**, and data-residency / cross-border-transfer rules are respected.
- **Auditor checks —** `[J]` which regimes does this data/audience trigger (student → FERPA, health → HIPAA, EU resident → GDPR, card data → PCI), and are that regime's controls present? `[J]` are processor/BAA/data-transfer obligations covered for any third party touched? `[J]` is PCI-prohibited data (full track, CVV) never stored?

## Audit trails & accountability

- **Good looks like —** The security-significant event set: authN success/failure · authZ denials · privilege changes · access to regulated records · admin actions · config/security changes · data exports and deletions — each with *who, what, when, from where*, a correlation ID, and tamper-resistance. **Audit logs themselves carry no secrets, tokens, or raw PII.**
- **Auditor checks —** `[J]` are the security-significant events for this change logged with actor/action/timestamp/source and a correlation ID? `[D]` grep to confirm the audit log lines don't include passwords/tokens/secrets/raw PII (overlaps with the logging-hygiene dimension below). `[J]` are audit logs tamper-resistant and retained per the applicable regime?

## Sensitive-data hygiene — never log or commit real user data

- **Auditor checks —** `[D]` grep added log/print/tracker calls for whole-request/whole-object dumps, password/token/PII fields, `Authorization`/`Cookie` headers; scan committed fixtures/seeds for realistic PII or live credentials. `[D]` secret-scanner over the diff (shared with secrets management). `[J]` does any new log statement risk emitting sensitive data under real inputs? `[J]` is test/seed data synthetic?

> Authoring rules `_TEMPLATE.md` · governance `README.md`
