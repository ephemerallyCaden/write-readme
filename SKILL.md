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
| 10 | Web Application | Server framework (express/fastapi/flask/django/next/nuxt/svelte/rails) + dev/start/serve script |
| 11 | API / Backend Service | Server framework + NO frontend files (no pages/, components/, public/index.html) |
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

If CLI tool detected, run:
```bash
timeout 5 <entry_point> --help 2>&1 || true
```

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

### 1i. Supplementary docs

```bash
find . -maxdepth 3 -name "*.md" -not -name "README*" -not -name "LICENSE*" -not -name "CONTRIBUTING*" -not -name "CODE_OF_CONDUCT*" -not -name "SECURITY*" -not -name "CHANGELOG*" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null
```

Read the first 5 lines of each to understand its purpose. Link significant docs in the generated README.

## Phase 2: ASK

### 2a. Required questions (0-3 max, priority ordered)

When more than 3 would be needed, use this priority:
1. "Enhance existing or generate fresh?" -- only if existing README found
2. "Describe your project in 1-2 sentences -- what does it do and who is it for?" -- SKIP if manifest description >10 words AND no existing README
3. "This looks like both a [type A] and [type B]. Which is its primary identity?" -- only if type detection is ambiguous
4. If monorepo: "Generate README for the root monorepo or a specific package?"

Hard cap: 3 required questions. After 3, infer everything remaining.

### 2b. Optional choices (single block, all skippable)

Present after required questions:

```
Before I generate, a few quick choices (press Enter to skip any):

 License:       [MIT] [Apache-2.0] [GPL-3.0] [Skip -- no license]
                Default: Skip if none exists, keep current if one exists

 Contributing:  [Include section] [Skip]
                Default: Include for multi-contributor projects, Skip for solo/academic

 Verbosity:     [Minimal] [Standard] [Detailed]
                Default: Standard (or inferred from context)

 Screenshots:   [Auto-capture] [I'll add later] [Point to files]
                Only shown if no screenshots AND visual project type
```

Unanswered choices use defaults. "Go", "just do it", or Enter accepts all defaults.

### Verbosity levels

**minimal** -- Ship fast. Personal projects, prototypes, hackathons.
- Includes: Title, description (1-2 sentences), install, basic usage (one example), license
- Skips: badges, features, TOC, contributing, community, sponsors, architecture
- No screenshot placeholders
- Target: 30-80 lines
- Triggered by: "minimal", "short", "quick", "simple", "brief", or <5 source files

**standard** (default) -- Balanced README. Most projects.
- Includes: all MUST sections + SHOULD sections where data is available
- Skips: COULD sections unless data already exists
- Screenshot placeholders follow Phase 3d flow
- Target: ideal length for detected type (see Length Targets)
- Triggered by: default when no preference stated

**detailed** -- Polished landing page. Open source launches, portfolio pieces.
- Includes: all MUST + SHOULD + COULD sections
- Adds: comparison with alternatives, performance notes, detailed config, env vars table, directory tree, star history widget, contributor graph
- Target: upper end of ideal length or above
- Triggered by: "detailed", "comprehensive", "full", "polished", "landing page", "launch"

## Phase 3: GENERATE

### 3a. Select template

Pick the template matching the detected type (see Type-to-Template Mapping below).

### 3b. Generate section by section

Follow the template ordering, with one override:

**Run-first rule.** The first H2 section is always how to get the project running: install + the command that runs, plays, or imports it (heading: "Getting Started", "Quick Start", "Install", or "Local Development" for static sites). Only the title, badges, 1-2 sentence description, hero image, and TOC may come before it. Features, Architecture, Download tables, Model tables, Prerequisites prose, and everything else go after it. For Library / Package the minimal code example may sit inside this first section alongside install. For Educational / Awesome lists (no runnable code) this rule does not apply.

Apply all anti-AI writing rules during generation (see section below), not as a post-pass. The full catalog with replacements and register notes is in `references/anti-ai-rules.md` (relative to this skill's base directory). Read it before writing prose.

### 3c. Generate badges

```
1. Parse owner/repo from: git remote get-url origin
2. Detect registry:
   package.json -> npm | pyproject.toml/setup.py -> PyPI | Cargo.toml -> crates.io
   go.mod -> Go | Gemfile/gemspec -> RubyGems | pubspec.yaml -> pub.dev
   composer.json -> Packagist | pom.xml/build.gradle -> Maven Central
   mix.exs -> Hex.pm | *.cabal -> Hackage
   No match -> GitHub-only badges
3. Select badges (ordered, max 6, flat style):
   a. License: ![License](https://img.shields.io/github/license/{owner}/{repo})
   b. CI (if .github/workflows/ exists): ![CI](https://img.shields.io/github/actions/workflow/status/{owner}/{repo}/{workflow_file})
   c. Version (if published): registry-specific shield URL
   d. Downloads (if published): registry-specific shield URL
   e. Community (if Discord/Slack link found): appropriate badge
4. No git remote or private repo -> skip all shields.io badges
```

### 3d. Visual assets

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

Only reference images that would help a reader understand what the project does or looks like. When in doubt, skip it.

Step 3 -- Branch:
- **Usable screenshots found**: Use them. Reference at correct template positions. Read each image to write accurate alt text. If some MUST positions are still uncovered, treat those as "no assets."
- **Only internal assets found (no screenshots)**: Treat as "no assets."
- **No assets + template says MUST**: Ask the user: "(a) Auto-capture now, (b) Skip -- I'll leave placeholders, (c) I have images -- let me point you to them." If (a), delegate to screenshot sub-skill at skills/screenshot/SKILL.md. If (b), insert descriptive placeholders. If (c), user provides paths.
- **No assets + template says SHOULD/COULD**: Skip silently. Insert placeholders without asking.

### 3e. TOC

Generate only if the README exceeds 150 lines. Format: flat list of H2 headings, GitHub anchor style (lowercase, hyphens, strip special chars). Insert after description/badges, before first content section. Include H3s only if >10 H2 headings.

### 3f. Target length

Check the Length Targets table for the detected type. If over: trim COULD sections. If under: add missing SHOULD sections.

## Type-to-Template Mapping

These lists set which sections each type gets. Placement of Install / Quick Start / Getting Started is governed by the Run-first rule in Phase 3b, which overrides the order shown here.

**Web Application:**
Title+Logo, Badges, Nav links, Description, `<!-- screenshot:hero -->`, Features, Demo link, Install (Docker-first), Config, Architecture, Docs, Contributing, Community, Sponsors, License

**CLI Tool:**
Title+Logo, Badges, Description, `<!-- screenshot:hero | format=gif -->`, TOC (if >150 lines), Install (multi-platform), Quick Start, Usage Examples, Command Reference, Config, Shell Integration, FAQ, Contributing, License

**Library / Package:**
Title+Logo, Badges, Description, Code Example (before install), Features, Install, Quick Start, Usage (progressive), API/Docs link, Benchmarks, Sponsors, Contributing, License

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
Title, Badges, Description, TOC (mandatory), Content sections by topic, Contributing, License

**Browser Extension:**
Title+Icon, Badges, Description, `<!-- screenshot:hero -->`, Install (per-browser store links), Supported Browsers, Features, Keyboard Shortcuts, Permissions/Privacy, Build from source, Contributing, License

**API / Backend Service:**
Title+Logo, Badges, Tagline, Quick Start code, Features, Architecture/Request flow, Install, Docs, Client Libraries/SDK table, API Reference, Deploy/Self-host, Config, Security, Contributing, License

**Mobile App:**
Title+Icon, Badges, Description, `<!-- screenshot:hero | description=Device screenshots -->`, Features, Download table (per-platform stores), Platform Compatibility, Docs, Translation/Localization, Build from source, Contributing, License

**Documentation Site / SSG:**
Title+Logo, Badges, Tagline, `<!-- screenshot:hero | description=Generated output -->`, Features, One-line scaffold, Docs, Showcase/"Trusted by", Deploy buttons, Contributing, License

**Bot:**
Title+Avatar, Tagline, Badges, Description, Features/Commands, Prerequisites (bot registration), Quick Start (register, token, config, run), Config (.env), Commands reference, Plugins/Cogs, Docker, Contributing, License

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
1. Self-review every prose sentence against the P0 + P1 checks and the 12 structural rules in the Anti-AI Writing Rules section below.
2. Then run the scripted check. Write the draft to a temp file (e.g. `/tmp/write-readme-draft/README.md`, never the project root before approval) and run, with `<skill-dir>` being this skill's base directory:
   ```bash
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P1   # gate: P0+P1
   python3 <skill-dir>/scripts/check-anti-ai.py --file /tmp/write-readme-draft/README.md --severity P2   # adds P2 style findings
   python3 <skill-dir>/scripts/validate-readme.py /tmp/write-readme-draft/README.md --type <type_slug> --verbosity <level> --dir <project-root>
   ```
   `--severity` is required: without it the checker reports P0 only.
3. Fix every P0 and P1 finding and re-run until the `--severity P1` check exits 0. P2 findings and `validate-readme.py` issues: fix, or list them under "Warnings" in the Phase 5 summary with a reason. If `python3` is unavailable, note that in Warnings and rely on step 1.

### Completeness
- Run-first rule holds: the first H2 is install/run (Phase 3b)
- All MUST sections for detected type are present
- All detected community files are referenced
- At least one code example for types that need it

### Formatting
- Single H1, consistent heading hierarchy
- Code blocks specify language
- Badge count 3-6
- Length within target range

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

These rules are constraints applied DURING generation, not post-hoc. Internalize them before writing any prose.

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

### 12 structural rules

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
12. Feature lists: no bold labels, no em dashes. Write plain bullets that start with the feature name followed by a colon or just flow into the description naturally. Do not repeat the same `**Name** -- description` pattern on every line.

### Voice register

- Description: third person ("Flask is a lightweight framework")
- Instructions: imperative ("Install with pip", not "You can install with pip")
- Contributing: first person plural ("We welcome contributions")
- Tone: quietly confident. Declarative. No hedging on features that work. No superlatives unless backed by benchmarks.

### The portability test

If a sentence could appear in another project's README unchanged, it is filler. Replace it with a fact specific to THIS project.

Fails: "A powerful tool for modern developers." "Easy to get started." "Built with performance in mind."
Passes: "Compiles 100K lines of Python in under 200ms." "Mirror your Android screen at 30-120fps." "Manage your zsh configuration with 300+ plugins."

### P0 checks (credibility killers -- must fix)
- No chatbot artifacts ("Feel free to...", "I hope this helps", "Great question")
- No cutoff disclaimers ("As of my last update")
- No vague attributions ("Experts believe", "Studies show")
- No significance inflation on routine features
- No reasoning chain artifacts ("Let me break this down")

### P1 checks (AI smell -- fix before publishing)
- No Tier 1A words (see banned list above)
- No template phrases ("a [adjective] step towards [adjective] [noun]")
- No "Let's" openers
- No synonym cycling within the same section
- No formulaic openings ("In the rapidly evolving world of...")
- No "Whether you're X or Y" false-breadth
- No performed candor ("Let's be honest")
- No narrated candor ("In the interest of transparency")
- No section preambles explaining what the section covers
- No fake enthusiasm ("We're excited to...", "We're thrilled to...")

## Enhance Mode

When the user chooses "enhance" for an existing README:

**Step 1: Parse.** Split by H2 headings. Each section = heading + content until next H2.

**Step 2: Classify each section.**

- **Auto-generatable** (regenerate with fresh data): badge rows (lines that are all `![...](...)` links), TOC (bulleted list of anchor links), license one-liners, contributing boilerplate (<3 sentences, no project-specific detail).
- **Human-authored** (preserve verbatim): project-specific prose >3 sentences, personal voice or opinions, content not inferable from codebase (philosophy, roadmap, acknowledgments, comparison with alternatives), custom sections not in any template.
- **Mixed** (preserve human content, supplement): features section with some human items -- keep them, add newly detected features below. Usage with human examples -- keep them, add auto-inferred examples only for different functionality.

**Step 3: Add missing sections.** Check which MUST sections for the detected type are absent. Insert at canonical position. Match surrounding style. Apply the Run-first rule: if install/run instructions exist but sit below Features or other content, move that section (content preserved verbatim) to be the first H2 and report it as MOVED in Step 5.

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
Write after user confirms.

## Special Detection

### Solo project
Signals: 1 contributor, <5 stars, no CONTRIBUTING.md, no CI or `publish_to: none` or academic markers.
When detected: default Contributing to "Skip", suppress "PRs Welcome" badge, skip community links, frame as portfolio/showcase. If user overrides, generate lightweight version: "This is a personal project. Feel free to fork it or open issues for questions."

### Academic / Coursework
Signals: .university or .edu in manifest groupId/org, assessment brief files, single contributor, no license, module codes in repo name.
When detected: default Contributing to "Skip" with academic integrity note, add "Developed as part of [module] at [university]" if inferable, emphasize architecture and design decisions, link to documentation directory, no "PRs Welcome" badge, default license to "Skip."

### GitHub Pages / Static Site
Signals: CNAME at root, .nojekyll, raw index.html with no manifest, gh-pages branch.
When detected: auto-generate "Live Site" link from CNAME, add GitHub Pages badge, use "Local Development" instead of "Installation" as heading, suggest `python3 -m http.server` or `npx serve`.

### Early-stage project
Signals: no manifest OR manifest <3 fields OR <5 source files.
When detected: generate only Title, Description, Install (if any), Usage, License. Target 30-60 lines. Skip badges, TOC, features, Docker, Contributing.

### Monorepo
Signals: workspaces in package.json, [workspace] in Cargo.toml, lerna.json, pnpm-workspace.yaml, packages/ or apps/ directory.
When detected: ask "Generate README for the root monorepo or a specific package?" Root README adds a "Packages" section with table of sub-packages.

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
4. Select badges (ordered, max 6, flat style): License, CI, Version, Downloads, Community
5. No git remote or private repo: skip shields.io badges entirely

## Length Targets

| Type | Target Lines |
|------|-------------|
| Web Application | 100-300 |
| CLI Tool | 200-1200 |
| Library / Package | 50-400 |
| Framework | 100-300 |
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
