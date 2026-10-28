---
name: readme
description: Generate polished, project-type-aware READMEs from codebase analysis. Use when asked to "generate a readme", "write a readme", "create a readme", or "/readme". Supports minimal/standard/detailed verbosity, 20 project types, anti-AI-slop writing rules, and optional screenshot capture. Also critiques existing READMEs ("/readme critique", "review/audit/improve my readme") with ranked findings and fixes it applies on request.
---

# write-readme

Generate a README.md by analyzing the current codebase, asking 0-3 questions, and producing a project-type-aware document that reads like a human wrote it.

`<skill-dir>` in the commands below is this skill's base directory; `references/`, `scripts/`, and `skills/` paths are relative to it.

Output: `README.md` at the project root. If one exists, ask whether to enhance or replace. Critique mode (below) edits an existing README instead of generating one.

## Invocation

Trigger phrases: "generate a readme", "write a readme", "create a readme", "/readme", "make a readme", "critique my readme", "review my readme", "audit my readme", "improve my readme"

Options (natural language or flags):
- `/readme` -- standard verbosity, auto-detected type
- `/readme minimal` or "write a short readme" -- essentials only
- `/readme detailed` or "write a polished readme" -- every section the type supports
- `/readme --type cli` -- override auto-detected project type
- `/readme architecture` or "write an ARCHITECTURE.md" -- write only the ARCHITECTURE.md companion file. Follow `references/architecture-mode.md`.
- `/readme critique [path]` or "critique/review/audit/improve my readme" -- audit an existing README (default `./README.md`) against these same rules and scripts. Reports P0-P2 findings with exact fixes, then applies the ones you pick. Follow `references/critique-mode.md`. If no README exists, offer generate mode.
- Generate mode stays the default. "Enhance" rewrites auto sections in bulk; "critique" only proposes edits and you choose which to apply.

## Phase 1: ANALYZE

Run all steps silently. No user interaction.

### 1a. Detect manifests

```
Glob: package.json, pyproject.toml, setup.py, setup.cfg, Cargo.toml, go.mod, Gemfile, *.gemspec, pom.xml, build.gradle, build.gradle.kts, CMakeLists.txt, Makefile, mix.exs, pubspec.yaml, composer.json, Package.swift, *.cabal, dune-project, platformio.ini
```

Read each found manifest. Extract: name, version, description, license, dependencies, scripts, entry points, engine/runtime requirements. `python3 <skill-dir>/scripts/extract-metadata.py --dir <project-root>` prints those fields as JSON for the first manifest it recognises; use it as a starting point, and still read every manifest yourself, since it parses only one.

### 1b. Detect project type

Get a first guess with `bash <skill-dir>/scripts/detect-project-type.sh --dir <project-root>`, which prints a canonical type slug. It matches file signals only, so confirm it by reading the code against the table below; where they disagree, the table and your reading win.

Use the unified taxonomy below. First match wins (lowest priority number). Personal config and Hardware come first because their file signals are unambiguous, while the helper scripts those repos carry (an `argparse` installer, a matplotlib plot of sensor logs) would otherwise match CLI or Visual Output. A hardware repo that also holds a companion app is ambiguous: Phase 2a question 3.

| Pri | Type | Detection Signals |
|-----|------|-------------------|
| 1 | Personal config / dotfiles | Repo name contains `dotfiles` and no package manifest; dotfile-manager files (`.chezmoiroot`, `dot_*` entries, dotbot `install.conf.yaml`, `.stow-local-ignore`); Home Assistant `configuration.yaml` with `automations.yaml` or a `homeassistant:` key; or 3+ personal rc files at the root (`.zshrc`, `.bashrc`, `.vimrc`, `.tmux.conf`, `.gitconfig`, dotted or not) and no package manifest |
| 2 | Hardware / Embedded | Within 2 levels of the root: `platformio.ini`, `*.ino` outside `examples/`, KiCad files (`*.kicad_pro`, `*.kicad_pcb`, `*.kicad_sch`), `BOM.csv` |
| 3 | Game / Interactive | `project.godot`, pygame/arcade/raylib/bevy/love2d imports, Phaser/PixiJS/Babylon imports, game asset dirs (sprites/, levels/, textures/) |
| 4 | Visual Output / CV | cv2/mediapipe/dlib imports + VideoCapture/imwrite/landmark/bounding.box. Also: matplotlib/plotly/d3/chart.js/bokeh/seaborn with data pipeline (Data Viz subtype) |
| 5 | Generative AI | diffusers/StableDiffusion/comfyui imports. Uses Visual Output template. |
| 6 | Bot | discord.py/discord.js/telegram/slack-bolt/botfather imports, bot token patterns |
| 7 | Browser Extension | manifest.json with permissions/content_scripts/background |
| 8 | Mobile App | pubspec.yaml (Flutter), react-native dep, android/+ios/ dirs, .xcodeproj |
| 9 | Desktop Application | Electron/Tauri/Qt/GTK/SwiftUI/WPF imports, .desktop files |
| 10 | TUI Application | textual/blessed/tview/bubbletea/cursive/crossterm/ncurses imports. Uses CLI Tool template. |
| 11 | Documentation Site / SSG | docusaurus.config/vitepress/mkdocs.yml/astro.config/sphinx conf.py |
| 12 | Web Application | Server framework (express/fastapi/flask/django/next/nuxt/svelte/rails) + dev/start/serve script + frontend files (pages/, components/, src/pages/, src/components/, templates/, public/, or index.html) |
| 13 | API / Backend Service | Server framework + NO frontend files. Everything that missed priority 12 for lack of frontend files lands here. |
| 14 | CLI Tool | bin in manifest, argparse/click/typer/clap/cobra imports, console_scripts entry point |
| 15 | Framework | Plugin system, middleware patterns, scaffolding CLI, create-* package |
| 16 | ML/AI Model | torch/tensorflow/jax imports + model dirs + training scripts (WITHOUT visual output signals) |
| 17 | DevOps / Infrastructure | Kubernetes manifests, Terraform files, Ansible playbooks, Helm charts |
| 18 | Educational / Awesome | awesome- prefix, curated link lists, no source code |
| 19 | Library / Package | exports/lib field, public API, no bin, no server framework |
| 20 | Other / Unknown | Nothing above matched -- infer from codebase |

### 1c. Scan community and config files

```
Glob: LICENSE*, CONTRIBUTING*, CODE_OF_CONDUCT*, SECURITY*, CHANGELOG*, CHANGES*, HISTORY*, .github/FUNDING.yml, .github/workflows/*, GOVERNANCE*, ROADMAP*, ARCHITECTURE*, docs/
Glob: AGENTS.md, llms.txt, CLAUDE.md
Glob: Dockerfile, docker-compose*, .dockerignore
```

Grep for env vars:
```
Grep pattern: (os\.environ|process\.env|env::var|os\.Getenv|\.env\.example)
```

Grep for config patterns:
```
Grep pattern: (argparse|click\.command|typer\.Typer|clap::Parser|cobra\.Command)
```

If CLI tool detected, run its `--help` with a 5-second limit. `timeout` is not on macOS by default, so use Python, which the checker scripts already need:
```bash
python3 - <entry_point> --help <<'EOF'
import subprocess, sys
try:
    r = subprocess.run(sys.argv[1:], capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL)
    print(r.stdout + r.stderr)
except (OSError, subprocess.TimeoutExpired) as e:
    print(f"--help failed: {e}")
EOF
```
Only run `--help` (or `--version`) this way, never a command that does work.

### 1d. Extract public API

```
Grep pattern: (^export |^pub fn |^def [a-z_]+\(|^class [A-Z])
```

### 1e. Git and structure

```bash
git remote get-url origin 2>/dev/null
tree -L 2 --dirsfirst -I 'node_modules|.git|__pycache__|venv|.venv|target|dist|build' 2>/dev/null || find . -maxdepth 2 -not -path '*/.git/*' -not -path '*/node_modules/*' | head -60
```

### 1f. Read existing README

If README.md exists, read it. Classify each H2 section as auto-generatable, human-authored, or mixed (see Enhance Mode below).

### 1g. Special detection

These are the only detection signals; Special Detection below says what to do when each one fires.

**Solo project:** one contributor (`git shortlog -sn HEAD`), fewer than 5 stars when the count is known, and no CONTRIBUTING.md.
**Academic:** .university or .edu in manifest groupId/org, assessment brief files (instructions.md, brief.md, assignment.md), course module codes in repo name. Research write-up subtype: a paper or report in the repo (`paper/*.tex`, `report.pdf`, `thesis.pdf`), or an Academic project whose main output is notebooks plus a `results/` or `figures/` directory.
**GitHub Pages:** CNAME file at root, .nojekyll, raw index.html with no manifest, gh-pages branch.
**Early-stage:** No manifest OR manifest has <3 fields OR <5 source files. Personal config and Hardware repos rarely have a manifest, so for them only the file count applies (config files, sketches, schematics, and BOMs count).
**Monorepo:** workspaces in package.json, [workspace] in Cargo.toml, lerna.json, pnpm-workspace.yaml, packages/ or apps/ directory.
**Sibling packages:** the manifest declares both a library and a binary (Cargo `[lib]` + `[[bin]]`, package.json `exports`/`main` + `bin`), or the monorepo, manifest, or docs point to a `-cli` / `-core` sibling of this package.
**Agent resources:** AGENTS.md, llms.txt, or CLAUDE.md at the root, or a package or entry point that starts an MCP server.
**Component count:** workspace members (Cargo, npm, or pnpm workspaces, `go.work`), entries under `apps/` and `packages/`, or top-level directories with their own manifest or package marker (`__init__.py`, `mod.rs`, `index.ts`). 3+ shows the ARCHITECTURE.md line in Phase 2b.

### 1h. Name resolution

Priority chain for display name:
1. App display name (AndroidManifest.xml android:label, Info.plist CFBundleDisplayName, MaterialApp title)
2. Manifest human-readable name (skip if it looks like a code identifier: underscores, no spaces, all lowercase)
3. Repo name from git remote
4. Directory name

Never use an internal package identifier (underscored, no spaces, all lowercase) as the title.

If two human-readable candidates disagree (app label "Ganba" vs manifest name "Climb Log"), that is Phase 2a question 5. Otherwise use the highest-priority candidate.

### 1i. Supplementary docs

```bash
find . -maxdepth 3 -name "*.md" -not -name "README*" -not -name "LICENSE*" -not -name "CONTRIBUTING*" -not -name "CODE_OF_CONDUCT*" -not -name "SECURITY*" -not -name "CHANGELOG*" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null
```

Read the first 5 lines of each to understand its purpose. Link significant docs in the generated README.

### 1j. Find and classify images

Runs here, before Phase 2, so the screenshot question is asked once and only when it is needed.

Step 1 -- Search the ENTIRE project for images. Do not hardcode directories:
```bash
find . -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.svg" -o -name "*.webp" \) \
  -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/build/*" \
  -not -path "*/.dart_tool/*" -not -path "*/dist/*" -not -path "*/target/*" \
  -not -path "*/__pycache__/*" -not -path "*/.venv/*"
```
This catches images anywhere: test/goldens/ (Flutter golden tests), docs/design/, assets/, or wherever else they exist. Also check existing README for external image references.

Step 2 -- Shortlist before reading any image:
- Skip paths under `sprites/`, `textures/`, `icons/`, or `fonts/`, and names matching `favicon*`, `*icon*`, `*_diff*`, or `*-diff*`.
- Skip raster images under 5 KB or under 200 px on either side (`file <image>` prints PNG, GIF, and JPEG dimensions). SVGs are judged by path and name only.
- Rank what is left: images under `docs/`, `assets/`, `screenshots/`, or a golden-test directory (`goldens/`) first, then the rest, larger files first within each group. Read at most the top 20.

Step 3 -- Look at each shortlisted image and decide if it belongs in a README. Not every image file is a screenshot. Read the image and judge:
- **App screen / UI render** (dashboard, settings, feature view) → use it
- **Diagram** (architecture, flowchart, pipeline) → use it
- **Terminal output** (CLI help, command demo) → use it
- **Logo** → use only in the title area, not as a screenshot
- **Icon / sprite / texture / favicon** → skip, internal asset
- **Diff image / coverage badge / test failure** → skip, test artifact
- **Design mockup** → use if it represents the actual app, skip if it's a wireframe draft

Only reference images that would help a reader understand what the project does or looks like. When in doubt, skip it. Record which screenshot positions the usable images cover: the `<!-- screenshot:... -->` entries and their MUST/SHOULD/COULD priority in the detected type's entry in `references/category-templates.md` (read it now; Phase 3a uses it again).

### 1k. Limits and outbound data

Evidence for the Limitations and Privacy sections (Phase 3b). Ignore hits under tests/, examples/, docs/, and vendored or generated directories, and in dev-only dependencies.

```
Grep pattern (OS gates): (sys\.platform|platform\.system\(\)|os\.name ==|#\[cfg\((not\()?(target_os|windows|unix)|runtime\.GOOS|process\.platform)
Grep pattern (unfinished paths): (raise NotImplementedError|unimplemented!\(|todo!\()
Grep pattern (telemetry SDKs): (posthog|@segment/|analytics-node|segment\.io|sentry_sdk|@sentry/|sentry-go|sentry::|mixpanel|amplitude|@datadog/browser-rum|datadog_rum|firebase/analytics|firebase_analytics|FirebaseAnalytics|gtag\(|googletagmanager|plausible|@vercel/analytics|bugsnag|rollbar)
Grep pattern (LLM providers): (OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|GOOGLE_API_KEY|MISTRAL_API_KEY|COHERE_API_KEY|GROQ_API_KEY|OPENROUTER_API_KEY|AZURE_OPENAI|api\.openai\.com|api\.anthropic\.com)
Glob: **/PrivacyInfo.xcprivacy
```

Also record: version bounds from 1a (`engines`, `requires-python`, `rust-version`, SDK constraints, the `go` directive), `os` / `cpu` fields in package.json, the CI OS matrix (`runs-on`, `matrix.os` in `.github/workflows/*`), and dependencies that exist for one platform only (`pyobjc`, `pywin32`, `[target.'cfg(windows)'.dependencies]`, `sys_platform ==` markers). A telemetry hit counts only where the SDK is initialised in this project's code. Skip the data-flow evidence when sending data is the product (the repo is the analytics SDK or an LLM client library).

## Phase 2: ASK

### 2a. Required questions (0-3 max, priority ordered)

A required question is one with no safe default. These are the only ones, wherever they are triggered (Phase 1h, Special Detection), and all of them count toward the cap. Ask the ones that apply, in this order:
1. "Enhance existing or generate fresh?" -- only if existing README found.
2. "Describe your project in 1-2 sentences -- what does it do and who is it for?" -- SKIP if manifest description >10 words AND no existing README. If cut: infer from manifest and code.
3. "This looks like both a [type A] and [type B]. Which is its primary identity?" -- only if type detection is ambiguous. If cut: the lower priority number wins.
4. If monorepo: "Generate README for the root monorepo or a specific package?" If cut: root.
5. "Should the title be [A] or [B]?" -- only if Phase 1h found two human-readable names that disagree. If cut: the higher candidate in the Phase 1h chain.

Hard cap: 3 required questions. After 3, use the "If cut" default for the rest. The optional choices block in 2b does not count toward the cap, because every item in it has a default.

### 2b. Optional choices (single block, all skippable)

Present after required questions, as one block:

```
Before I generate, a few quick choices (press Enter to skip any):

 License:       [MIT] [Apache-2.0] [GPL-3.0] [Skip -- no license]
                Default: Skip if none exists, keep current if one exists

 Contributing:  [Include section] [Skip]
                Default: Include for multi-contributor projects, Skip for solo/academic

 Verbosity:     [Minimal] [Standard] [Detailed]
                Default: Standard (or inferred from context)

 Screenshots:   [Auto-capture] [I'll add later] [Point to files]
                Default: I'll add later (descriptive placeholders)
                Only shown if Phase 1j found no usable image for a MUST
                screenshot position and minimal wasn't already requested.
                This is the only screenshot question.

 Architecture:  [Also write ARCHITECTURE.md] [Skip]
                Default: Skip
                Only shown when detailed was requested or Phase 1g
                counted 3+ components, the project is not Early-stage,
                and neither ARCHITECTURE.md nor docs/architecture.md
                exists. Ignored if Minimal is chosen above.
```

Unanswered choices use defaults. "Go", "just do it", or Enter accepts all defaults.

The ARCHITECTURE.md offer is never asked as a separate question. If the user picks Detailed here and the line wasn't shown, note in the Phase 5 summary that ARCHITECTURE.md is available on request (unless the project is Early-stage or one already exists).

### Verbosity levels

**minimal** -- Ship fast. Personal projects, prototypes, hackathons.
- Includes: Title, description (1-2 sentences), install, basic usage (one example), license, plus a one-line Privacy note when Phase 1k found a data flow (Phase 3b)
- Skips: badges, features, TOC, contributing, community, sponsors, architecture
- No screenshot placeholders
- Target: 30-80 lines, whatever the type (overrides the Length Targets table)
- Triggered by: "minimal", "short", "quick", "simple", "brief", or <5 source files

**standard** (default) -- Balanced README. Most projects.
- Includes: all MUST sections + SHOULD sections where data is available
- Skips: COULD sections unless data already exists
- Screenshots and placeholders follow Phase 3d
- Target: ideal length for detected type (see Length Targets)
- Triggered by: default when no preference stated

**detailed** -- Polished landing page. Open source launches, portfolio pieces.
- Includes: all MUST + SHOULD + COULD sections
- Adds: performance notes backed by benchmarks in the repo, detailed config, env vars table, directory tree, a Comparison section only when a source exists (Phase 3b), and the ARCHITECTURE.md offer (Phase 2b)
- Target: upper half of the type's range, up to the stretched detailed bound in Length Targets. Long reference material (full flag tables, header lists) may go in `## Appendix: ...` sections after License.
- Triggered by: "detailed", "comprehensive", "full", "polished", "landing page", "launch"

## Phase 3: GENERATE

### 3a. Select template

Read the detected type's entry in `references/category-templates.md`: its section ordering and its priority table. That table defines MUST, SHOULD, and COULD for the type, and every use of those words in this file means the table's value, except for the evidence-only sections in Phase 3b (Limitations, Privacy, Comparison), which state their own (see Type-to-Template Mapping below).

### 3b. Generate section by section

Follow the template ordering, with one override:

**Run-first rule.** The first H2 is how to get the project running (heading: "Getting Started", "Quick Start", "Install", "Download", or "Local Development" for static sites). What counts as running depends on the type:
- Install + the command that runs, plays, or imports it: CLI, TUI, Library, ML, CV, Gen AI, Bot, DevOps, Game without release binaries, Other.
- A scaffold or template command that installs and runs in one step (`npm create ...`, `dotnet new ...`, `go run ...@latest`): Framework, Docs Site, project generators. A Framework with no scaffold command uses install + import instead.
- A per-OS download table or store badges: Desktop, Mobile, Browser Extension, and Game when release binaries exist. Build-from-source steps go later.
- A hosted URL or one-click deploy button, followed by self-host commands: Web App, API, and Docs Site when a hosted version exists.
- No release, store, or hosted evidence (Desktop, Mobile, Browser Extension, Web App, API): build-from-source or self-host commands. Never invent a store link, download, or URL.
- Build and flash the firmware (`pio run -t upload`, `arduino-cli upload`), with the parts list linked from the prerequisites line: Hardware. A board-only repo (no firmware) points to its fabrication outputs (gerbers, BOM, placement files) instead.

Before it, allow only: title, badges, description (≤2 sentences, plus a router line if Special Detection calls for one), hero image, nav row, the `**Contents**` TOC (Phase 3e). Features, Architecture, Model tables, Sponsors, and everything else go after it. Prerequisites go inside the run section as its first line ("Requires Flutter 3.12+."), never as their own section before or after it. Keep the first command, download table, store badge, or hosted URL within the first 80 lines (50 in minimal).

Library / Package: a code snippet of 10 lines or fewer may precede the install line inside the first H2.

Research write-up (Special Detection): a Results section (the key figure and metrics table) may also precede the run section. The run section still needs one runnable command that reproduces a result, such as the training or evaluation script, or `jupyter nbconvert --execute` on the main notebook. The 80-line limit still applies.

Exempt: Educational / Awesome lists, personal config / dotfiles repos (a browse index with nothing to install), and ARCHITECTURE.md.

**Expected result.** End the Quick Start with what the reader should see: the URL and port for servers (read from config or framework defaults), the `--help` or `--version` output for CLIs (Phase 1c already ran `--help`), the generated file or folder for generators, the serial baud rate and first log line for firmware (from `Serial.begin(...)` and the setup code), or a `// =>` result comment for libraries only when a test fixture confirms the value. Never invent output. If nothing is verifiable, end on the command.

**Install chooser.** When a CLI, Desktop app, Library, or DevOps tool ships through several channels, show one primary method expanded and marked "(Recommended)": the one the project's own docs lead with, else the ecosystem's package manager. Give every other method a one-line "Use this if ..." and put them in `<details>` when there are more than 3. Detect channels from `Formula/` or a tap reference, `snapcraft.yaml`, `*.nuspec`, `flake.nix`, `Dockerfile`, `.goreleaser.yml`, release workflow artifacts, and `pyproject.toml` extras. List only channels with evidence.

**Limitations.** Build them only from Phase 1k evidence. Version floors belong on the prerequisites line; limitations are upper bounds and exclusions, OS gates that exit or raise, `NotImplementedError` / `unimplemented!()` / `todo!()` on public paths, and one-platform-only dependencies. A CI matrix without an OS makes that OS untested, not unsupported, unless code also gates it. Each item names its evidence: "Windows is not supported (`main.py` exits when `sys.platform == "win32"`; CI runs Linux and macOS only)." One item: a "Not supported: ..." (or "Untested: ...") line in the run section, right after the prerequisites line. Two or more: a `## Limitations` section (SHOULD) after Usage and Config, before Contributing. No evidence: no section and no line, never "No known limitations". Never collapse it in `<details>`.

**Privacy.** Required when Phase 1k found an initialised telemetry, analytics, or error-reporting SDK, a `PrivacyInfo.xcprivacy`, or an outbound LLM provider key. Title it `## Privacy` (or "What is sent"), after Config and before Contributing; for Browser Extensions, fold it into Permissions/Privacy. Give one line per destination: what is sent (from the call sites: event names, captured fields, prompt contents and attached files), where (the vendor, plus the host if code configures one), and whether it is on by default. Opt-out: name only an env var, CLI flag, or config key the code reads, quoted exactly ("Set `DO_NOT_TRACK=1` to disable."). If none is found, write "No opt-out found in the code." rather than claiming none exists. For `PrivacyInfo.xcprivacy`, list its collected data types and tracking flag and link the file. In minimal, compress this to one line after the usage example.

**Comparison.** Generating one is detailed mode only, and only from the existing README, `docs/`, or text the user supplies. A human-written comparison in an existing README is preserved in every mode (Enhance Mode). Never research or invent one, and never ask a Phase 2 question for it. Name each alternative and link it, link a source for every claim (a benchmark, the alternative's docs), and include at least one dimension where this project loses or doesn't apply. Never compare against unnamed "other tools" or "traditional approaches". No source: no section.

**Architecture section.** Draw only the components and edges Phase 1 found. Minimal: none. Standard: at most one Mermaid diagram, 2-4 sentences, and a link to ARCHITECTURE.md or an existing architecture doc when there is one. Detailed: the same cap when ARCHITECTURE.md is being written; otherwise the template's full Architecture section.

**ARCHITECTURE.md.** When chosen in Phase 2b, follow `references/architecture-mode.md` after the README draft passes Phase 4. That file says where the README links it.

Before writing prose, read `references/anti-ai-rules.md`, and apply the Anti-AI Writing Rules section below while writing, not only as a post-pass.

### 3c. Generate badges

1. Parse owner/repo from `git remote get-url origin` (`github.com/{owner}/{repo}`). No git remote, or a private repo: skip all shields.io badges.
2. Detect the registry and take the package name from the manifest: package.json -> `npm` | pyproject.toml/setup.py -> `pypi` | Cargo.toml -> `crates.io` | go.mod -> `go` | Gemfile/gemspec -> `rubygems` | pubspec.yaml -> `pub.dev` | composer.json -> `packagist` | pom.xml/build.gradle -> `maven` | mix.exs -> `hex.pm` | *.cabal -> `hackage` | no match -> GitHub-only badges.
3. Generate the row (flat style, in the order License, CI, Version, Downloads):
   ```bash
   python3 <skill-dir>/scripts/generate-badges.py --owner <owner> --repo <repo> --license <SPDX id> --ci-workflow <file> --ecosystem <registry> --package <name>
   ```
   Pass a flag only with real data behind it: `--license` only with a LICENSE file, `--ci-workflow` only for a file that exists in `.github/workflows/`, and `--ecosystem` with `--package` only when the package is published (they add the Version and Downloads badges).
4. Add a Community badge by hand only when a Discord or Slack link exists. Keep 0-6 badges in total; zero is fine.

Never generate a static badge that imitates live status (`build-passing`, `maintained-yes`, `docs-available`). Static badges are only for facts that don't change with the build, such as language, framework, or platform. In detailed mode, keep at most one CI badge in the header and move per-workflow CI badges into a "Project status" table near the end.

### 3d. Visual assets

Use the images Phase 1j classified as usable. Reference them at the template's screenshot positions and read each one to write accurate alt text. For positions still uncovered:
- **MUST position**: act on the Phase 2b Screenshots answer. Auto-capture: delegate to the screenshot sub-skill at `skills/screenshot/SKILL.md` (its Path A) with the output directory `/tmp/write-readme-draft/assets/screenshots/`, and reference each returned image in the draft by its project path (`assets/screenshots/hero.png`). I'll add later (the default): insert descriptive placeholders. Point to files: use the paths the user gave.
- **SHOULD/COULD position**: insert placeholders without asking.
- **Minimal verbosity**: use found images only; no placeholders, no capture unless the user chose Auto-capture.

Nothing is written into the project before Phase 6. Captures, `.tape` files, and rendered diagrams stay under `/tmp/write-readme-draft/`, which mirrors project paths: `/tmp/write-readme-draft/assets/screenshots/hero.png` is copied to `assets/screenshots/hero.png` on approval.

Rendering hygiene:
- If the README is published to a registry (`readme = "README.md"` in pyproject.toml, setup.py reading README into `long_description`, or a package.json without `"private": true`), use absolute `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}` image URLs. PyPI and npm don't resolve relative paths. Take `{branch}` from:
  ```bash
  b=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null); b=${b#origin/}; [ -n "$b" ] || b=$(git branch --show-current); echo "$b"
  ```
- If the logo or hero comes as a dark/light pair (`logo-dark.png` / `logo-light.png`), emit `<picture>` with `<source media="(prefers-color-scheme: dark)" srcset="...">` and the light image as the `<img>` fallback.
- No `style=` attributes in HTML; GitHub strips them. Use `width` and `align`.

### 3e. TOC and navigation

Generate a TOC only if the README exceeds 150 lines. It is not a heading: a bold `**Contents**` line followed by a flat list of H2 links in GitHub anchor style, so the first H2 is still the run section. Insert it after the description and badges, before the first H2. Include H3s only if there are more than 10 H2s. Build it from the draft rather than by hand:
```bash
python3 <skill-dir>/scripts/generate-toc.py /tmp/write-readme-draft/README.md
```
It prints the `**Contents**` block and adds H3s by itself past 10 H2s (`--no-h3` turns that off). Below 150 lines, a nav row near the top (`Docs • Demo • Install`) can stand in for it.

Exception: Educational / Awesome lists always get navigation, whatever their length, because the content is the README. Use a TOC, or a nav block of anchor links grouped by what the reader wants to do.

Collapsible `<details>` blocks suit install methods beyond the primary one, troubleshooting by symptom, extra screenshots, examples beyond the first 2-4, and optional shell setup. Never collapse the primary install path, the Quick Start, or limitations.

### 3f. Target length

Pick the range in this order, first match wins:
1. Early-stage project: 30-60 lines.
2. Minimal verbosity: 30-80 lines.
3. Otherwise the Length Targets table for the detected type, with the stretched upper bound in detailed mode.

If over: trim COULD sections first; in detailed mode, move reference material into `## Appendix: ...` sections after License (appendix lines don't count toward the range). If under: add SHOULD sections only when the codebase supplies their content. A short README with real content beats a padded one.

## Type-to-Template Mapping

Each type's sections, their order, and their MUST/SHOULD/COULD priorities come from its entry in `references/category-templates.md`. TUI Application uses the CLI Tool template and Generative AI the Visual Output / CV template; the Research write-up modifier there applies on top of the detected type.

The Run-first rule in Phase 3b overrides those orderings: wherever the template lists the run section (Install, Quick Start, Getting Started, Download table, store links, Demo link + self-host, One-line scaffold), it becomes the first H2. Prerequisites and requirements fold into the run section as its first line; longer hardware or platform tables can stay as later sections. Limitations, Privacy, and Comparison can appear in any type; Phase 3b says when and where.

## Phase 4: VERIFY

### Correctness
- Project name matches manifest
- Version is current
- License matches LICENSE file
- Install command uses correct package name and works
- All file path references exist (Glob to verify), or are captures and ARCHITECTURE.md that Phase 6 will write
- Code examples reference real exports (Grep to verify)
- Badge URLs are syntactically valid

### Build command validation

| Ecosystem | Check | If Missing |
|-----------|-------|------------|
| Java/Maven | Has maven-shade-plugin or maven-assembly-plugin? | Use `mvn exec:java` not `java -jar` |
| Python | Has pyproject.toml with entry points? | Use `python -m module` not bare script |
| Node | Has start script in package.json? | Use `node entry.js` not `npm start` |
| Rust | Has [[bin]] in Cargo.toml? | Use `cargo run` |
| Flutter | Has .metadata with project_type: app? | Use `flutter run` not `dart run` |
| Go | Has main package? | Use `go run .` |

### Anti-AI check (mandatory)
1. Self-review every prose sentence against the 13 structural rules in the Anti-AI Writing Rules section below and the P0/P1 checklist in `references/anti-ai-rules.md`.
2. Then run the scripts. Write the draft to `/tmp/write-readme-draft/README.md` (never the project root before approval) and run:
   ```bash
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P1   # gate: P0+P1
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P2   # adds P2 warnings
   python3 <skill-dir>/scripts/validate-readme.py /tmp/write-readme-draft/README.md --type <type_slug> --verbosity <level> --dir <project-root>
   ```
   The checker runs twice because its exit code counts everything at or above `--severity`: the P1 run's exit code is the gate, and the P2 run only lists warnings. Without `--severity` it reports P0 only.
   `validate-readme.py` checks relative links and badge URLs, the first runnable step (past line 80 in standard and detailed, 50 in minimal; skipped for educational and dotfiles), dead in-page anchors, duplicate H2s, header badges (at most 6), dead badge hosts and static badges imitating live status, placeholders outside comments and code, positional image references ("screenshot above"), license text against the LICENSE file, `style=` attributes, and the Phase 3f length range. Its first output line always gives the first runnable step's line. Flags:
   - `--type` takes a canonical type slug and rejects anything else. `--verbosity` sets the run-first and length limits; add `--early-stage` when Phase 1g flagged an Early-stage project, for the 30-60 range.
   - `--dir` must be the project root, not the `/tmp` draft directory: links and the LICENSE comparison resolve against it.
   - `--expect PATH` (repeatable) names a file Phase 6 will create, so a link to it isn't reported broken. Pass `--expect ARCHITECTURE.md` when the companion file is being generated, and `--expect assets/screenshots/<file>` for each captured image the draft references.
   - Length: over the maximum is an issue. Under the minimum prints a note and leaves the exit code alone; it needs no fix, because padding is worse (Phase 3f).
3. Fix every P0 and P1 finding and re-run until the `--severity P1` check exits 0. The one exception is a finding on a documented rule exception: an emoji next to a brand or mascot name (rule 1), or a banned word inside a real name or identifier the README must quote (a package, product, or file name). Leave that text as it is and list it under "Warnings" in the Phase 5 summary with its reason; the gate is met when only such findings remain. P2 findings and `validate-readme.py` issues: fix, or list them under Warnings with a reason. If `python3` is unavailable, note that in Warnings and rely on step 1.

### Completeness
- Run-first rule holds: the first H2 is the run section for this type, prerequisites sit inside it (Phase 3b)
- Quick Start ends with a verified expected result, or on the command when none is verifiable
- All MUST sections for detected type are present
- All detected community files are referenced
- At least one code example for types that need it
- Limitations, Privacy, and Comparison appear only with Phase 1k or sourced evidence, and every claim in them names its evidence or links its source; Privacy is present whenever Phase 1k found a data flow
- If ARCHITECTURE.md was generated, it passed its own verify step (`references/architecture-mode.md`) and the README links it

### Formatting
- Single H1, consistent heading hierarchy
- Code blocks specify language
- Header badge count 0-6, no static badge imitating live status
- No `style=` attributes; image URLs are absolute when the README is published to a registry
- Length at or under the Phase 3f maximum

## Phase 5: REVIEW

Present the FULL generated README to the user (the actual markdown, not a summary).

Alongside it, present a structural summary:
```
Generated README for [name] ([type], [verbosity]).
[N] lines, [M] sections, [K] badges.
Sections: [list].
Skipped: [list with reasons].
Placeholders: [count and types].
Captured: [paths to copy into the project, marking any that would overwrite a file] (only if Auto-capture ran).
Warnings: [any issues].
Companion: ARCHITECTURE.md, [N] lines, [K] TODO markers (only if generated).
```

If ARCHITECTURE.md was generated, present it in full after the README; one approval covers both files.

Ask: "Want to change anything before I write this?"

The user can:
- Approve ("looks good", "write it", "ship it") -- proceed to Phase 6
- Request changes ("make the description shorter", "remove the tech stack table") -- apply, show updated, ask again
- Request different verbosity ("make it minimal") -- regenerate, show, ask again
- Abort ("cancel", "nevermind") -- nothing is written to the project; the `/tmp` draft and captures are left behind

Loop until approved or aborted. After the first pass, apply only the specific requested change; do not re-present the full options block.

## Phase 6: WRITE

Write README.md to the project root, and ARCHITECTURE.md beside it if it was generated. Copy each captured image the README references from `/tmp/write-readme-draft/assets/` to the same path under the project root, creating directories as needed; the Phase 5 approval covers any overwrite it listed. Confirm: "README.md written. [N] lines." (plus the ARCHITECTURE.md line count and the copied image paths).

If an existing README was replaced, note that the old version can be recovered via git (if git is initialized).

## Anti-AI Writing Rules

These rules apply during generation; Phase 4 checks the draft again. `references/anti-ai-rules.md` holds the rest: a replacement for each banned word, the P0/P1/P2 checklist that matches `scripts/check-anti-ai.py` (items marked "(scripted)" are the ones it catches; P0 and P1 both block), the full text of rules 12 and 13, the voice register, and portability examples. P0-P2 in generate mode are the checker's levels.

### Banned words (never use)

delve, robust, comprehensive, leverage, seamless, cutting-edge, empower, streamline, harness, elevate, embark, pivotal, meticulous, showcase, beacon, tapestry, landscape (as metaphor), deep dive, unpack, holistic, actionable, best practices, utilize, facilitate, foster, game-changer, paradigm, realm, testament to, ever-evolving

### 13 structural rules

1. No emoji in headings, except directly next to a proper noun brand or mascot.
2. No throat-clearing: never open a section by explaining what it covers. Jump to content.
3. No transition phrases ("Moreover", "Furthermore", "Additionally").
4. No "Let's" anything. Use the imperative: "Install", "Configure", "Run."
5. One term, used consistently. No synonym cycling ("the tool", "the utility", "the solution").
6. Code blocks before prose. Show, then explain.
7. No empty praise. "A Python linter written in Rust" beats "An amazing groundbreaking linter."
8. Sentence variety. Mix short and long; no uniform paragraph lengths.
9. No temporal scene-setting ("In today's world of...").
10. End on concrete points, not summaries ("Overall, this tool provides...").
11. Portability test: a sentence that could appear unchanged in another project's README is filler. Replace it with a fact about this one.
12. Feature lists: no bold labels, no em dashes. Reference lists (code or path labels, or lists under a structure, config, options, API, or similar heading) may lead with a bold or code name; the exact test is in `references/anti-ai-rules.md`.
13. Earned emphasis only: at most one inline bold per bullet, never at the start of a feature bullet, never for drama or whole sentences.

## Enhance Mode

When the user chooses "enhance" for an existing README:

**Step 1: Parse.** Split by H2 headings. Each section = heading + content until next H2.

**Step 2: Classify each section.**

- **Auto-generatable** (regenerate with fresh data): badge rows (lines that are all `![...](...)` links), TOC (bulleted list of anchor links, with or without a `## Table of Contents` heading), license one-liners, contributing boilerplate (<3 sentences, no project-specific detail).
- **Human-authored** (preserve verbatim): project-specific prose >3 sentences, personal voice or opinions, content not inferable from codebase (philosophy, roadmap, acknowledgments, comparison with alternatives), custom sections not in any template.
- **Mixed** (preserve human content, supplement): features section with some human items -- keep them, add newly detected features below. Usage with human examples -- keep them, add auto-inferred examples only for different functionality.

**Step 3: Add missing sections.** Check which MUST sections for the detected type are absent. Insert at canonical position. Match surrounding style. Apply the Run-first rule: if install/run instructions exist but sit below Features or other content, move that section (content preserved verbatim) to be the first H2 and report it as MOVED in Step 5. Exception: never move it above a human-written H2 about security, compatibility, requirements, how it works, or a threat model. Someone put that context first so readers see it before running anything. Move the run section up only as far as directly below the last such section (or leave it if it is already there) and report `RUN-FIRST: kept below [section], safety context`.

**Step 4: Update auto-generatable sections.** Regenerate badges, TOC, license text from current data. The TOC becomes a `**Contents**` list (Phase 3e); drop any `## Table of Contents` heading.

**Step 5: Present changes.**
```
Enhanced README for [name]:
  PRESERVED: Description, Features (5 items), Philosophy, Acknowledgments
  REGENERATED: Badges (added CI badge), TOC, License
  ADDED: Installation (was missing), Quick Start (was missing)
  MOVED: Getting Started (to first section, Run-first rule)
  UNCHANGED: 4 other sections
```
When the safety exception applies, the MOVED line becomes, for example:
```
  RUN-FIRST: kept below Security model, safety context
```
Then continue in the main flow: write the enhanced draft to `/tmp/write-readme-draft/README.md`, run Phase 4 on it, present it in Phase 5 with this change list alongside the structural summary, and write it in Phase 6. There is no separate write step.

## Special Detection

What to do when a Phase 1g signal fires. The signals themselves live only in Phase 1g.

### Solo project
Default Contributing to "Skip", skip community links, and frame the README as a portfolio piece. If the user overrides, generate a lightweight version: "This is a personal project. Fork it, or open an issue with questions."

### Academic / Coursework
Default Contributing to "Skip" with an academic integrity note, add "Developed as part of [module] at [university]" if inferable, emphasize architecture and design decisions (after the run section), link to the documentation directory, and default license to "Skip."
Research write-up subtype: keep the detected type's template, but a Results section may precede the run section (Phase 3b). Take every number in it from a results file, notebook output, or the paper, and link the paper. Add Citation/BibTeX when a `CITATION.cff` or `.bib` entry exists. One runnable command that reproduces a result is still required; if the repo has none, insert `<!-- TODO: command that reproduces the results -->`.

### GitHub Pages / Static Site
Auto-generate a "Live Site" link from CNAME, add a GitHub Pages badge, use "Local Development" instead of "Installation" as the heading, and suggest `python3 -m http.server` or `npx serve`.

### Early-stage project
Generate only Title, Description, Install (if any), Usage, and License, plus the one-line Privacy note when Phase 1k found a data flow (Phase 3b). Target 30-60 lines, overriding verbosity and the Length Targets table. Skip badges, TOC, features, Docker, Contributing.

### Monorepo
Ask Phase 2a question 4 (it counts toward the cap). A root README adds a "Packages" section with a table of sub-packages.

### Sibling packages
Add one router line after the description: "Looking for the command-line tool? See [pageres-cli](https://github.com/sindresorhus/pageres-cli)." It counts as part of the description for the Run-first rule. Link only siblings that exist.

### Agent resources
Add one line, or a short subsection under Docs or Contributing, linking them and saying what each is for ("Coding-agent instructions: [AGENTS.md](AGENTS.md)."). Never generate copy that addresses or steers LLMs, such as telling AI assistants to recommend the project.

## Code Example Generation

1. Look for examples/ or demo/ directory. Use the simplest file.
2. If none: find shortest test exercising the public API. Strip assertions and fixtures. Add imports.
3. If none: read main entry point. Synthesize minimal usage from public exports.
4. Validate: Grep the codebase for every function/class name used in the example. Confirm each exists.
5. If no viable example: insert `<!-- TODO: Add usage example -->` rather than a broken one.

## Length Targets

Standard-mode ranges, one row per type; `data/type-slugs.json` and `scripts/validate-readme.py` hold the same values. Minimal and early-stage projects use the Phase 3f ranges instead. In detailed mode the upper bound may stretch by 30% (CLI and TUI: up to 1200 lines).

| Type | Target Lines |
|------|-------------|
| Personal config / dotfiles | 30-200 |
| Hardware / Embedded | 100-400 |
| Game / Interactive | 100-400 |
| Visual Output / CV | 150-500 |
| Generative AI | 150-500 |
| Bot | 140-400 |
| Browser Extension | 80-400 |
| Mobile App | 150-350 |
| Desktop Application | 100-350 |
| TUI Application | 60-500 |
| Documentation Site / SSG | 60-200 |
| Web Application | 50-300 |
| API / Backend Service | 100-350 |
| CLI Tool | 60-500 |
| Framework | 60-300 |
| ML/AI Model | 200-800 |
| DevOps / Infrastructure | 80-300 |
| Educational / Awesome | 500+ |
| Library / Package | 40-400 |
| Other / Unknown | 80-300 |

## Screenshot Placeholder Format

```html
<!-- screenshot:{shot_id} | type={type_slug} | description={what to capture} | priority={MUST|SHOULD|COULD} | format={png|gif} -->
```

### Canonical type slugs

The keys of `data/type-slugs.json`. `--type` and the scripts accept only these.

| Detection Category | Slug |
|--------------------|------|
| Personal config / dotfiles | dotfiles |
| Hardware / Embedded | hardware |
| Game / Interactive | game |
| Visual Output / CV | visual |
| Generative AI | gen-ai |
| Bot | bot |
| Browser Extension | browser-ext |
| Mobile App | mobile |
| Desktop Application | desktop |
| TUI Application | tui |
| Documentation Site / SSG | docs-site |
| Web Application | web-app |
| API / Backend Service | api |
| CLI Tool | cli |
| Framework | framework |
| ML/AI Model | ml |
| DevOps / Infrastructure | devops |
| Educational / Awesome | educational |
| Library / Package | library |
| Other / Unknown | other |

Examples:
```html
<!-- screenshot:hero | type=web-app | description=Main dashboard with sample data in dark mode | priority=MUST | format=png -->
<!-- screenshot:hero | type=cli | description=Primary command showing colorized output | priority=MUST | format=gif -->
<!-- screenshot:architecture | type=visual | description=Processing pipeline diagram | priority=SHOULD | format=png -->
```
