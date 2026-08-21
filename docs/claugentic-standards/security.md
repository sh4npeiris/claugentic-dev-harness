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
> **Relevance here is threat-driven** — set by what the change **exposes** (a new endpoint, a new sink, a new data field), never by diff size. A one-line change can be in scope.

---

## Authentication (proving who the caller is)

- **Good looks like —** A memory-hard salted KDF (Argon2id / scrypt / bcrypt); minimum length **≥12, target ≥15** for single-factor; **no arbitrary composition rules**; a **breached-password blocklist** check (NIST SP 800-63B). Nothing about the credential in the URL, query string, or logs.
- **Auditor checks —** `[D]` grep for weak hash calls (`md5`, `sha1(`, `hashlib.sha256(password`), hardcoded credential literals, logged passwords. `[D]` a dependency/secrets scan flags committed credentials. `[J]` authN delegated to a vetted lib/IdP, not hand-rolled. `[J]` reset tokens single-use + expiring. `[J]` uniform failure path (no user-enumeration by message or timing). `[J]` throttling on auth endpoints.

## Authorization, least privilege & object-level access (IDOR / BOLA)

- **Auditor checks —** `[J]` every new endpoint/handler has an authZ check *and* an ownership/tenant check before the resource is read or mutated. `[J]` changing an `id` in the request cannot reach another user's/tenant's row. `[D]` grep for routes/handlers added without the auth middleware/decorator, where the framework makes that greppable. `[J]` roles least-privilege, not "admin for convenience". `[J]` authZ server-side, not hidden UI.

## Session & token management

- **Auditor checks —** `[D]` grep cookie set-calls for missing `HttpOnly`/`Secure`/`SameSite`; grep JWT verify calls for unpinned/`none` algorithms or skipped verification. `[J]` sessions rotated on login, killed on logout/password-change. `[J]` token claims (`exp`,`aud`,`iss`) validated, not just decoded. `[J]` short lifetime with revocation possible.

## Secrets management

- **Auditor checks —** `[D]` secret-scanner (gitleaks / trufflehog / detect-secrets) over the diff **and** history is clean; `.gitignore` covers `.env*`/keys. `[D]` grep for high-entropy strings, `AKIA`, `-----BEGIN ... PRIVATE KEY-----`, `password=`, `api_key=` in tracked files. `[J]` secrets sourced from a manager/env, not literals. `[J]` rotation possible and per-env separation real.

## Input validation at trust boundaries

- **Good looks like —** **Canonicalize before validating.** Allowlist, server-side, fail-closed — never silently coerced. Uploads store outside the web root under generated, non-executable names.
- **Auditor checks —** `[J]` a schema/validator at each new boundary, allowlist-based. `[D]` where a schema lib is used (pydantic/zod/JSON-Schema/bean-validation), grep confirms new DTOs/endpoints are typed/validated rather than reading raw `request.body`/`params`. `[J]` invalid input rejected, not silently defaulted/truncated. `[J]` uploads constrained and stored safely.

## Injection prevention (SQL/NoSQL · command · path · XSS · template/LDAP)

- **Auditor checks —** `[D]` grep the danger sinks: f-string/`+`/`%`/`.format` building SQL, `os.system`/`subprocess(... shell=True)`/`eval`/`exec` with variable input, `innerHTML`/`dangerouslySetInnerHTML`/`v-html`, `Path`/`open` joined to raw user input. `[D]` SAST (semgrep / CodeQL / Bandit) on the diff shows no injection findings. `[J]` each flagged sink is trusted input or properly parameterized/encoded/sanitized. `[J]` encoding correct for the *output context*.

## CSRF, CORS, clickjacking & cross-origin posture

- **Good looks like —** On cookie-authenticated apps CSRF protection is a token **and** `SameSite` — **SameSite alone is not sufficient.** A token-/header-authenticated API **documents** why CSRF tokens are unnecessary.
- **Auditor checks —** `[D]` grep CORS config for wildcard origin, `Origin` reflection, or `*` + credentials; grep for missing CSP/HSTS/frame-ancestors where a server config exists. `[J]` new state-changing routes have CSRF protection (or a justified header-auth exemption). `[J]` CORS origin list specific and intentional.

## SSRF & outbound-request safety

- **Good looks like —** Deny-by-default allowlist of hosts/schemes; block private/loopback/link-local/metadata ranges (`127.0.0.0/8`, `169.254.169.254`, `10/172.16/192.168`, IPv6 ULA/`::1`); validate the **resolved IP after DNS** (DNS-rebinding); disable or constrain redirects; never echo raw upstream responses.
- **Auditor checks —** `[J]` any new code fetching a URL derived from user input has allowlist + private-range block + redirect control. `[D]` grep for HTTP clients (`requests.get`, `fetch(`, `urllib`, `httpx`) taking a variable URL near request input. `[J]` the post-resolution IP is validated (rebinding-safe), not just the string.

## Safe deserialization & dynamic execution

- **Auditor checks —** `[D]` grep for `pickle.load`, `yaml.load(` without `SafeLoader`, `eval(`, `exec(`, `BinaryFormatter`, `unserialize(`, `node-serialize` on externally-sourced data. `[J]` the data's origin is trusted/signed, or a safe loader + schema is in place.

## Dependency & supply-chain hygiene

- **Auditor checks —** `[D]` lockfile present and updated with the change; dependency-audit gate green (no unaddressed critical/high). `[D]` CI runs an SCA scan. `[J]` each newly-added dependency justified (real need, maintained, reasonable footprint, acceptable license). `[J]` pins exact, not floating `latest`.

## Build & release pipeline authorization (who may publish, and with what token)

- **Good looks like —** Workflow-level permissions **read-only by default**, the write/publish grant scoped to the single publishing job. Releasability is checked, not assumed: the published ref is an **ancestor of trunk** and **the tag matches the manifest version**. Publishing runs the **one tested build path**, never a re-implementation in YAML.
- **Auditor checks —** `[J]` No job holds more authorization than its work needs — in particular, the job running tests or installing dependencies must not hold the publish credential. `[D]` Grep for workflow-level write `permissions:` and job-level overrides. `[J]` A check that the ref being published actually landed on the trunk — a *reverse* guard ("trunk ⊆ HEAD") does **not** establish it. `[D]` The publish job `needs:` the gate job. `[J]` The workflow does not re-implement build/publish logic the repo already has tested code for. `[J]` Floating `@vN` / `install -g` dependencies inside the credentialed job are named as an accepted risk, not silently assumed pinned.
- **Incident —** 0041 S2 (2026-08-12): the **spec itself** prescribed `permissions: contents: write` at *workflow* level and the implementation matched it faithfully — arming the gates job (full suite + an unpinned global npm install) with a write-capable token; the security lens refuted the **spec**, not the diff. Two more findings sat in the same hole: the base-ancestry guard was *reverse* inclusion, so a never-merged descendant could be tagged and published (fixed with `git merge-base --is-ancestor "$GITHUB_SHA" refs/remotes/origin/main`), and a floating `npm install -g` ran inside the credentialed publish job, documented nowhere. The verdict's own words: *"dimension the spec missed: tag-commit authorization — no gate covered it."*

## Secure defaults & misconfiguration

- **Auditor checks —** `[D]` grep for `DEBUG = True`, `app.run(debug=True)`, stack-trace-to-client handlers, disabled CSRF (`CSRF_ENABLED=False` or equivalent), `chmod 777`, container `USER root`. `[J]` errors generic to the client, detailed server-side. `[J]` admin endpoints protected and unused features off. `[J]` TLS enforced end-to-end (disabled-TLS-verification grep — `verify=False`/`rejectUnauthorized:false` — see *Cryptography correctness*).

## Cryptography correctness

- **Good looks like —** Authenticated symmetric ciphers (AES-GCM / ChaCha20-Poly1305), TLS 1.2+, SHA-256+, a password KDF for passwords — via standard libraries, never home-grown. CSPRNG only (`secrets`, `crypto.randomBytes`, `SecureRandom`). Keys managed and purpose-separated; constant-time comparison for secrets/MACs.
- **Auditor checks —** `[D]` grep for `MD5`/`SHA1`/`DES`/`RC4`/`ECB`, `Math.random()` for security tokens, `verify=False`/`rejectUnauthorized:false`/disabled cert checks, hardcoded keys/IVs. `[J]` authenticated cipher, standard construction (right mode, fresh IV, CSPRNG). `[J]` keys managed and comparisons constant-time.

## PII minimization & data classification

- **Auditor checks —** `[J]` each new personal-data field collected/stored/transmitted is actually needed for the feature. `[J]` sensitive data minimized, masked where displayed/exported, not duplicated into logs/caches/analytics. `[J]` the most-sensitive data avoided unless essential, and specially handled.

## Encryption in transit & at rest

- **Auditor checks —** `[D]` grep for `http://` to sensitive endpoints, disabled TLS verification, sensitive columns/files written unencrypted where the platform expects otherwise. `[J]` at-rest encryption enabled for the new data store/field, backups covered. `[J]` keys managed/rotated (not embedded), most-regulated data handled per its standard.

## Retention, deletion & data-subject rights

- **Auditor checks —** `[J]` new persisted data has a retention/deletion story, not written somewhere it can never be removed. `[J]` an erasure request reaches this data everywhere it lands (replicas, backups, logs, indexes, third parties). `[J]` a hard-delete path exists, not only soft-delete, for regulated data.

## Consent, lawful basis & purpose limitation

- **Auditor checks —** `[J]` new processing/sharing has a lawful basis, and where consent applies it is opt-in, granular, recorded, revocable. `[J]` data used only for its original purpose (no scope creep into new analytics/ML/marketing). `[J]` trackers/third-party shares respect consent state.

## Regulatory compliance mapping (GDPR · FERPA · HIPAA · PCI DSS)

- **Auditor checks —** `[J]` which regimes this data/audience triggers (student → FERPA, health → HIPAA, EU resident → GDPR, card data → PCI), and that regime's controls are present — **met rather than assumed**, with data-residency and cross-border-transfer rules respected. `[J]` processor/BAA/data-transfer obligations covered for any third party touched. `[J]` PCI-prohibited data (full track, CVV) never stored.

## Audit trails & accountability

- **Good looks like —** The security-significant event set: authN success/failure · authZ denials · privilege changes · access to regulated records · admin actions · config/security changes · data exports and deletions — each with *who, what, when, from where*, a correlation ID, and tamper-resistance. **Audit logs themselves carry no secrets, tokens, or raw PII.**
- **Auditor checks —** `[J]` the security-significant events for this change are logged with actor/action/timestamp/source and a correlation ID. `[D]` grep the audit log lines for passwords/tokens/secrets/raw PII (overlaps *Sensitive-data hygiene*). `[J]` audit logs tamper-resistant and retained per the applicable regime.

## Sensitive-data hygiene — never log or commit real user data

- **Auditor checks —** `[D]` grep added log/print/tracker calls for whole-request/whole-object dumps, password/token/PII fields, `Authorization`/`Cookie` headers; scan committed fixtures/seeds for realistic PII or live credentials. `[D]` secret-scanner over the diff (shared with *Secrets management*). `[J]` no new log statement risks emitting sensitive data under real inputs. `[J]` test/seed data synthetic.

> Authoring rules `_TEMPLATE.md` · governance `README.md`
