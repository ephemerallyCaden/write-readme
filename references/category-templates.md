# Category-Specific README Structure Templates

> 17 project types, 45+ repos analyzed. Each template defines section ordering, MUST/SHOULD/COULD priorities, above-the-fold content, ideal length, and unique sections.

> **Ordering override:** SKILL.md Phase 3b's Run-first rule wins over the orderings below. The run section is always the first H2; only the title, badges, description (≤2 sentences, plus an optional router line), hero image, nav row, and TOC come before it. What counts as the run section depends on the type: install + run command for most types, a scaffold command for Frameworks and Docs Sites, a download table or store badges for Desktop, Mobile, and Browser Extension, and a hosted URL or deploy button followed by self-host commands for Web Apps, APIs, and hosted Docs Sites, and the build-and-flash command for Hardware. Prerequisites go inside the run section as its first line. A research write-up may put Results before the run section. Educational / Awesome lists, personal config / dotfiles repos, and ARCHITECTURE.md are exempt.

> **Evidence-only sections (every type):** Limitations, Privacy, and Comparison are not listed per template. SKILL.md Phase 3b says when each appears and where it goes. Architecture rows below follow the Phase 3b cap: in standard mode, one Mermaid diagram, 2-4 sentences, and a link.

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
| **Educational / Awesome** | Content IS the README, navigation mandatory (TOC or anchor nav block), Back-to-top links |
| **Browser Extension** | Per-browser install links, Supported Browsers, Permissions/Privacy, Key bindings |
| **API / Backend Service** | Client Libraries/SDK table, Request flow diagram, API Reference link |
| **Mobile App** | Device screenshots, Store badges, Platform compatibility, Translation/Localization |
| **Documentation Site / SSG** | Generated output screenshot, Deploy buttons, Showcase/"Trusted by" |
| **Bot** | Bot registration steps, Commands reference, Token/config setup, Plugins/Cogs |
| **Personal config / dotfiles** | What this repo is (and isn't), Browse index, Apply step (only with an installer) |
| **Hardware / Embedded** | Bill of Materials table, Wiring/pin table, Safety callouts, PCB files |

---

## Ideal Length Summary

Standard-mode ranges. SKILL.md Phase 3f sets the minimal, early-stage, and detailed ranges, which win over this table. Add sections to reach the floor only when the codebase supplies their content.

| Category | Lines | Model |
|---|---|---|
| Web Application | 50-300 | Hub-and-spoke |
| CLI Tool | 60-500 (detailed: up to 1200) | README as docs |
| Library / Package | 40-400 | Hub-and-spoke to comprehensive |
| Framework | 60-300 | Hub-and-spoke |
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
| Personal config / dotfiles | 30-200 | Browse index |
| Hardware / Embedded | 100-400 | Setup-heavy, photo-heavy |

---

## Cross-Category Section Matrix

| Section | WebApp | CLI | Lib | Frame | Game | CV | ML | Desktop | DevOps | Edu | BrExt | API | Mobile | Docs | Bot | Dot | HW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Logo/Banner | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | COULD | MUST | MUST | MUST | MUST | MUST | COULD | COULD |
| Badges | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | SHOULD | COULD | COULD |
| Screenshot/Demo | MUST | MUST(GIF) | -- | COULD | MUST | MUST | COULD | MUST | -- | -- | SHOULD | -- | MUST | SHOULD | -- | COULD | SHOULD |
| Description | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST |
| Features | MUST | SHOULD | SHOULD | SHOULD | SHOULD | MUST | SHOULD | MUST | MUST | -- | MUST | MUST | MUST | SHOULD | MUST | -- | SHOULD |
| Code Example | -- | SHOULD | MUST | SHOULD | -- | SHOULD | SHOULD | -- | COULD | -- | -- | MUST | -- | -- | -- | -- | -- |
| Install | MUST | MUST | MUST | MUST | SHOULD | MUST | MUST | MUST | MUST | -- | MUST | MUST | MUST | MUST | MUST | COULD | MUST |
| Quick Start | MUST | MUST | MUST | MUST | -- | MUST | MUST | -- | MUST | -- | -- | MUST | -- | MUST | MUST | -- | SHOULD |
| Docs link | MUST | COULD | MUST | MUST | SHOULD | MUST | MUST | SHOULD | MUST | -- | COULD | MUST | SHOULD | MUST | SHOULD | -- | COULD |
| TOC | COULD | MUST* | COULD | COULD | COULD | COULD | COULD | COULD | COULD | MUST | COULD | COULD | COULD | -- | COULD | COULD | COULD |
| Contributing | MUST | SHOULD | SHOULD | MUST | SHOULD | SHOULD | SHOULD | MUST | MUST | MUST | SHOULD | MUST | MUST | MUST | SHOULD | -- | SHOULD |
| License | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST | MUST |

*MUST if over 150 lines. Dot = Personal config / dotfiles, HW = Hardware / Embedded. Dotfiles Install means an Apply step, only when the repo ships an installer. The Hardware screenshot is a device photo, which can't be auto-captured.

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

**Ideal length:** 50-300 lines
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
| TOC | MUST* | *Required if >150 lines |
| Install (multi-platform) | MUST | Homebrew, apt, cargo, pip, npm, binary |
| Quick Start | MUST | One command that shows value |
| Usage Examples | SHOULD | Progressive: basic, intermediate, piped |
| Command Reference | SHOULD | Flags table or link to man page |
| Config | SHOULD | Config file location and options |
| Shell Integration | COULD | Completions, aliases, shell hooks |
| FAQ | COULD | Common issues |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 60-500 lines (detailed: up to 1200)
**Model:** README as docs (CLI tools often have no docs site)

---

### 3. Library / Package

**Section ordering:**
Title+Logo, Badges, Description, Code Example (before install, inside the first H2), Features, Install, Quick Start, Usage (progressive), API/Docs link, Benchmarks, Sponsors, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | Version, downloads, CI, license (0-6, only with real data) |
| Description | MUST | Category-value format |
| Code Example | MUST | 10 lines or fewer; may precede the install line inside the first H2 to show what using this looks like |
| Features | SHOULD | Plain bullets, feature name first; a concrete number or named spec in each (no bold labels, rule 12) |
| Install | MUST | Package manager command |
| Quick Start | MUST | Minimal working example |
| Usage (progressive) | SHOULD | Basic, realistic, advanced |
| API/Docs link | MUST | Link to generated API docs |
| Benchmarks | COULD | If performance is a selling point |
| Sponsors | COULD | |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 40-400 lines
**Model:** Hub-and-spoke (with docs site) or comprehensive (without)

---

### 4. Framework

**Section ordering:**
Title+Logo, Badges, Tagline, Description, Features/Why, Quick Start (scaffold command), Install, Docs, Ecosystem/Plugins, Migration, Community, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Logo | MUST | |
| Badges | SHOULD | 0-6, only with real data |
| Tagline | SHOULD | Punchy one-liner |
| Description | MUST | What it does, philosophy |
| Features/Why | SHOULD | What it does differently, stated as facts about this framework. Comparisons with named alternatives follow the Comparison rule (SKILL.md Phase 3b) |
| Quick Start | MUST | Scaffold command that gets a project running |
| Install | MUST | |
| Docs | MUST | Link to comprehensive docs |
| Ecosystem/Plugins | SHOULD | Available integrations |
| Migration | COULD | From previous versions (CHANGELOG or docs/), or from another framework only when docs/ has that guide |
| Community | SHOULD | |
| Contributing | MUST | |
| License | MUST | |

**Ideal length:** 60-300 lines
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
Title, Badges, Description, TOC or anchor nav block (mandatory), Content sections by topic, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title | MUST | |
| Badges | SHOULD | |
| Description | MUST | What the collection covers |
| TOC | MUST | Always required -- content is long. A nav block of anchor links grouped by intent ("Build with agents") can replace a flat TOC |
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
| Badges | SHOULD | 0-6, only with real data |
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
Title+Avatar, Tagline, Badges, Description, Features/Commands, Quick Start (bot registration as the prerequisite, then token, config, run), Config (.env), Commands reference, Plugins/Cogs, Docker, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title+Avatar | MUST | Bot avatar as logo |
| Tagline | SHOULD | What the bot does in one line |
| Badges | SHOULD | |
| Description | MUST | What the bot does, which platform |
| Features/Commands | MUST | Key commands and capabilities |
| Prerequisites | MUST | Bot registration steps, required tokens. First part of Quick Start, not a separate section |
| Quick Start | MUST | Register bot, get token, configure, run |
| Config (.env) | SHOULD | Token setup, environment variables |
| Commands reference | SHOULD | Full command list with descriptions |
| Plugins/Cogs | COULD | Extensibility system |
| Docker | COULD | Docker deployment |
| Contributing | SHOULD | |
| License | MUST | |

**Ideal length:** 140-400 lines
**Model:** Setup-heavy (bot registration is the hard part)

---

### 16. Personal config / dotfiles

**Section ordering:**
Title, Description, What this repo is (and isn't), Browse index, `<!-- screenshot:hero | description=Desktop or editor with this config applied | priority=COULD -->`, Apply (only with an installer), Credits, License

Run-first exempt: the README is a browse index, and most readers copy one file rather than install the repo.

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title | MUST | |
| Description | MUST | Whose setup, for which OS, shell, editor, or Home Assistant version (from `.HA_VERSION`, `Brewfile`, package lists) |
| What this repo is (and isn't) | MUST | Two or three lines: what it configures, and that it is a personal setup to read and copy from, not a framework to install. Name what it doesn't cover only when the repo shows it (no Linux paths, no Windows terminal config) |
| Browse index | MUST | Table: path, then what it configures. One row per top-level config directory or file; group by tool, not by file type |
| Screenshot | COULD | A found image, else a placeholder per SKILL.md Phase 3d |
| Apply | COULD | Only when the repo ships `install.sh`, a Makefile target, or a stow, chezmoi, or dotbot config. Quote its real command and say what it overwrites or symlinks |
| Credits | COULD | Configs it borrows from, only when files or comments name them |
| License | MUST | One line |

**Ideal length:** 30-200 lines
**Model:** Browse index. Home Assistant configs often add an automations index (automation file, then what it does).

---

### 17. Hardware / Embedded

**Section ordering:**
Title, Badges, Description, `<!-- screenshot:hero | description=Photo of the assembled device | priority=SHOULD -->`, Getting Started (build and flash), Bill of Materials, Wiring, Assembly, Firmware config, PCB, Contributing, License

**Section priorities:**

| Section | Priority | Notes |
|---|---|---|
| Title | MUST | |
| Badges | COULD | 0-6. Usually none: there is rarely a registry or CI |
| Description | MUST | What the device does, the board or MCU (`board =` in `platformio.ini`, the FQBN in `sketch.yaml`) |
| Device photo | SHOULD | A photo can't be auto-captured; use a found image or a placeholder |
| Getting Started | MUST | First line: "Requires the parts in [Bill of Materials](#bill-of-materials) and PlatformIO." Then build and flash (`pio run -t upload`, `arduino-cli compile` + `upload`). End with the serial baud rate and first log line from the setup code. Board-only repos point to the fab outputs instead |
| Bill of Materials | MUST when `BOM.csv` or a KiCad BOM export exists | Table built from the file's own columns (reference, quantity, part, value or footprint, link). Never add prices, suppliers, or links the file doesn't have |
| Wiring | SHOULD | Pin table from the pin definitions in code (`#define LED_PIN 4`, `const int`, `-D` build flags), plus the schematic image or KiCad export if found |
| Safety callouts | MUST when evidenced | `> [!WARNING]` directly above the step where the hazard arises, naming it: mains voltage (relay or AC modules in the BOM), lithium cells and charging (LiPo, 18650, charger ICs), reversed VCC/GND on unprotected boards, motor and heater current limits, logic levels (5 V parts on a 3.3 V MCU). Only hazards the BOM, schematic, or code shows; never a generic "be careful" line |
| Assembly | COULD | Only from build notes or photos in the repo |
| Firmware config | SHOULD | Build flags, `config.h` keys, Wi-Fi or secrets files the code reads |
| PCB | SHOULD when KiCad files exist | KiCad source paths, fab outputs (gerbers, drill, placement), and the KiCad version from the project file |
| Contributing | SHOULD | |
| License | MUST | Hardware and firmware may carry different licenses (CERN-OHL, MIT); read every LICENSE file |

**Ideal length:** 100-400 lines
**Model:** Setup-heavy (parts, wiring, flashing), photo-heavy

---

### Modifier: Research write-up

Applies on top of the detected type's template (usually ML, Visual Output, or Other) when SKILL.md Phase 1g flags the Academic research write-up subtype.

| Section | Priority | Notes |
|---|---|---|
| Results | MUST | May precede the run section. The key figure and a metrics table, each number taken from a results file, notebook output, or the paper |
| Paper / report link | MUST | Link the PDF or `.tex` source in the repo |
| Run section | MUST | One runnable command that reproduces a result, even when the write-up is the point |
| Citation/BibTeX | SHOULD | Only from `CITATION.cff` or a `.bib` entry |
| Dataset | SHOULD | Where the data comes from and its license, from the code or the paper |
