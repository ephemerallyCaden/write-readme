---
name: readme
description: Generate polished, project-type-aware READMEs from codebase analysis. Use when asked to "generate a readme", "write a readme", "create a readme", or "/readme". Supports minimal/standard/detailed verbosity, 18 project types, anti-AI-slop writing rules, and optional screenshot capture.
---

# write-readme

Generate a README.md by analyzing the current codebase, asking 0-3 questions, and producing a project-type-aware document that reads like a human wrote it.

Output: `README.md` at the project root. If one exists, ask whether to enhance or replace.

## Invocation

Trigger phrases: "generate a readme", "write a readme", "create a readme", "/readme", "make a readme"

Options (natural language or flags):
- `/readme` -- standard verbosity, auto-detected type
- `/readme minimal` or "write a short readme" -- essentials only
- `/readme detailed` or "write a polished readme" -- all sections, comprehensive
- `/readme --type cli` -- override auto-detected project type

## Phase 1: ANALYZE

Run all steps silently. No user interaction.

### 1a. Detect manifests

```
Glob: package.json, pyproject.toml, setup.py, setup.cfg, Cargo.toml, go.mod, Gemfile, *.gemspec, pom.xml, build.gradle, build.gradle.kts, CMakeLists.txt, Makefile, mix.exs, pubspec.yaml, composer.json, Package.swift, *.cabal, dune-project
```

Read each found manifest. Extract: name, version, description, license, dependencies, scripts, entry points, engine/runtime requirements.

### 1b. Detect project type

Use the unified taxonomy below. First match wins (lowest priority number).

| Pri | Type | Detection Signals |
|-----|------|-------------------|
| 1 | Game / Interactive | `project.godot`, pygame/arcade/raylib/bevy/love2d imports, Phaser/PixiJS/Babylon imports, game asset dirs (sprites/, levels/, textures/) |
| 2 | Visual Output / CV | cv2/mediapipe/dlib imports + VideoCapture/imwrite/landmark/bounding.box. Also: matplotlib/plotly/d3/chart.js/bokeh/seaborn with data pipeline (Data Viz subtype) |
| 3 | Generative AI | diffusers/StableDiffusion/comfyui imports. Uses Visual Output template. |
| 4 | Bot | discord.py/discord.js/telegram/slack-bolt/botfather imports, bot token patterns |
| 5 | Browser Extension | manifest.json with permissions/content_scripts/background |
| 6 | Mobile App | pubspec.yaml (Flutter), react-native dep, android/+ios/ dirs, .xcodeproj |
| 7 | Desktop Application | Electron/Tauri/Qt/GTK/SwiftUI/WPF imports, .desktop files |
| 8 | TUI Application | textual/blessed/tview/bubbletea/cursive/crossterm/ncurses imports. Uses CLI Tool template. |
| 9 | Documentation Site / SSG | docusaurus.config/vitepress/mkdocs.yml/astro.config/sphinx conf.py |
| 10 | Web Application | Server framework (express/fastapi/flask/django/next/nuxt/svelte/rails) + dev/start/serve script + frontend files (pages/, components/, src/pages/, src/components/, templates/, public/, or index.html) |
| 11 | API / Backend Service | Server framework + NO frontend files. Everything that missed priority 10 for lack of frontend files lands here. |
| 12 | CLI Tool | bin in manifest, argparse/click/typer/clap/cobra imports, console_scripts entry point |
| 13 | Framework | Plugin system, middleware patterns, scaffolding CLI, create-* package |
| 14 | ML/AI Model | torch/tensorflow/jax imports + model dirs + training scripts (WITHOUT visual output signals) |
| 15 | DevOps / Infrastructure | Kubernetes manifests, Terraform files, Ansible playbooks, Helm charts |
| 16 | Educational / Awesome | awesome- prefix, curated link lists, no source code |
| 17 | Library / Package | exports/lib field, public API, no bin, no server framework |
| 18 | Other / Unknown | Nothing above matched -- infer from codebase |

### 1c. Scan community and config files

```
Glob: LICENSE*, CONTRIBUTING*, CODE_OF_CONDUCT*, SECURITY*, CHANGELOG*, CHANGES*, HISTORY*, .github/FUNDING.yml, .github/workflows/*, GOVERNANCE*, ROADMAP*, docs/
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

**Solo project:** contributors == 1 AND stars < 5 AND no CONTRIBUTING.md.
**Academic:** .university or .edu in manifest groupId/org, assessment brief files (instructions.md, brief.md, assignment.md), course module codes in repo name.
**GitHub Pages:** CNAME file at root, .nojekyll, raw index.html with no manifest, gh-pages branch.
**Early-stage:** No manifest OR manifest has <3 fields OR <5 source files.
**Monorepo:** workspaces in package.json, [workspace] in Cargo.toml, lerna.json, pnpm-workspace.yaml, packages/ or apps/ directory.

### 1h. Name resolution

Priority chain for display name:
1. App display name (AndroidManifest.xml android:label, Info.plist CFBundleDisplayName, MaterialApp title)
2. Manifest human-readable name (skip if it looks like a code identifier: underscores, no spaces, all lowercase)
3. Repo name from git remote
4. Directory name

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

Step 2 -- Look at each found image and decide if it belongs in a README. Not every image file is a screenshot. Read the image and judge:
- **App screen / UI render** (dashboard, settings, feature view) → use it
- **Diagram** (architecture, flowchart, pipeline) → use it
- **Terminal output** (CLI help, command demo) → use it
- **Logo** → use only in the title area, not as a screenshot
- **Icon / sprite / texture / favicon** → skip, internal asset
- **Diff image / coverage badge / test failure** → skip, test artifact
- **Design mockup** → use if it represents the actual app, skip if it's a wireframe draft

Only reference images that would help a reader understand what the project does or looks like. When in doubt, skip it. Record which template screenshot positions (MUST/SHOULD/COULD) the usable images cover.

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
```

Unanswered choices use defaults. "Go", "just do it", or Enter accepts all defaults.

### Verbosity levels

**minimal** -- Ship fast. Personal projects, prototypes, hackathons.
- Includes: Title, description (1-2 sentences), install, basic usage (one example), license
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
- Adds: comparison with alternatives, performance notes, detailed config, env vars table, directory tree
- Target: upper half of the type's range, up to the stretched detailed bound in Length Targets. Long reference material (full flag tables, header lists) may go in `## Appendix: ...` sections after License.
- Triggered by: "detailed", "comprehensive", "full", "polished", "landing page", "launch"

## Phase 3: GENERATE

### 3a. Select template

Pick the template matching the detected type (see Type-to-Template Mapping below).

### 3b. Generate section by section

Follow the template ordering, with one override:

**Run-first rule.** The first H2 is how to get the project running (heading: "Getting Started", "Quick Start", "Install", "Download", or "Local Development" for static sites). What counts as running depends on the type:
- Install + the command that runs, plays, or imports it: CLI, TUI, Library, Framework, ML, CV, Bot, DevOps, Other.
- A scaffold or template command that installs and runs in one step (`npm create ...`, `dotnet new ...`, `go run ...@latest`): Framework, Docs Site, project generators.
- A per-OS download table or store badges: Desktop, Mobile, Browser Extension, and Game when release binaries exist. Build-from-source steps go later.
- A hosted URL or one-click deploy button, followed by self-host commands: Web App, API, and Docs Site when a hosted version exists.

Before it, allow only: title, badges, description (≤2 sentences), hero image, nav row, TOC. Features, Architecture, Model tables, Sponsors, and everything else go after it. Prerequisites go inside the run section as its first line ("Requires Flutter 3.12+."), never as their own section before or after it. Keep the first command, download table, store badge, or hosted URL within the first 80 lines (50 in minimal).

Library / Package: a code snippet of 10 lines or fewer may precede the install line inside the first H2.

Exempt: Educational / Awesome lists, personal config / dotfiles repos (a browse index with nothing to install), and ARCHITECTURE.md.

Apply all anti-AI writing rules during generation (see section below), not only as a post-pass. The full catalog with replacements and register notes is in `references/anti-ai-rules.md` (relative to this skill's base directory). Read it before writing prose.

### 3c. Generate badges

```
1. Parse owner/repo from: git remote get-url origin
2. Detect registry:
   package.json -> npm | pyproject.toml/setup.py -> PyPI | Cargo.toml -> crates.io
   go.mod -> Go | Gemfile/gemspec -> RubyGems | pubspec.yaml -> pub.dev
   composer.json -> Packagist | pom.xml/build.gradle -> Maven Central
   mix.exs -> Hex.pm | *.cabal -> Hackage
   No match -> GitHub-only badges
3. Select 0-6 badges (ordered, flat style). Zero is fine; skip any badge without real data behind it:
   a. License: ![License](https://img.shields.io/github/license/{owner}/{repo})
   b. CI (if .github/workflows/ exists): ![CI](https://img.shields.io/github/actions/workflow/status/{owner}/{repo}/{workflow_file})
   c. Version (if published): registry-specific shield URL
   d. Downloads (if published): registry-specific shield URL
   e. Community (if Discord/Slack link found): appropriate badge
4. No git remote or private repo -> skip all shields.io badges
```

Never generate a static badge that imitates live status (`build-passing`, `maintained-yes`, `docs-available`). Static badges are only for facts that don't change with the build, such as language, framework, or platform. In detailed mode, keep at most one CI badge in the header and move per-workflow CI badges into a "Project status" table near the end.

### 3d. Visual assets

Use the images Phase 1j classified as usable. Reference them at the template's screenshot positions and read each one to write accurate alt text. For positions still uncovered:
- **MUST position**: act on the Phase 2b Screenshots answer. Auto-capture: delegate to the screenshot sub-skill at skills/screenshot/SKILL.md. I'll add later (the default): insert descriptive placeholders. Point to files: use the paths the user gave.
- **SHOULD/COULD position**: insert placeholders without asking.
- **Minimal verbosity**: use found images only; no placeholders, no capture unless the user chose Auto-capture.

### 3e. TOC and navigation

Generate a TOC only if the README exceeds 150 lines. Format: flat list of H2 headings, GitHub anchor style (lowercase, hyphens, strip special chars). Insert after description/badges, before first content section. Include H3s only if >10 H2 headings. Below 150 lines, a nav row under the description (`Docs • Demo • Install`) can stand in for it.

Exception: Educational / Awesome lists always get navigation, whatever their length, because the content is the README. Use a TOC, or a nav block of anchor links grouped by what the reader wants to do.

### 3f. Target length

Pick the range in this order, first match wins:
1. Early-stage project: 30-60 lines.
2. Minimal verbosity: 30-80 lines.
3. Otherwise the Length Targets table for the detected type, with the stretched upper bound in detailed mode.

If over: trim COULD sections first; in detailed mode, move reference material into `## Appendix: ...` sections after License (appendix lines don't count toward the range). If under: add SHOULD sections only when the codebase supplies their content. A short README with real content beats a padded one.

## Type-to-Template Mapping

These lists set which sections each type gets. Placement of the run section (Install, Quick Start, Getting Started, Download table, store links, Demo link + self-host, One-line scaffold) is governed by the Run-first rule in Phase 3b, which overrides the order shown here. Prerequisites and requirements listed below fold into the run section as its first line; longer hardware or platform tables can stay as later sections.

**Web Application:**
Title+Logo, Badges, Nav links, Description, `<!-- screenshot:hero -->`, Features, Demo link, Install (Docker-first), Config, Architecture, Docs, Contributing, Community, Sponsors, License

**CLI Tool:**
Title+Logo, Badges, Description, `<!-- screenshot:hero | format=gif -->`, TOC (if >150 lines), Install (multi-platform), Quick Start, Usage Examples, Command Reference, Config, Shell Integration, FAQ, Contributing, License

**Library / Package:**
Title+Logo, Badges, Description, Code Example (10 lines or fewer, may precede the install line inside the first H2), Features, Install, Quick Start, Usage (progressive), API/Docs link, Benchmarks, Sponsors, Contributing, License

**Framework:**
Title+Logo, Badges, Tagline, Description, Features/Why, Quick Start (scaffold command), Install, Docs, Ecosystem/Plugins, Migration, Community, Contributing, License

**Game / Interactive:**
Title+Logo, Badges, `<!-- screenshot:hero | format=gif -->`, Description, Features, Download/Play (binaries), How to Play/Controls, Install from source, Modding, Community, Contributing, Credits, License

**Visual Output / CV:**
Title+Logo, Badges, `<!-- screenshot:hero | description=Visual results demo -->`, Description, Features/Tasks, Model Performance table, Install (GPU reqs), Quick Start (CLI+Python), Supported Models, Architecture, Hardware Requirements, Citation/BibTeX, Contributing, License

**ML/AI Model:**
Title+Logo, Badges, Description, Architecture diagram, Supported Models table, Install (GPU), Quick Start, Usage (inference+training), Model Card, Training, Evaluation/Benchmarks, Citation/BibTeX, Contributing, License

**Desktop Application:**
Title+Logo, Badges, Tagline, `<!-- screenshot:hero -->`, Features, Download table (multi-store), Platform Compatibility, Setup/Config, Docs, Troubleshooting, Build from source, Contributing, License

**DevOps / Infrastructure:**
Title+Logo, Badges, Description, Architecture diagram, Features, Getting Started, Install (binary/Docker/Helm/source), Config, Docs, Governance, Contributing, Security, License

**Educational / Awesome:**
Title, Badges, Description, TOC or anchor nav block (mandatory, Phase 3e), Content sections by topic, Contributing, License

**Browser Extension:**
Title+Icon, Badges, Description, `<!-- screenshot:hero -->`, Install (per-browser store links), Supported Browsers, Features, Keyboard Shortcuts, Permissions/Privacy, Build from source, Contributing, License

**API / Backend Service:**
Title+Logo, Badges, Tagline, Quick Start code, Features, Architecture/Request flow, Install, Docs, Client Libraries/SDK table, API Reference, Deploy/Self-host, Config, Security, Contributing, License

**Mobile App:**
Title+Icon, Badges, Description, `<!-- screenshot:hero | description=Device screenshots -->`, Features, Download table (per-platform stores), Platform Compatibility, Docs, Translation/Localization, Build from source, Contributing, License

**Documentation Site / SSG:**
Title+Logo, Badges, Tagline, `<!-- screenshot:hero | description=Generated output -->`, Features, One-line scaffold, Docs, Showcase/"Trusted by", Deploy buttons, Contributing, License

**Bot:**
Title+Avatar, Tagline, Badges, Description, Features/Commands, Quick Start (bot registration as the prerequisite, then token, config, run), Config (.env), Commands reference, Plugins/Cogs, Docker, Contributing, License

**Other / Unknown:**
Title, Badges, Description, Features, Install, Quick Start, Docs, Contributing, License
(Add/remove sections based on codebase analysis. This is the minimal safe default.)

## Phase 4: VERIFY

### Correctness
- Project name matches manifest
- Version is current
- License matches LICENSE file
- Install command uses correct package name and works
- All file path references exist (Glob to verify)
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
1. Self-review every prose sentence against the P0 + P1 checks and the 13 structural rules in the Anti-AI Writing Rules section below.
2. Then run the scripted check. Write the draft to a temp file (e.g. `/tmp/write-readme-draft/README.md`, never the project root before approval) and run, with `<skill-dir>` being this skill's base directory:
   ```bash
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P1   # gate: P0+P1
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P2   # adds P2 style findings
   python3 <skill-dir>/scripts/validate-readme.py /tmp/write-readme-draft/README.md --type <type_slug> --verbosity <level> --dir <project-root>
   ```
   `--severity` is required: without it the checker reports P0 only.
3. Fix every P0 and P1 finding and re-run until the `--severity P1` check exits 0. P2 findings and `validate-readme.py` issues: fix, or list them under "Warnings" in the Phase 5 summary with a reason. If `python3` is unavailable, note that in Warnings and rely on step 1.

### Completeness
- Run-first rule holds: the first H2 is the run section for this type, prerequisites sit inside it (Phase 3b)
- All MUST sections for detected type are present
- All detected community files are referenced
- At least one code example for types that need it

### Formatting
- Single H1, consistent heading hierarchy
- Code blocks specify language
- Header badge count 0-6, no static badge imitating live status
- Length within the Phase 3f range

## Phase 5: REVIEW

Present the FULL generated README to the user (the actual markdown, not a summary).

Alongside it, present a structural summary:
```
Generated README for [name] ([type], [verbosity]).
[N] lines, [M] sections, [K] badges.
Sections: [list].
Skipped: [list with reasons].
Placeholders: [count and types].
Warnings: [any issues].
```

Ask: "Want to change anything before I write this?"

The user can:
- Approve ("looks good", "write it", "ship it") -- proceed to Phase 6
- Request changes ("make the description shorter", "remove the tech stack table") -- apply, show updated, ask again
- Request different verbosity ("make it minimal") -- regenerate, show, ask again
- Abort ("cancel", "nevermind") -- no file written

Loop until approved or aborted. After the first pass, apply only the specific requested change; do not re-present the full options block.

## Phase 6: WRITE

Write README.md to the project root. Confirm: "README.md written. [N] lines."

If an existing README was replaced, note that the old version can be recovered via git (if git is initialized).

## Anti-AI Writing Rules

These rules are constraints applied DURING generation; Phase 4 then checks the draft again. Internalize them before writing any prose.

### Banned words (never use)

delve, robust, comprehensive, leverage, seamless, cutting-edge, empower, streamline, harness, elevate, embark, pivotal, meticulous, showcase, beacon, tapestry, landscape (as metaphor), deep dive, unpack, holistic, actionable, best practices, utilize, facilitate, foster, game-changer, paradigm, realm, testament to, ever-evolving

### Replacement table

| Temptation | Write instead |
|------------|---------------|
| robust | reliable, solid |
| comprehensive | full, complete |
| leverage | use |
| seamless | smooth, easy |
| cutting-edge | latest |
| streamline | simplify |
| empower | let, enable |
| utilize | use |
| facilitate | enable, help |
| foster | build, support |
| in order to | to |
| serves as | is |
| it's worth noting | (cut -- just state the fact) |
| ecosystem (in prose) | system, community, network |

### 13 structural rules

1. No emoji in headings. Only exception: emoji directly next to a proper noun brand/mascot.
2. No throat-clearing. Never open a section by explaining what it covers. The heading does that. Jump to content.
3. No transition phrases. No "Moreover", "Furthermore", "Additionally" between sections.
4. No "Let's" anything. Imperative mood: "Install", "Configure", "Run."
5. One term, used consistently. No synonym cycling ("the tool", "the utility", "the application", "the solution").
6. Code blocks before prose. Show, then explain.
7. No empty praise. "A Python linter written in Rust" beats "An amazing groundbreaking linter."
8. Sentence variety. Mix short and long. No uniform paragraph lengths.
9. No "In today's world of..." -- ever. No temporal scene-setting.
10. End on concrete points, not summaries. No "Overall, this tool provides..." endings.
11. Every prose sentence must pass the portability test (see below).
12. Feature lists: no bold labels, no em dashes. Write plain bullets that start with the feature name followed by a colon or just flow into the description naturally. Do not repeat the same `**Name** -- description` pattern on every line. This applies to lists of features, capabilities, and benefits. Reference lists (files, directories, config keys, options, flags, languages) may lead with the name in backticks or bold, because the name is what the reader scans for.
13. Earned emphasis only. Bold a keyword only when it helps scanning: at most one inline bold per bullet, never at the start of a feature bullet (rule 12). Never bold for drama, and never bold whole sentences.

### Voice register

- Description: third person ("Flask is a lightweight framework")
- Instructions: imperative ("Install with pip", not "You can install with pip")
- Contributing: first person plural ("We welcome contributions")
- Tone: quietly confident. Declarative. No hedging on features that work. No superlatives unless backed by benchmarks.

### The portability test

If a sentence could appear in another project's README unchanged, it is filler. Replace it with a fact specific to THIS project.

Fails: "A powerful tool for modern developers." "Easy to get started." "Built with performance in mind."
Passes: "Compiles 100K lines of Python in under 200ms." "Mirror your Android screen at 30-120fps." "Manage your zsh configuration with 300+ plugins."

### Severity levels

These match `scripts/check-anti-ai.py`. P0 and P1 both block publishing (the Phase 4 gate is `--severity P1`); the split says which kind of failure it is. Items marked (scripted) are caught by the checker; the rest need self-review.

**P0 -- banned words (must fix)**
- No word from the banned list above (scripted, except "landscape", which is banned only as a metaphor)

**P1 -- chatbot and template phrasing (must fix)**
- No chatbot artifacts ("Feel free to...", "I hope this helps", "Don't hesitate to", "Please note that") (scripted)
- No template phrases ("in order to", "serves as a", "a wide range of", "a [adjective] step towards [adjective] [noun]") (scripted)
- No "Let's" openers (scripted)
- No emoji in headings (scripted)
- No bold-label or em-dash feature lists, rule 12 (scripted)
- No cutoff disclaimers ("As of my last update")
- No vague attributions ("Experts believe", "Studies show")
- No significance inflation on routine features
- No reasoning chain artifacts ("Let me break this down")
- No synonym cycling within the same section
- No formulaic openings ("In the rapidly evolving world of...")
- No "Whether you're X or Y" false-breadth
- No hedge-stacked predictions ("could potentially", "may eventually")
- No performed or narrated candor ("Let's be honest", "In the interest of transparency")
- No fake enthusiasm ("We're excited to...", "We're thrilled to...")
- No rhetorical questions in descriptions or prose. Questions are fine as FAQ entries and router lines ("Looking for the command-line tool? See ...").

**P2 -- polish (fix, or list under Warnings)**
- Section preambles ("This section covers...") (scripted). Rule 2 bans them, so fix these rather than listing them.
- Transition words opening a line: Moreover, Furthermore, Additionally (scripted)
- More than 2 em dashes in prose (scripted)
- Compulsive rule of three, uniform paragraph lengths, generic conclusions ("The future looks bright")

## Enhance Mode

When the user chooses "enhance" for an existing README:

**Step 1: Parse.** Split by H2 headings. Each section = heading + content until next H2.

**Step 2: Classify each section.**

- **Auto-generatable** (regenerate with fresh data): badge rows (lines that are all `![...](...)` links), TOC (bulleted list of anchor links), license one-liners, contributing boilerplate (<3 sentences, no project-specific detail).
- **Human-authored** (preserve verbatim): project-specific prose >3 sentences, personal voice or opinions, content not inferable from codebase (philosophy, roadmap, acknowledgments, comparison with alternatives), custom sections not in any template.
- **Mixed** (preserve human content, supplement): features section with some human items -- keep them, add newly detected features below. Usage with human examples -- keep them, add auto-inferred examples only for different functionality.

**Step 3: Add missing sections.** Check which MUST sections for the detected type are absent. Insert at canonical position. Match surrounding style. Apply the Run-first rule: if install/run instructions exist but sit below Features or other content, move that section (content preserved verbatim) to be the first H2 and report it as MOVED in Step 5. Exception: never move it above a human-written H2 about security, compatibility, requirements, how it works, or a threat model. Someone put that context first so readers see it before running anything. Move the run section up only as far as directly below the last such section (or leave it if it is already there) and report `RUN-FIRST: kept below [section], safety context`.

**Step 4: Update auto-generatable sections.** Regenerate badges, TOC, license text from current data.

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
Write after user confirms.

## Special Detection

### Solo project
Signals: 1 contributor, <5 stars, no CONTRIBUTING.md, no CI or `publish_to: none` or academic markers.
When detected: default Contributing to "Skip", suppress "PRs Welcome" badge, skip community links, frame as portfolio/showcase. If user overrides, generate lightweight version: "This is a personal project. Fork it, or open an issue with questions."

### Academic / Coursework
Signals: .university or .edu in manifest groupId/org, assessment brief files, single contributor, no license, module codes in repo name.
When detected: default Contributing to "Skip" with academic integrity note, add "Developed as part of [module] at [university]" if inferable, emphasize architecture and design decisions (after the run section), link to documentation directory, no "PRs Welcome" badge, default license to "Skip."

### GitHub Pages / Static Site
Signals: CNAME at root, .nojekyll, raw index.html with no manifest, gh-pages branch.
When detected: auto-generate "Live Site" link from CNAME, add GitHub Pages badge, use "Local Development" instead of "Installation" as heading, suggest `python3 -m http.server` or `npx serve`.

### Early-stage project
Signals: no manifest OR manifest <3 fields OR <5 source files.
When detected: generate only Title, Description, Install (if any), Usage, License. Target 30-60 lines, overriding verbosity and the Length Targets table. Skip badges, TOC, features, Docker, Contributing.

### Monorepo
Signals: workspaces in package.json, [workspace] in Cargo.toml, lerna.json, pnpm-workspace.yaml, packages/ or apps/ directory.
When detected: ask "Generate README for the root monorepo or a specific package?" (Phase 2a question 4, counts toward the cap). Root README adds a "Packages" section with table of sub-packages.

### Name resolution
Never use internal package identifiers (underscored, no spaces, all lowercase) as the README title. Follow the priority chain in Phase 1h.

## Code Example Generation

1. Look for examples/ or demo/ directory. Use the simplest file.
2. If none: find shortest test exercising the public API. Strip assertions and fixtures. Add imports.
3. If none: read main entry point. Synthesize minimal usage from public exports.
4. Validate: Grep the codebase for every function/class name used in the example. Confirm each exists.
5. If no viable example: insert `<!-- TODO: Add usage example -->` rather than a broken one.

## Badge Generation

1. Extract owner/repo: `git remote get-url origin` then parse `github.com/{owner}/{repo}`
2. Detect registry from manifest type (see Phase 3c mapping)
3. Extract package name from manifest
4. Select 0-6 badges (ordered, flat style): License, CI, Version, Downloads, Community. No static badges that imitate live status (Phase 3c)
5. No git remote or private repo: skip shields.io badges entirely

## Length Targets

Standard-mode ranges. Minimal and early-stage projects use the Phase 3f ranges instead. In detailed mode the upper bound may stretch by 30% (CLI and TUI: up to 1200 lines).

| Type | Target Lines |
|------|-------------|
| Web Application | 50-300 |
| CLI Tool / TUI | 60-500 |
| Library / Package | 40-400 |
| Framework | 60-300 |
| Game / Interactive | 100-400 |
| Visual Output / CV | 150-500 |
| ML/AI Model | 200-800 |
| Desktop Application | 100-350 |
| DevOps / Infrastructure | 80-300 |
| Educational / Awesome | 500+ |
| Browser Extension | 80-400 |
| API / Backend Service | 100-350 |
| Mobile App | 150-350 |
| Documentation Site / SSG | 60-200 |
| Bot | 140-400 |
| Other | 80-300 |

## Screenshot Placeholder Format

```html
<!-- screenshot:{shot_id} | type={type_slug} | description={what to capture} | priority={MUST|SHOULD|COULD} | format={png|gif} -->
```

### Canonical type slugs

| Detection Category | Slug |
|--------------------|------|
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
