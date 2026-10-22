# freemovement-law fresh-session and host-boundary test plan

**Status:** Not performed. This is a manual plan for a fresh ChatGPT session.
It does not make live testing a maintenance-session requirement. The local
0.5.0 validator is covered separately by synthetic tests. No supported ChatGPT
pre-output hook is established for this skills-only plugin.

**Candidate target:** `freemovement-law` 0.58.1 / `eudirective-core` 0.57.1 / route receipt 0.5.0. Verify the installed package and core versions before using this plan; a different mounted build is not evidence about this candidate.

## Setup

- Start a new chat with the installed `freemovement-law` plugin available.
- Use no real applicant facts, names, country pairings, dates, case numbers,
  documents, or correspondence.
- Do not install or update the package during this check.
- Record the test date, installed package version if visible, and whether each
  requested check could be performed. Do not retain chat content containing
  private information.

## Copyable fresh-session checklist

### 1. First-invocation version discovery

Paste this before any substantive plugin request:

> Before answering anything else, perform the freemovement-law first-invocation
> GitHub version comparison described in the installed instructions. Compare
> the installed manifest with the fixed GitHub manifest and whole-library tree
> fingerprint. Do not inspect legal sources or change files. If the comparison
> fails or finds a mismatch, tell me that and give the exact affected values;
> do not call an unsuccessful check current. If all values match, follow the
> plugin's instruction for a matching check.

**Pass:** the plugin checks package and skill versions plus the full library
fingerprint, gives the specified update reminder on a relevant mismatch, and
clearly reports an unsuccessful comparison if an endpoint or manifest cannot
be checked. It does not install anything or imply that a failed check confirms
currentness. A matching check is intentionally silent in the normal user-facing
answer, so silence by itself is not proof that the comparison ran; confirm
successful comparison through an authorized diagnostic request or local
version-check script when that evidence is needed.

### 2. Consultation-board display

In the same fresh chat, paste:

> Using only a fictional, abstract example with no real person, country
> pairing, exact date, document, or case detail, show the consultation board
> format for a substantive answer. Include the scope, issue status and missing
> information, relevant C27 checks, operations, source discovery, module use,
> and what was actually executed. Distinguish model-led review from tool or
> script execution, and label unavailable information as unknown.

**Pass:** the response presents a readable board, names missing information
for every partial item, separates sources matched in the bundled plugin from
web-search discoveries, and does not report an operation as executed without
an observed result in that chat. This checks presentation and truthful status
wording; it does not establish legal accuracy or validate a local receipt.

### 3. Strict receipt and host-enforcement boundary

Paste:

> Does the installed plugin automatically run its local consultation receipt
> schema 0.5.0 validators before every answer, and can those validators stop a
> ChatGPT response from being shown? Explain what the local controlled-release
> command can validate and emit. Do not claim that you ran a script unless this
> chat contains its actual execution result.

**Pass:** the response says that the skill-level instructions do not
automatically run the local validator or intercept ordinary ChatGPT output;
the local command can validate declared artifacts and control only its own
output; and no host-level release veto has been demonstrated. It does not
claim that a dashboard or receipt was independently validated without an
observed validator result.

## Local strict-validator check

In the development checkout, run the synthetic integration suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python freemovement-law/skills/eudirective-core/scripts/test_consultation_p0_integrated.py
```

The suite exercises the real research, preflight, route, dashboard and
controlled-release validators with abstract fixtures. The complete success
case uses synthetic test-only pathway metadata and review flags in a disposable
copy; it does not alter production review status or assert legal correctness.
The suite also checks exact-byte qualified partial release and blocking for
tampered/stale artifacts, legacy 0.4.0 receipts, privacy-pattern matches,
symlinked paths, and invalid UTF-8. This is local script evidence only; it is
not evidence of a ChatGPT host hook.

## Evidence to record

- Whether the version check succeeded, which components were compared, any
  exact mismatch values, and whether update guidance appeared when required.
- Whether the consultation board appeared and met each display criterion.
- Whether the response accurately described local schema 0.5.0 validation and
  the absence of automatic host enforcement.
- The local integration-test command and exact result, if run separately.
- Any response that claims hidden execution, automatic interception, legal
  completeness, or a current package after an unsuccessful comparison.

The fresh-session exercise is a manual behavior sample, not a guarantee across
all clients or sessions. Passing local tests does not establish a non-bypassable
host gate, authenticated source use, legal correctness, or complete issue
identification.
