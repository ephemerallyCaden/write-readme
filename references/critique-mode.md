# Critique Mode

Audit an existing README against the rules generate mode follows, report ranked findings with ready-to-apply fixes, then apply only the fixes the user picks.

Section names in this file ("Phase 1: ANALYZE", "Run-first rule", "Enhance Mode", and so on) refer to SKILL.md. Read the current text of each section when you use it; do not work from memory.

## Invocation

- `/readme critique [path]`: critique `path`. A directory means `<dir>/README.md`. No path means `./README.md`.
- Natural triggers: "critique my readme", "review my readme", "audit my readme", "improve my readme", "what's wrong with my readme".
- `--type <slug>` overrides the detected type. `minimal` / `detailed` override the inferred verbosity.

Resolve the target before anything else:
1. If the file does not exist, try a case-insensitive match (`readme.md`, `Readme.md`) in the same directory.
2. Still missing: reply "No README found at `<path>`. Want me to generate one?" and stop. On yes, run generate mode from Phase 1.
3. Not Markdown (`.rst`, `.txt`, `.adoc`): reply that critique supports Markdown only, and stop.

Project root is the README's directory. Run Phase 1 against it, so a package README in a monorepo is judged against its own package manifest.

## Hard rules

- Nothing is written until the user picks fixes and approves the write. Never create files in the project during critique; the working copy lives at `/tmp/write-readme-critique/README.md`.
- Assessment A (judgment) never sees script output. Script results are evidence for the synthesis, not a starting point for the review.
- Every finding carries a concrete fix: the exact old text and the exact new text, or an exact insert/delete/move. "Consider improving X" is not a fix.
- A fix may only state facts found in the codebase. If the right text needs a fact the codebase lacks (expected output, a URL, a benchmark), the fix inserts a `<!-- TODO: ... -->` comment naming the missing fact. Never invent output, numbers, or links.
- Fix text must itself pass the Anti-AI Writing Rules.
- Human-authored content is edited surgically, never rewritten wholesale (see Step 3).
- The report ends with exactly one question. Nothing follows it.

## Step 1: Load context

1. Read the README with line numbers.
2. Run every step of Phase 1: ANALYZE against the project root. In 1f, classify each H2 as auto-generatable, human-authored, or mixed using Enhance Mode Step 2. Keep the table: heading, line range, class.
3. Type: `--type` if given, else the Phase 1b result. Map it to a slug with the canonical type slugs table.
4. Verbosity: the user's flag if given; else `minimal` when Phase 1g flags Early-stage or the README is under 80 lines with no Features section; else `standard`.
5. Read `references/anti-ai-rules.md` and the type's entry in `references/category-templates.md` (both relative to this skill's base directory).

## Step 2: Assess

### Orchestration

- **Agent tool available:** spawn Assessment A as one sub-agent. Pass it the README path, project root, type, verbosity, the H2 classification table, a short Phase 1 summary (name, manifests, scripts, entry points, license file, git remote, env vars), and the paths to SKILL.md and this file. Tell it not to run `check-anti-ai.py` or `validate-readme.py`, and to return findings as Step 4 finding blocks (severity per the Step 3 table), plus its Unverified list. Run Assessment B in this context while A works. Never pass B's output to A.
- **No Agent tool:** run A in this context first. Write A's full findings list down before running any script, and do not revise it after reading script output; disagreements go in the synthesis.
- Record which path ran. It goes in the report header.

### Assessment A: judgment review

Check every item. Verify claims against the codebase with Read, Glob, and Grep; never assume a claim is true. Anything you cannot verify goes in an Unverified list, not in the findings.

**Correctness** (claims against reality)
- Title matches Phase 1h name resolution.
- Install and run commands use the manifest's package name; every `npm run X` / `make X` / `just X` target exists; entry points exist. Apply the build-command table in Phase 4: VERIFY.
- Clone URLs and repo links match `git remote get-url origin`.
- Every relative link and image path exists (Glob).
- Every in-page anchor `](#slug)` matches a heading slug (GitHub style: lowercase, spaces to hyphens, punctuation stripped, duplicate headings get `-1`, `-2`).
- Code examples: every imported or called name exists in the source (Grep), per Code Example Generation step 4.
- License text and license badge match the LICENSE file. "All rights reserved" next to an open-source LICENSE is a mismatch.
- Runtime and version claims match the manifest (`engines`, `requires-python`, `rust-version`, SDK constraints).
- Env vars and config keys the README names exist in code.
- A feature bullet is a P0 false claim only after a Grep for its key terms finds nothing.

**Getting started**
- The Run-first rule in Phase 3b holds, including its stated exceptions.
- Time to first command: note the line of the first runnable command (fenced shell block, download table, or store badge). Past line 80 (line 50 for minimal) is P1.
- Prerequisites name the runtime versions the manifest requires.
- An expected-result line follows the run command: the URL and port for servers (from config or defaults), `--help` / `--version` for CLIs, the generated files for generators. Missing is P2; the fix uses only codebase facts.
- Post-install steps the code requires (env vars read at startup, migrations, a config file that must exist) are documented. Missing is P1.
- The primary install path is not collapsed inside `<details>`.
- If install sits below an H2 about security, compatibility, requirements, or a threat model, do not propose moving it above that section. Report it as P2 with the reason, and offer the move only as an option the user picks by id.

**Structure**
- Every MUST section for the type (Type-to-Template Mapping, plus the matrix in `category-templates.md`) is present. Missing MUST is P1. Respect Special Detection: no Contributing for solo or academic projects.
- Missing SHOULD sections are P2, and only when the codebase supplies their content. Never propose padding to reach a Length Target; over-length fixes name the sections to cut or collapse.
- One H1, no skipped heading levels, no duplicate or near-duplicate H2s.
- TOC and navigation rule from Phase 3e: a TOC exists above 150 lines (Educational / Awesome always has a TOC or anchor nav block), and every TOC entry matches a heading.
- Every fenced code block names a language.

**Visuals**
- The type's screenshot positions from Phase 3d: a MUST position with no image is P1.
- Run the Phase 1j image search and classification. Screenshots in the repo that the README never uses are P2, and the fix gives the path and alt text.
- Every image has descriptive alt text, read from the image itself.
- No positional references ("the screenshot below", "animation above").
- No `style=` attributes in HTML (GitHub strips them).
- No feature text that exists only inside an image.

**Writing**
- Anti-AI Writing Rules: banned words, the 12 structural rules, the P0 and P1 checks, the portability test, voice register.
- Honest limits: when the code gates OS, runtime, or input type (`sys.platform`, `#[cfg(target_os)]`, `engines`, the CI OS matrix, `NotImplementedError` on public paths) and the README is silent, propose a one-line limitation built from that evidence. P2.
- In human-authored sections, flag only P0 checks, banned words, and factual errors. Leave tone, humour, and sentence style alone.

**Maintenance / drift**
- At most 6 header badges. Dead badge hosts (`travis-ci.org`, `nodei.co`, `ci.appveyor.com`, `david-dm.org`) are P0. Static badges that imitate live status ("build passing", "maintained: yes") are P1. A CI badge must name a workflow file that exists.
- Hardcoded versions (badges, prose) that differ from the manifest are P0; ones that match today but duplicate the manifest are P2.
- Placeholder text outside `<!-- -->` comments (`TODO`, `TBD`, `coming soon`, `link needed`, lorem ipsum) is P1.
- Community files found in Phase 1c (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG) that the README never links are P2.

### Assessment B: scripts

Run both against the README in place (both are read-only), with `<skill-dir>` being this skill's base directory:

```bash
python3 <skill-dir>/scripts/check-anti-ai.py --file <readme> --severity P2
python3 <skill-dir>/scripts/validate-readme.py <readme> --type <slug> --verbosity <level> --dir <project-root>
```

Keep the raw output and exit codes. These are the "before" results. If `python3` is unavailable, record "Scripts not run: python3 unavailable" and continue with A alone.

## Step 3: Synthesize

1. Turn each script finding into a finding, or merge it into the matching A finding and add "(also flagged by `<script>`)" to its evidence.
2. Dismiss script false positives (for example a bold-label hit on a file list) in the Not actioned list, with the reason.
3. Assign severity:

| Severity | Meaning | Examples |
|---|---|---|
| P0 | Broken or misleading | Wrong or failing command, dead link or anchor, false claim, license mismatch, dead badge host |
| P1 | Blocks the reader or breaks a rule | Install buried, missing MUST section, post-install step missing, placeholder text, AI-isms |
| P2 | Polish | Missing expected-result line, unused screenshot, duplicated version string, style-level writing fixes |

4. Write each fix against the H2 classification:
   - Auto-generatable sections (badge rows, TOC, license one-liner): the fix may replace the whole section.
   - Human-authored and mixed sections: replace the smallest span that fixes the problem, usually one phrase or one line. Keep the author's wording everywhere else.
   - A fix that deletes or moves human-authored content gets the tag `[human]` and quotes everything it removes.
5. Order findings by group (Correctness, Getting started, Structure, Visuals, Writing, Maintenance), then severity, then line.
6. Score each group: **fail** if it has any P0, **warn** if it has any P1, **pass** otherwise (P2 only, or no findings).

## Step 4: Report

Write the whole report, then ask the question. Use this layout:

```
README critique: <path> (<type>, <verbosity>, <N> lines)
Method: dual-agent (A: sub-agent, B: scripts in main context) | single-context (no Agent tool)
Scores: Correctness fail · Getting started warn · Structure pass · Visuals pass · Writing warn · Maintenance pass
Totals: 1 P0, 3 P1, 4 P2

Keep: <1-3 specific things the README does well, so the fixes don't erode them>
```

Then one block per finding. IDs use the group letter (C, G, S, V, W, M) and a counter, and stay fixed for the rest of the session:

````
C1 · P0 · Correctness · L42 (Getting Started)
Problem: the run step calls `npm run dev`, which does not exist.
Evidence: package.json "scripts" defines only `start` and `build`.
Fix (replace L42):
```diff
- npm run dev
+ npm start
```
````

Fix kinds: `replace Lx-Ly`, `insert after Lx`, `delete Lx-Ly [human]`, `move Lx-Ly to after Lz [human]`. Show every fix as a diff block like the one above.

After the findings, add three short lists:
- Not actioned: dismissed script findings and intentional skips (for example "no Contributing: solo project"), each with a one-line reason.
- Unverified: claims you could not check, with what would confirm them.
- Scripts (before): the check-anti-ai counts per severity and the validate-readme issue count.

Last, ask one question. Use AskUserQuestion when available:

> Which fixes should I apply?
> - All P0 + P1 (Recommended): <ids>, excluding `[human]` findings
> - All findings, including `[human]`
> - Pick by id (e.g. "C1 G2 W3")
> - None: report only

With no P0 or P1 findings, make "All findings" the recommended option. With no findings at all, skip the question and end with "No findings. Nothing to apply."

## Step 5: Apply

- None / report only: stop. Write nothing, and create no working copy.
- Otherwise copy the README to `/tmp/write-readme-critique/README.md` and apply the chosen fixes there, from the highest line number to the lowest so earlier line numbers stay valid. Apply each fix as an exact replacement of its quoted old text. If the old text no longer matches (two fixes overlap), skip that fix and report it as skipped.
- Change nothing outside the chosen fixes, with one exception: when a fix changes headings, regenerate an existing TOC and report it as "follow-on: TOC updated".
- Re-run both Assessment B commands on the working copy. Keep `--dir <project-root>` so relative links resolve against the project, not `/tmp`.
- If a fix introduced a new P0 or P1 script finding, correct the fix's own text and re-run. Never touch other text to clear it.

Then show, in this order:
1. Applied and skipped ids, with the reason for each skip.
2. `diff -u <readme> /tmp/write-readme-critique/README.md`, the full unified diff.
3. A before/after table: check-anti-ai P0/P1/P2 counts and the validate-readme issue count.
4. The question "Write these changes to `<path>`?". Skip it if the user already approved writing in their selection (for example "apply all and write it").

On approval, write the file and confirm: "`<path>` updated. <K> fixes applied." If git is initialized, note that `git diff` shows the change and `git checkout -- <path>` reverts it. If the user asks to adjust a fix, change only that fix, re-apply, and show the new diff and results.
