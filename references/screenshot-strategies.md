# Screenshot Strategies Reference

> Complete reference for what to capture, how to capture it, and what to avoid for each project type. Backs up the screenshot placeholders embedded in README templates.

A capture that runs the project's own code (a dev server, the CLI, a game) runs only after the user confirms that exact command: see Project commands in `skills/screenshot/SKILL.md`.

---

## Money Shot Matrix

The "money shot" is the single most important screenshot for a project's README. If you can only include one image, this is it.

| Project Type | Money Shot | Why |
|---|---|---|
| Web Application | Main dashboard with populated sample data, dark mode | Shows what users will see daily |
| CLI Tool | Animated GIF of the core command (5-8s) | Motion demonstrates the tool's value faster than words |
| TUI Application | Full-screen TUI with all panels visible and populated | Proves the TUI is polished, not a toy |
| Desktop Application | Main window with content loaded | Shows the app looks native and professional |
| Game / Interactive | Gameplay mid-action (not title screen, not pause menu) | This is the back of the box -- one frame that says "this is what playing feels like" |
| Visual Output / CV | The visual result the project produces (annotated frame, generated image) | The output IS the product |
| Generative AI | Generated output at full quality | Shows what the model can create |
| Data Visualization | Populated chart/dashboard with real or realistic data | The visualization IS the output |
| ML/AI Model | Architecture diagram or model results table | Most ML output is not visual |
| Browser Extension | Extension active in the browser toolbar/page | Shows where it lives and what it does |
| Mobile App | Device screenshot with app running | Shows the app on a real device frame |
| Documentation Site / SSG | Generated documentation site in the browser | The docs site IS the product demo |
| Bot | Bot responding in a chat interface | Shows it working in context |
| API / Backend Service | Architecture/request flow diagram | APIs have no visual UI |
| Library / Package | Code example (not a screenshot) | Code examples beat screenshots for libraries |
| DevOps / Infrastructure | Architecture diagram | Infrastructure has no visual UI |
| Educational / Awesome | No screenshot needed | Content IS the README |
| Other / Unknown | LLM infers the most visually valuable aspect | See inference heuristics below |

---

## Shot Plans by Project Type

### Web Application

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Hero: Main dashboard | MUST | Home/dashboard view with sample data, dark mode preferred | Start dev server, navigate to `/`, wait for `networkidle`, screenshot |
| Feature 1: Key differentiator | SHOULD | The feature that makes this app unique (workflow editor, monitoring view, API explorer) | Navigate to feature route, screenshot |
| Feature 2: Secondary view | COULD | Settings, analytics, or other important view | Navigate, screenshot |
| Architecture diagram | SHOULD | System architecture as Mermaid | Generate from codebase analysis, render to SVG/PNG |
| Light/dark variants | COULD | Hero in both modes (for `<picture>` element) | Toggle theme, re-screenshot |

**Rules:**
- Viewport: 1280x800 (standard laptop)
- Wait for `networkidle` state before capturing
- If the app has a login, check for demo/seed data scripts first
- Never screenshot a login page or empty state as the hero
- If the app is API-only (no UI), skip screenshots entirely

### CLI Tool

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Hero: Core command GIF (5-8s) | MUST | Type the primary command, results appear colorized | VHS tape file or Playwright HTML terminal render |
| Help output | SHOULD | `--help` output, cleanly formatted | Run `--help`, capture, style as terminal image |
| Feature comparison | COULD | Side-by-side with the tool it replaces | Run both tools, capture both outputs, compose side-by-side |
| Advanced usage | COULD | Complex invocation showing piping, filtering, or config | VHS or Playwright terminal |

**Rules:**
- Dark terminal background (Dracula, One Dark, or similar)
- Colorized output mandatory
- GIF preferred over static screenshot
- Font: monospace, 16-18pt
- Width: 800px
- If VHS unavailable: use Playwright to render a styled HTML terminal

**Command selection strategy (in priority order):**
1. Check existing README for usage examples -- use the first example
2. Parse `--help` to identify the primary subcommand/verb
3. Run against the project's own codebase when possible
4. Generate sample input if needed
5. Truncate output for the screenshot (ideal: 8-15 lines)

### TUI Application

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Hero: Full TUI | MUST | All panels visible, populated with data | Launch in terminal, VHS or screen capture |
| Feature panels | COULD | Individual panel close-ups | Element-specific captures |

### Desktop Application

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Hero: Main window | MUST | Full window with content loaded | macOS: `screencapture -l <windowID>` |
| Feature view | COULD | Secondary feature window | Same approach |

**Note:** Desktop app screenshots are hardest to automate. If the app cannot be launched headlessly, provide manual capture instructions with specific guidelines (viewport size, content to show, theme).

### Game / Interactive

| Shot | Priority | What to Capture | Why | How |
|---|---|---|---|---|
| Hero: Gameplay in action | MUST | Core gameplay loop mid-action -- characters moving, world visible, HUD active | One frame that says "this is what playing feels like" | See capture strategies below |
| Gameplay GIF/video (5-15s) | MUST | Continuous gameplay sequence showing movement, interaction, signature mechanic | Static screenshots undersell games. Motion IS the product. | See capture strategies below |
| Title screen / main menu | SHOULD | Branded title screen | Shows polish level and art direction | Capture on launch before gameplay |
| Environment variety (2-3 shots) | SHOULD | Different biomes, levels, game states, or modes | Proves there is more than one screen | Capture at different game stages |
| UI/HUD detail | COULD | In-game interface -- health bars, inventory, minimap, build menu | For strategy, RPG, city builder, management sim | Crop from gameplay captures |

**Sub-type rules:**

*Action / Platformer / Shooter:*
- Hero frame MUST show the player character mid-action with at least one enemy/obstacle visible
- GIF should show a tight 3-5s sequence of the core loop
- Environment variety matters most

*Strategy / Management / Simulation:*
- Hero frame MUST show a populated game state -- city built, army positioned, factory running
- The more on screen, the better. Zoom out to show complexity.
- UI/HUD is a feature -- show the interface elements

*Puzzle / Card / Board:*
- Hero frame MUST show a puzzle in mid-solve, not an empty or completed board
- GIF showing a satisfying solve/combo/chain reaction is the best asset

*Roguelike / RPG:*
- Hero frame: character in dungeon/world with visible stats
- Show item/loot variety if it is a selling point

*Sandbox / Creative:*
- Hero frame: an impressive player-created build, not an empty world
- Requires human effort -- the tool cannot make a creative build for you

**Capture strategies:**

*Browser games (Phaser, Three.js, PixiJS):*
- Start dev server, use Playwright
- Skip intro via JS: `page.evaluate('game.scene.start("Level1")')`
- Check for URL params: `?level=3`, `?demo=true`, `?skip-intro`
- Use `page.keyboard` and `page.mouse` to simulate basic input
- Capture canvas element directly: `page.locator('canvas').screenshot()`
- Burst screenshots during simulated input, compose into GIF

*Native games (Godot, Pygame, Unity, Bevy):*
- Check for `--screenshot` flag, demo mode, or headless render
- If not possible: provide detailed manual capture instructions

### Visual Output / CV

| Shot | Priority | What to Capture | Why | How |
|---|---|---|---|---|
| Hero: The output in action | MUST | Visual result -- annotated frame, generated image, transformed output | This single image explains the entire project | Run project against sample input, capture output |
| Demo GIF/video (3-8s) | MUST (real-time) | Tool processing in real-time -- input changing, output tracking | Proves it works in real-time, not just on cherry-picked frames | ffmpeg/VHS or Playwright record if web-based |
| Pipeline architecture | SHOULD | Processing pipeline as a diagram | Shows technical depth | Mermaid diagram from code analysis |
| Input vs Output comparison | SHOULD | Side-by-side before/after | Makes the transformation concrete | Compose with Pillow/ImageMagick |
| Output gallery / grid | COULD | Multiple results in a grid | Shows breadth and scope | Compose grid with Pillow/matplotlib |
| Failure case / edge handling | COULD | How the tool handles challenging input | Builds trust about limitations | Run against challenging sample |

**Sub-type rules:**

*Computer Vision / Pose Estimation / Detection:*
- Hero MUST show landmarks/bounding boxes overlaid on the input
- Use a clean, well-lit sample input
- GIF showing tracking across motion is more compelling than a static frame

*Image Generation / Style Transfer:*
- Hero MUST show the generated/transformed output at full quality
- Before/after comparison is the strongest format
- For style transfer: show original, style reference, and result together

*Data Visualization:*
- Hero MUST show a populated visualization with real or realistic data
- Dark theme for developer-facing tools, light for business-facing
- Include axis labels, legends, titles

### ML/AI Model (non-visual output)

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Architecture diagram | MUST | Model/pipeline architecture as Mermaid | Generate from code analysis, render |
| UI screenshot (if UI exists) | SHOULD | Interface showing completed result | Start UI server, navigate, screenshot |
| Performance chart | COULD | Benchmark results as chart | matplotlib to PNG |
| Terminal output | COULD | Inference example showing input to output | Styled HTML terminal via Playwright |

### Bot

No standard screenshot plan. If possible, capture the bot responding in a real chat interface.

### API / Backend Service

No standard screenshot plan. Architecture/request flow diagrams are the primary visual.

### Library / Package

Libraries generally do not need screenshots. Code examples in the README are better. An architecture diagram (COULD priority) is the only visual that might help.

### Documentation Site / SSG

| Shot | Priority | What to Capture | How |
|---|---|---|---|
| Generated output | SHOULD | The generated docs site in a browser | Start server, Playwright screenshot |
| Deploy buttons | COULD | One-click deploy experience | N/A -- badges, not screenshots |

### Educational / Awesome

No screenshots needed. Content IS the README.

### DevOps / Infrastructure

No standard screenshot plan. Architecture diagrams are the primary visual.

---

## Screenshot Anti-Patterns

| Anti-Pattern | Why It Fails | What to Do Instead |
|---|---|---|
| Title screen as hero (games) | Tells the viewer nothing about gameplay | Capture gameplay mid-action |
| Login page as hero (web apps) | Every app has a login page | Capture the dashboard with data |
| Empty state as hero | Shows nothing of value | Seed sample data before capture |
| Terminal with no output | Proves nothing | Run a real command, show real output |
| Blurry or low-resolution screenshots | Looks unprofessional | Use `device_scale_factor: 2` for retina |
| Screenshots of code (for libraries) | Code blocks in markdown are better | Use fenced code blocks instead |
| White background screenshots on light GitHub theme | Image boundary is invisible | Use dark mode or add a subtle border |
| Extremely wide screenshots | Unreadable at README width | Cap viewport at 1280px |
| Screenshots with personal data visible | Privacy concern | Use demo/seed data |
| GIFs longer than 15 seconds | Too large, viewer loses interest | Keep to 5-10 seconds max |

---

## Dimensions and Format Recommendations

### Viewport sizes

| Context | Width | Height | Notes |
|---|---|---|---|
| Web app screenshot | 1280px | 800px | Standard laptop viewport |
| CLI terminal capture | 800px | varies | Width matters, height is content-dependent |
| Mobile device frame | 375px | 812px | iPhone-size for device screenshots |
| Game capture | 1280px | 720px | 16:9 aspect ratio |

### Retina scaling

Always capture at `device_scale_factor: 2` for crisp images on high-DPI displays. The actual image will be 2x the viewport dimensions but display at 1x with `width` attribute.

### File formats

| Format | Best For | Notes |
|---|---|---|
| PNG | Static screenshots | Lossless, good for UI with text |
| GIF | Short animations (5-15s) | Limited to 256 colors, large files |
| WebP | Static or animated | Better compression than PNG/GIF, but less GitHub support |
| SVG | Diagrams, architecture charts | Scalable, small file size |

### File size targets

| Type | Target | Maximum |
|---|---|---|
| Hero screenshot (PNG) | Under 200KB | 500KB |
| Animated GIF | Under 2MB | 5MB |
| Architecture diagram (SVG) | Under 50KB | 200KB |

---

## "Other/Unknown" LLM Inference Heuristics

When a project does not match any defined category, the tool uses LLM inference to determine what is visually valuable. The key principle: every shot must pass the portability test -- if the image could appear in another project's README and make equal sense, it is not specific enough.

### Inference process

1. Analyze the codebase for visual surface area
2. Ask: "What would a human showing off this project point a camera at?"
3. Score candidate shots by visual value
4. Generate a custom shot plan with reasoning

### Signal-to-screenshot mapping

| Signal Found in Codebase | What to Screenshot | Reasoning |
|---|---|---|
| Writes HTML/PDF/DOCX files | A rendered output document | The output IS the product |
| Has a `templates/` directory | A populated template output | Shows what users get |
| Produces audio/video | Waveform visualization or player screenshot | Make the output visible |
| Has API with Swagger/OpenAPI | The Swagger UI | Interactive docs are impressive |
| Runs a bot (Discord, Slack, Telegram) | The bot responding in a chat | Shows it working in context |
| Produces structured data (JSON, CSV, DB) | A table/visualization of the data | Make invisible output visible |
| Is a browser extension | The extension active in the browser | Show where it lives |
| Is a VS Code extension | The extension panel in VS Code | Hardest to auto-capture -- provide manual instructions |
| Is a GitHub Action | The action running in a workflow summary | Screenshot via Playwright at the GitHub URL |
| Is a Jupyter notebook / data pipeline | A rendered notebook with charts | Convert to HTML, Playwright screenshot |
| Is a documentation site generator | The generated docs site | Start server, Playwright screenshot |
| Processes email / messages | A formatted message output | Show the transformation |
| Nothing visual whatsoever | Architecture diagram only | Some projects genuinely do not need screenshots |

### Scoring criteria for candidate shots

| Criterion | Question to Ask |
|---|---|
| Explanatory power | Does this image explain what the project does faster than words? |
| Uniqueness | Does this show something specific to THIS project? (portability test) |
| Impressiveness | Would this make someone want to try the project? |
| Feasibility | Can we actually capture this automatically? |
