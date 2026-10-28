# Category-Specific README Structure Templates

> 15 project types, 45+ repos analyzed. Each template defines section ordering, MUST/SHOULD/COULD priorities, above-the-fold content, ideal length, and unique sections.

> **Ordering override:** SKILL.md Phase 3b's Run-first rule wins over the orderings below. The install/run section is always the first H2 after title, badges, description, hero image, and TOC.

---

## Quick Reference: Unique Sections by Category

| Category | Unique Section(s) |
|---|---|
| **Web Application** | Demo/live instance, Self-hosting/Docker, Architecture diagram |
| **CLI Tool** | Shell integration/completions, Command reference, Environment variables |
| **Library / Package** | API Reference, Dependencies, Code-before-install |
| **Framework** | Scaffold command, Ecosystem/Plugins, Migration guide |
| **Game / Interactive** | How to Play/Controls, Download/Play (binaries), Modding |
| **Visual Output / CV** | Visual output demos, Model performance tables, Hardware requirements |
| **ML/AI Model** | Model Card, Citation/BibTeX, Training instructions, Evaluation metrics |
| **Desktop Application** | Platform compatibility table, Multi-store download table, Per-platform build |
| **DevOps / Infrastructure** | Architecture diagram, Governance, Adopters, Configuration (YAML/HCL) |
| **Educational / Awesome** | Content IS the README, TOC mandatory, Back-to-top links |
| **Browser Extension** | Per-browser install links, Supported Browsers, Permissions/Privacy, Key bindings |
| **API / Backend Service** | Client Libraries/SDK table, Request flow diagram, API Reference link |
| **Mobile App** | Device screenshots, Store badges, Platform compatibility, Translation/Localization |
| **Documentation Site / SSG** | Generated output screenshot, Deploy buttons, Showcase/"Trusted by" |
| **Bot** | Bot registration steps, Commands reference, Token/config setup, Plugins/Cogs |

---

## Ideal Length Summary

| Category | Lines | Model |
|---|---|---|
| Web Application | 100-300 | Hub-and-spoke |
| CLI Tool | 200-1200 | README as docs |
| Library / Package | 50-400 | Hub-and-spoke to comprehensive |
| Framework | 100-300 | Hub-and-spoke |
| Game / Interactive | 100-400 | Moderate, visual-heavy |
| Visual Output / CV | 150-500 | Visual + tables |
| ML/AI Model | 200-800 | Comprehensive |
| Desktop Application | 100-350 | Visual + download-heavy |
| DevOps / Infrastructure | 80-300 | Hub-and-spoke |
| Educational / Awesome | 500-3000+ | Content IS README |
| Browser Extension | 80-400 | Moderate |
| API / Backend Service | 100-350 | Code-first hub-and-spoke |
| Mobile App | 150-350 | Visual + download-heavy |
| Documentation Site / SSG | 60-200 | Ultra-hub-and-spoke |
| Bot | 140-400 | Setup-heavy |

---

## Cross-Category Section Matrix

| Section | WebApp | CLI | Lib | Frame | Game | CV | ML | Desktop | DevOps | Edu | BrExt | API | Mobile | Docs | Bot |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Logo/Banner | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | COULD | MUST | MUST | MUST | MUST | MUST |
| Badges | SHOULD | SHOULD | MUST | MUST | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | MUST | SHOULD | SHOULD | SHOULD |
| Screenshot/Demo | MUST | MUST(GIF) | -- | COULD | MUST | MUST | COULD | MUST | -- | -- | SHOULD | -- | MUST | SHOULD | -- |
| Description | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST |
| Features | MUST | SHOULD | SHOULD | SHOULD | SHOULD | MUST | SHOULD | MUST | MUST | -- | MUST | MUST | MUST | SHOULD | MUST |
| Code Example | -- | SHOULD | MUST | SHOULD | -- | SHOULD | SHOULD | -- | COULD | -- | -- | MUST | -- | -- | -- |
| Install | MUST | MUST | MUST | MUST | SHOULD | MUST | MUST | MUST | MUST | -- | MUST | MUST | MUST | MUST | MUST |
| Quick Start | MUST | MUST | MUST | MUST | -- | MUST | MUST | -- | MUST | -- | -- | MUST | -- | MUST | MUST |
| Docs link | MUST | COULD | MUST | MUST | SHOULD | MUST | MUST | SHOULD | MUST | -- | COULD | MUST | SHOULD | MUST | SHOULD |
| TOC | COULD | MUST* | COULD | COULD | COULD | COULD | COULD | COULD | COULD | MUST | COULD | COULD | COULD | -- | COULD |
| Contributing | MUST | SHOULD | SHOULD | MUST | SHOULD | SHOULD | SHOULD | MUST | MUST | MUST | SHOULD | MUST | MUST | MUST | SHOULD |
| License | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST |

*MUST if over 200 lines

---

## Full Templates

### 1. Web Application

**Section ordering:**
Title+Logo, Badges, Nav links, Description, `<!-- screenshot:hero -->`, Features, Demo link, Install (Docker-first), Config, Architecture, Docs, Roadmap, Contributing, Community, Sponsors, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | Centered, linked to live instance if available |
| Badges | SHOULD | License, CI, version |
| Nav links | SHOULD | Docs, Demo, Community, Sponsors |
| Description | MUST | What it does, who it is for |
| Screenshot/Demo | MUST | Hero screenshot of main dashboard with data |
| Features | MUST | Plain bullets, feature name first; a concrete number or named spec in each (no bold labels, rule 12) |
| Demo link | SHOULD | Link to live instance |
| Install (Docker-first) | MUST | Docker Compose is the primary path |
| Config | SHOULD | Environment variables, .env setup |
| Architecture | COULD | System diagram (Mermaid) |
| Docs | MUST | Link to documentation site |
| Roadmap | COULD | Link to GitHub project board |
| Contributing | MUST | Link to CONTRIBUTING.md |
| Community | SHOULD | Discord, forum links |
| Sponsors | COULD | Tiered sponsor logos |
| License | MUST | Type + link |

**Ideal length:** 100-300 lines
**Model:** Hub-and-spoke (README is landing page, docs site has depth)

---

### 2. CLI Tool

**Section ordering:**
Title+Logo, Badges, Description, `<!-- screenshot:hero | format=gif -->`, TOC (if >150 lines), Install (multi-platform), Quick Start, Usage Examples, Command Reference, Config, Shell Integration, FAQ, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Description | MUST | What it does, what it replaces |
| Screenshot (GIF) | MUST | Animated demo of core command |
| TOC | MUST* | *Required if >200 lines |
| Install (multi-platform) | MUST | Homebrew, apt, cargo, pip, npm, binary |
| Quick Start | MUST | One command that shows value |
| Usage Examples | SHOULD | Progressive: basic, intermediate, piped |
| Command Reference | SHOULD | Flags table or link to man page |
| Config | SHOULD | Config file location and options |
| Shell Integration | COULD | Completions, aliases, shell hooks |
| FAQ | COULD | Common issues |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 200-1200 lines
**Model:** README as docs (CLI tools often have no docs site)

---

### 3. Library / Package

**Section ordering:**
Title+Logo, Badges, Description, Code Example (before install), Features, Install, Quick Start, Usage (progressive), API/Docs link, Benchmarks, Sponsors, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | MUST | Version, downloads, CI, license |
| Description | MUST | Category-value format |
| Code Example | MUST | Before install -- show what using this looks like |
| Features | SHOULD | Plain bullets, feature name first; a concrete number or named spec in each (no bold labels, rule 12) |
| Install | MUST | Package manager command |
| Quick Start | MUST | Minimal working example |
| Usage (progressive) | SHOULD | Basic, realistic, advanced |
| API/Docs link | MUST | Link to generated API docs |
| Benchmarks | COULD | If performance is a selling point |
| Sponsors | COULD | |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 50-400 lines
**Model:** Hub-and-spoke (with docs site) or comprehensive (without)

---

### 4. Framework

**Section ordering:**
Title+Logo, Badges, Tagline, Description, Features/Why, Quick Start (scaffold command), Install, Docs, Ecosystem/Plugins, Migration, Community, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | MUST | |
| Tagline | SHOULD | Punchy one-liner |
| Description | MUST | What it does, philosophy |
| Features/Why | SHOULD | Why this framework over alternatives |
| Quick Start | MUST | Scaffold command that gets a project running |
| Install | MUST | |
| Docs | MUST | Link to comprehensive docs |
| Ecosystem/Plugins | SHOULD | Available integrations |
| Migration | COULD | From previous versions or competing frameworks |
| Community | SHOULD | |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 100-300 lines
**Model:** Hub-and-spoke (framework docs are always external)

---

### 5. Game / Interactive

**Section ordering:**
Title+Logo, Badges, `<!-- screenshot:hero | format=gif -->`, Description, Features, Download/Play (binaries), How to Play/Controls, Install from source, Modding, Community, Contributing, Credits, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Screenshot/Gameplay GIF | MUST | Gameplay mid-action, not title screen |
| Description | MUST | Genre, core mechanic, platform |
| Features | SHOULD | Game features, not technical features |
| Download/Play | SHOULD | Pre-built binaries, itch.io, Steam links |
| How to Play/Controls | SHOULD | Keybindings, controls table |
| Install from source | SHOULD | For developers who want to build |
| Modding | COULD | If the game supports mods |
| Community | SHOULD | Discord for multiplayer games |
| Contributing | SHOULD | |
| Credits | COULD | Art, music, sound attributions |
| License | MUST | |

**Ideal length:** 100-400 lines
**Model:** Moderate, visual-heavy

---

### 6. Visual Output / CV

**Section ordering:**
Title+Logo, Badges, `<!-- screenshot:hero | description=Visual results demo -->`, Description, Features/Tasks, Model Performance table, Install (GPU reqs), Quick Start (CLI+Python), Supported Models, Architecture, Hardware Requirements, Citation/BibTeX, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Visual results demo | MUST | The output IS the hero image |
| Description | MUST | What it detects/generates/transforms |
| Features/Tasks | MUST | Supported tasks with visual examples |
| Model Performance | SHOULD | Accuracy/speed table per model variant |
| Install (GPU reqs) | MUST | CUDA/ROCm requirements, pip install |
| Quick Start | MUST | CLI and Python API examples |
| Supported Models | SHOULD | Model variants, sizes, trade-offs |
| Architecture | COULD | Pipeline diagram |
| Hardware Requirements | SHOULD | GPU memory, CPU fallback |
| Citation/BibTeX | SHOULD | For academic projects |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 150-500 lines
**Model:** Visual + tables

---

### 7. ML/AI Model

**Section ordering:**
Title+Logo, Badges, Description, Architecture diagram, Supported Models table, Install (GPU), Quick Start, Usage (inference+training), Model Card, Training, Evaluation/Benchmarks, Citation/BibTeX, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Description | MUST | Model type, task, key result |
| Architecture diagram | SHOULD | Model/pipeline architecture |
| Supported Models table | MUST | Variants, parameters, performance |
| Install (GPU) | MUST | CUDA requirements, pip install |
| Quick Start | MUST | Inference in 3-5 lines |
| Usage (inference+training) | SHOULD | Separate inference and training examples |
| Model Card | COULD | Training data, limitations, biases |
| Training | SHOULD | How to train/fine-tune |
| Evaluation/Benchmarks | SHOULD | Metrics on standard datasets |
| Citation/BibTeX | MUST | For academic projects |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 200-800 lines
**Model:** Comprehensive

---

### 8. Desktop Application

**Section ordering:**
Title+Logo, Badges, Tagline, `<!-- screenshot:hero -->`, Features, Download table (multi-store), Platform Compatibility, Setup/Config, Docs, Troubleshooting, Build from source, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Tagline | SHOULD | |
| Screenshot | MUST | Main window with content loaded |
| Features | MUST | End-user features, not technical |
| Download table | MUST | Windows/macOS/Linux, store links |
| Platform Compatibility | SHOULD | OS versions, architectures |
| Setup/Config | SHOULD | First-run configuration |
| Docs | SHOULD | Link to docs if available |
| Troubleshooting | COULD | Common issues |
| Build from source | SHOULD | Per-platform build instructions |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 100-350 lines
**Model:** Visual + download-heavy

---

### 9. DevOps / Infrastructure

**Section ordering:**
Title+Logo, Badges, Description, Architecture diagram, Features, Getting Started, Install (binary/Docker/Helm/source), Config, Docs, Governance, Contributing, Security, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Description | MUST | What infrastructure problem it solves |
| Architecture diagram | SHOULD | System architecture, component interaction |
| Features | MUST | Infrastructure capabilities |
| Getting Started | MUST | Quickest path to running |
| Install | MUST | Binary, Docker, Helm, source |
| Config | SHOULD | YAML/HCL configuration examples |
| Docs | MUST | Link to comprehensive docs |
| Governance | COULD | Project governance model |
| Contributing | MUST | |
| Security | SHOULD | Security policy, reporting |
| License | MUST | |

**Ideal length:** 80-300 lines
**Model:** Hub-and-spoke

---

### 10. Educational / Awesome

**Section ordering:**
Title, Badges, Description, TOC (mandatory), Content sections by topic, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title | MUST | |
| Badges | SHOULD | |
| Description | MUST | What the collection covers |
| TOC | MUST | Always required -- content is long |
| Content sections | MUST | The content IS the README |
| Contributing | MUST | Guidelines for adding content |
| License | MUST | |

**Ideal length:** 500-3000+ lines
**Model:** Content IS README -- no external docs, the README is the product

---

### 11. Browser Extension

**Section ordering:**
Title+Icon, Badges, Description, `<!-- screenshot:hero -->`, Install (per-browser store links), Supported Browsers, Features, Keyboard Shortcuts, Permissions/Privacy, Build from source, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Icon | MUST | Extension icon as logo |
| Badges | SHOULD | |
| Description | MUST | What the extension does |
| Screenshot | SHOULD | Extension in action in the browser |
| Install (per-browser) | MUST | Chrome Web Store, Firefox Add-ons, Edge Add-ons |
| Supported Browsers | SHOULD | Compatibility table |
| Features | MUST | Key features |
| Keyboard Shortcuts | COULD | If the extension uses shortcuts |
| Permissions/Privacy | SHOULD | What permissions are needed and why |
| Build from source | SHOULD | For developers |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 80-400 lines
**Model:** Moderate

---

### 12. API / Backend Service

**Section ordering:**
Title+Logo, Badges, Tagline, Quick Start code, Features, Architecture/Request flow, Install, Docs, Client Libraries/SDK table, API Reference, Deploy/Self-host, Config, Security, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | MUST | |
| Tagline | SHOULD | |
| Quick Start code | MUST | curl or SDK example showing a request |
| Features | MUST | API capabilities |
| Architecture/Request flow | SHOULD | Request lifecycle diagram |
| Install | MUST | |
| Docs | MUST | Link to API documentation |
| Client Libraries/SDK | SHOULD | Table of official SDKs by language |
| API Reference | MUST | Link to OpenAPI/Swagger docs |
| Deploy/Self-host | SHOULD | Docker, Kubernetes, cloud deploy |
| Config | SHOULD | Environment variables |
| Security | SHOULD | Auth, rate limiting |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 100-350 lines
**Model:** Code-first hub-and-spoke

---

### 13. Mobile App

**Section ordering:**
Title+Icon, Badges, Description, `<!-- screenshot:hero | description=Device screenshots -->`, Features, Download table (per-platform stores), Platform Compatibility, Docs, Translation/Localization, Build from source, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Icon | MUST | App icon as logo |
| Badges | SHOULD | |
| Description | MUST | What the app does |
| Device screenshots | MUST | App running on device frames |
| Features | MUST | End-user features |
| Download table | MUST | App Store, Google Play, F-Droid links |
| Platform Compatibility | SHOULD | iOS/Android versions, devices |
| Docs | SHOULD | Link to docs if available |
| Translation/Localization | COULD | Supported languages, how to contribute translations |
| Build from source | SHOULD | Per-platform build instructions |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 150-350 lines
**Model:** Visual + download-heavy

---

### 14. Documentation Site / SSG

**Section ordering:**
Title+Logo, Badges, Tagline, `<!-- screenshot:hero | description=Generated output -->`, Features, One-line scaffold, Docs, Showcase/"Trusted by", Deploy buttons, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | |
| Tagline | SHOULD | |
| Generated output screenshot | SHOULD | What the generated site looks like |
| Features | SHOULD | Key differentiators |
| One-line scaffold | MUST | npx/pip create command |
| Docs | MUST | Link to the docs site (which is itself a demo) |
| Showcase/"Trusted by" | COULD | Sites built with this tool |
| Deploy buttons | COULD | Vercel, Netlify, Cloudflare Pages one-click |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 60-200 lines
**Model:** Ultra-hub-and-spoke (the docs site IS the product demo)

---

### 15. Bot (Discord/Slack/Telegram)

**Section ordering:**
Title+Avatar, Tagline, Badges, Description, Features/Commands, Prerequisites (bot registration), Quick Start (register, token, config, run), Config (.env), Commands reference, Plugins/Cogs, Docker, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Avatar | MUST | Bot avatar as logo |
| Tagline | SHOULD | What the bot does in one line |
| Badges | SHOULD | |
| Description | MUST | What the bot does, which platform |
| Features/Commands | MUST | Key commands and capabilities |
| Prerequisites | MUST | Bot registration steps, required tokens |
| Quick Start | MUST | Register bot, get token, configure, run |
| Config (.env) | SHOULD | Token setup, environment variables |
| Commands reference | SHOULD | Full command list with descriptions |
| Plugins/Cogs | COULD | Extensibility system |
| Docker | COULD | Docker deployment |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 140-400 lines
**Model:** Setup-heavy (bot registration is the hard part)
