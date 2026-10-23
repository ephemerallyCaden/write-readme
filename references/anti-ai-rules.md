# Anti-AI Writing Rules -- Complete Reference

> This document contains the full catalog of anti-AI writing rules for README generation. The SKILL.md has rules inline; this file provides the complete detail for anyone who needs the exhaustive list.

---

## Tier 1A -- Banned Words (Strongest AI Signals)

These words are the strongest indicators of AI-generated text. Never use them in generated README prose.

| Banned Word | Replacements | README Context |
|---|---|---|
| delve | look at, explore, examine | "Explore the API" not "Delve into the API" |
| robust | reliable, solid | "A reliable HTTP client" not "A robust HTTP client" |
| comprehensive | full, complete, thorough | "Full test coverage" not "Comprehensive test coverage" |
| leverage | use | "Use GPU acceleration" not "Leverage GPU acceleration" |
| seamless | smooth, easy | "Easy migration from v2" not "Seamless migration from v2" |
| cutting-edge | latest, newest | "Uses the latest MediaPipe models" not "Uses cutting-edge AI" |
| empower | let, enable, allow | "Lets developers build..." not "Empowers developers to build..." |
| streamline | simplify, speed up | "Simplifies deployment" not "Streamlines deployment" |
| harness | use | "Use the power of..." becomes just "Use..." |
| elevate | improve | Or describe the specific improvement |
| embark | start, begin, get started | "Get started" not "Embark on your journey" |
| pivotal | important, key | "An important tool for..." or skip the adjective entirely |
| meticulous | careful, precise | "Carefully designed" or describe the design decisions |
| showcase | show, demonstrate | "Showing the latest features" not "Showcasing" |
| beacon | (cut -- describe what is notable instead) | Never needed in a README |
| tapestry | (cut) | Never needed in a README |
| landscape | field, space, area | "In the AI field" not "In the AI landscape" |
| deep dive | look at, exploration | "A look at the internals" not "A deep dive" |
| unpack | explain, break down | "Here is how it works" not "Let us unpack this" |
| holistic | complete, full, overall | "A complete approach" not "A holistic approach" |
| actionable | practical, useful | "Practical insights" not "Actionable insights" |
| best practices | what works, standard approach, conventions | "What works" not "Following best practices" |

---

## Tier 1B -- Clarity Edits (Moderate AI Signals)

These words are less flagrant than Tier 1A but still smell of AI when used in README descriptions. Replace them.

| Word / Phrase | Replacements | Notes |
|---|---|---|
| utilize | use | Always replace. No exceptions. |
| facilitate | enable, help, allow | Always replace. |
| foster | build, support, encourage | "Build a community" not "Foster a community" |
| ecosystem (in prose) | system, community, network | Acceptable as a section heading for plugin directories. Ban in descriptive prose. |
| in order to | to | Always shorten. |
| serves as | is | "This is the config file" not "This serves as the config file" |
| it's worth noting | (cut -- just state the fact) | Always cut. The fact speaks for itself. |
| game-changer | (cut or describe the actual change) | Never needed. |
| paradigm | model, approach, pattern | Use concrete terms. |
| realm | area, field, domain | Plain language. |
| testament to | (cut) | Overblown. Describe the evidence directly. |
| ever-evolving | changing | Or just describe what changed. |

---

## The 11 Structural Rules

1. **No emoji in headings.** `## Features` is correct. `## [star] Features` looks AI-generated. The only acceptable emoji is one tied to a project's proper noun brand or mascot -- never decorative emoji on generic section names.

2. **No throat-clearing.** Never open a section by explaining what it covers. The heading does that. Jump straight to content.

3. **No transition phrases between sections.** Sections in a README are self-contained. Do not bridge them with "Moreover", "Furthermore", "Additionally", "Moving on to..." Headings handle transitions.

4. **No "Let's" anything.** Not "Let's get started", not "Let's explore", not "Let's dive in." Use imperative: "Install", "Configure", "Run."

5. **One term, used consistently.** Do not cycle between "the tool", "the framework", "the application", "the solution." Pick one and stick with it.

6. **Code blocks before prose.** A code example says more than three paragraphs of description. Show the code, then explain if needed.

7. **No empty praise.** "A Python linter written in Rust" beats "An amazing, groundbreaking Python linter that will revolutionize your workflow." The description must be factual.

8. **Earned emphasis only.** Bold a keyword only when it helps scanning. Do not bold for drama. Never bold entire sentences.

9. **Sentence variety.** Vary sentence length. Mix short declaratives with longer explanations. Do not fall into a rhythm of uniform 3-sentence paragraphs.

10. **No "In today's world of..." -- ever.** No temporal scene-setting. No "In the era of..." No "As the landscape of X evolves..."

11. **End sections on concrete points, not summaries.** Do not end with "Overall, this tool provides a powerful solution." End with the last useful piece of information.

---

## The Portability Test

> If a sentence could move unchanged to another project's README and still make sense, it is filler. Cut it or replace it with a fact specific to this project.

### Sentences that FAIL the portability test

- "A powerful tool for modern developers"
- "Easy to get started"
- "Built with performance in mind"
- "Designed for scalability"
- "Community-driven and open source"

### Sentences that PASS the portability test

- "Compiles 100K lines of Python in under 200ms"
- "Drop-in replacement for pip with 10-100x faster installs"
- "Mirror your Android screen on your computer at 30-120fps"
- "Manage your zsh configuration with 300+ plugins"

Every prose sentence in a generated README must pass this test. If it could appear in any project's README unchanged, replace it with a specific fact about the actual project.

---

## Voice Register Guidelines

### Context: READMEs are `docs`

READMEs operate in a `docs` register, not `blog` or `linkedin`. This relaxes some general anti-AI rules:

**Safe to use freely (docs profile skips these checks):**
- Bullet lists (lists are docs)
- Fragment lists (fragment lists are docs convention)
- Short paragraphs
- Frequent headings in short text
- Passive voice in feature descriptions ("Designed for...", "Built with...")

**Use with care (docs profile relaxes these):**
- Em dashes (0-2 per README, not as a rhythm crutch)
- Bold keywords (each bold bullet must contain a verb and a specific claim)
- Hedging with "may" (acceptable for genuine technical uncertainty)

**Always strict (docs profile keeps these):**
- P0 credibility killers (chatbot artifacts, cutoff disclaimers)
- Promotional language
- Rhetorical questions

### Pronouns by section type

| Section | Voice | Example |
|---|---|---|
| Description | Third person | "Flask is a lightweight framework" |
| Instructions | Imperative | "Install with pip" (not "You can install with pip") |
| Contributing | First person plural | "We welcome contributions" |

### Tone: Quietly confident

- Present tense, active voice: "React renders UI components" not "React can be used to render UI components"
- Declarative without superlatives (unless backed by benchmarks)
- No hedging on features that work: "Supports hot reload" not "Aims to support hot reload"
- No performed candor, no manufactured stakes, no fake enthusiasm
- Prefer plain copulatives ("X is Y") over inflated substitutes ("serves as", "stands as a testament to")

### Superlatives

Superlatives are acceptable ONLY when backed by evidence present in the codebase:
- "An extremely fast Python linter" works because Ruff publishes benchmarks
- Use specific numbers over vague claims: "10-100x faster than pip" beats "blazingly fast"
- Never use the Tier 1A banned words as superlatives

---

## Anti-AI Quality Checklist

### P0 -- Credibility Killers (must fix before any review)

- [ ] No chatbot artifacts ("Feel free to...", "I hope this helps", "Great question")
- [ ] No cutoff disclaimers ("As of my last update")
- [ ] No vague attributions ("Experts believe", "Studies show")
- [ ] No significance inflation on routine features
- [ ] No reasoning chain artifacts ("Let me break this down", "Step 1:" in prose)

### P1 -- AI Smell (fix before publishing)

- [ ] No emoji in section headings (only acceptable next to a proper noun brand/mascot)
- [ ] No Tier 1A words (delve, robust, comprehensive, leverage, seamless, cutting-edge, empower, streamline, harness, elevate, embark, pivotal, meticulous, showcase, beacon, tapestry, landscape, deep dive, unpack, holistic, actionable, best practices)
- [ ] No template phrases ("a [adjective] step towards [adjective] [noun]")
- [ ] No "Let's" transition openers
- [ ] No synonym cycling within the same section
- [ ] No formulaic openings ("In the rapidly evolving world of...")
- [ ] No hedge-stacked predictions ("could potentially", "may eventually")
- [ ] No "Whether you're X or Y" false-breadth
- [ ] No performed candor ("Let's be honest", "real talk")
- [ ] No narrated candor ("In the interest of transparency")

### P2 -- Polish

- [ ] Em dashes used sparingly (0-2 per README, not as a rhythm crutch)
- [ ] No transition phrases (Moreover, Furthermore, Additionally)
- [ ] No compulsive rule of three
- [ ] No uniform paragraph lengths
- [ ] Sentence length varies naturally
- [ ] No generic conclusions ("The future looks bright")
- [ ] Every sentence passes the portability test

### README-Specific Checks

- [ ] No section preambles explaining what the section covers
- [ ] No overexplaining commands (show the command, then explain if needed)
- [ ] Description is specific to THIS project, not generic
- [ ] Feature claims are backed by evidence from the codebase
- [ ] No fake enthusiasm ("We're excited to...", "We're thrilled to...")
- [ ] Badge count is reasonable (3-6)
- [ ] Code examples use real exports/functions from the project
