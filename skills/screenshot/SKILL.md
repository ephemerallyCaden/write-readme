---
name: screenshot
description: Capture screenshots, terminal recordings, and visual assets for READMEs. Use when asked to "take screenshots", "capture screenshots", "/screenshot", or when delegated from the write-readme skill. Supports web apps (Playwright), CLI tools (VHS/terminal render), games, visual output projects, and LLM-inferred capture for unknown types.
---

# Screenshot Sub-Skill

Captures visual assets for README files. Works as a standalone tool or as a delegate called by the write-readme skill during Phase 3d.

## Two Invocation Paths

### Path A: Delegated from write-readme (Phase 3d)

The write-readme skill detected no existing assets, the template requires visuals (MUST priority), and the user chose "Auto-capture." The write-readme skill passes:

- Detected project type (a slug from the canonical type slugs table in `../../SKILL.md`)
- Screenshot positions still uncovered (parsed `<!-- screenshot: -->` placeholders)
- Project root path
- Output directory: `<draft-dir>/assets/screenshots/`, where `<draft-dir>` is the literal per-run path write-readme created with `mktemp -d` (for example `/tmp/write-readme-draft.k3J9qL`). Use the path exactly as passed; never create another draft directory.

This skill handles everything from that point: what to capture, how, which tools, fallbacks. Nothing is written into the project on this path, because the user hasn't approved the README yet: every capture, `.tape` file, and intermediate image goes in the output directory, and no README is edited. Return each image's path under the output directory, or the failure reason. write-readme puts the references in its draft and copies the images into the project in its Phase 6, after approval. For screenshots, write-readme never calls the capture scripts directly.

### Path B: Direct user invocation

Trigger phrases: "/screenshot", "take screenshots", "capture screenshots", "generate visuals"

When invoked directly:

1. Read existing README for `<!-- screenshot: -->` placeholders
2. If placeholders found, use them as the shot plan
3. If no placeholders, run project type detection and apply the type-specific strategy
4. Present the shot plan to the user for confirmation before capturing
5. Capture, validate, save to `assets/screenshots/` in the project (the user asked for files there)
6. Update README.md image references (replace placeholders if they exist)

`<out>` in the commands and code below is the output directory: `<draft-dir>/assets/screenshots` (the literal path passed in) on Path A, `assets/screenshots` on Path B.

---

## Phase 1: DETECT

### 1a. Detect project type

Path A passes the slug; use it. On Path B, get a first guess with `bash ../../scripts/detect-project-type.sh --dir <project-root>`, then confirm it by reading the code against the taxonomy table in `../../SKILL.md` Phase 1b, which is the only copy of the types and their priorities.

### 1b. Detect available tooling

Check: Playwright (primary engine, required for most strategies), VHS (terminal GIF), Freeze (code/terminal PNG), silicon (code PNG), ImageMagick (post-processing), ffmpeg (video/GIF), pngquant (PNG compression).

If Playwright is not installed: fall back to Mermaid diagrams in markdown, matplotlib architecture diagrams, and descriptive placeholders. Suggest `pip install playwright && playwright install chromium`.

### 1c. Scan existing visual assets

Search `assets/`, `images/`, `screenshots/`, `docs/images/`, `docs/screenshots/`, `docs/assets/`, `.github/`, `img/`, `media/`, `static/`, `public/` for `*.png`, `*.gif`, `*.svg`, `*.jpg`, `*.webp`. Also check the README for existing `![...]()` and `<img src>` image references. If existing assets already cover required positions, skip those captures. Path A skips this step: write-readme already searched (its Phase 1j) and passes only uncovered positions.

### 1d. Detect how to start the project

For web apps, find the dev server command:
- `package.json` scripts: dev, start, serve
- Makefile targets: run, dev, serve
- Python: `manage.py runserver`, `flask run`, `uvicorn`
- Docker: `docker-compose.yml`

For CLI tools, find the entry point:
- `bin` field in package.json
- `console_scripts` in pyproject.toml/setup.py
- `__main__.py` or `if __name__ == "__main__"` patterns

---

## Phase 2: PLAN

Based on project type, build a shot plan. Present the plan to the user for confirmation before capturing.

### Web Application

1. **Hero: Main dashboard** (MUST) -- Start dev server, navigate to `/`, wait for `networkidle`, capture at 1280x800 viewport. Dark mode preferred. Never capture a login page or empty state.
2. **Key feature page** (SHOULD) -- Navigate to the route that shows the app's differentiator (workflow editor, monitoring view, API explorer). Detect routes from pages/ directory or route definitions.
3. **Secondary view** (COULD) -- Settings, analytics, or another important view.
4. **Architecture diagram** (SHOULD) -- Mermaid diagram generated from codebase analysis, rendered to PNG.
5. **Light/dark variants** (COULD) -- Hero in both color schemes for `<picture>` element.

Rules: viewport 1280x800, wait for `networkidle` + 2s settle time, `device_scale_factor: 2` for retina quality, check for seed/demo data scripts before capturing, skip if app is API-only with no UI.

### CLI Tool

1. **Hero: Core command GIF** (MUST) -- The primary command showing input-to-output cycle, under 8 seconds. Use VHS tape file if available, otherwise Playwright HTML terminal fallback.
2. **Help output** (SHOULD) -- `--help` output, syntax highlighted. Capture via Freeze, or render as styled HTML terminal.
3. **Feature comparison** (COULD) -- Side-by-side with the tool it replaces, showing speed or output quality difference.
4. **Advanced usage** (COULD) -- Complex invocation with piping, filtering, or configuration.

Command selection strategy (in order): check existing README usage examples, parse `--help` for the primary subcommand, run against the project's own codebase when possible, generate sample input if needed. Truncate output to 8-15 lines for readability.

Rules: dark terminal background (Dracula or similar), colorized output mandatory, GIF preferred over static, monospace font 16-18pt, width 800px.

### TUI Application

1. **Hero: Full TUI** (MUST) -- All panels visible, populated with data. Capture via VHS full-screen recording or Playwright HTML terminal render.
2. **Feature panels** (COULD) -- Individual panel close-ups cropped from the full capture.

### Desktop Application

1. **Hero: Main window** (MUST) -- Full window with content loaded. macOS: `screencapture -l <windowID>`.
2. **Feature view** (COULD) -- Secondary feature window.

When the app cannot be launched headlessly, provide manual capture instructions: launch at default window size, load realistic content, use OS capture (macOS: Cmd+Shift+4 then Space, Linux: gnome-screenshot -w, Windows: Alt+PrintScreen), save as `assets/screenshots/hero.png`, prefer dark mode.

### Game / Interactive

1. **Hero: Gameplay in action** (MUST) -- The core gameplay loop mid-action: characters moving, world visible, HUD active, something happening. NOT a title screen, NOT a pause menu, NOT an empty landscape.
2. **Gameplay GIF/video (5-15s)** (MUST) -- Continuous gameplay showing movement, interaction, the game's signature mechanic. Static screenshots undersell games more than any other project type.
3. **Title screen / main menu** (SHOULD) -- The branded splash screen. This is the one project type where a splash screen is a valid screenshot.
4. **Environment variety (2-3 shots)** (SHOULD) -- Different biomes, levels, game states, or modes. Proves scope beyond a single screen.
5. **UI/HUD detail** (COULD) -- Health bars, inventory, minimap, build menu. Include for strategy/RPG/management; skip for minimal-UI games.

Game sub-type rules:

- **Action / Platformer / Shooter:** Hero must show player mid-action with at least one enemy/obstacle. GIF shows a tight 3-5s core loop.
- **Strategy / Management / Simulation:** Hero must show a populated game state (city built, army positioned). Zoom out to show complexity. UI/HUD is a feature here.
- **Puzzle / Card / Board:** Hero must show a puzzle mid-solve, not empty or completed. GIF of a satisfying solve/combo is the best asset.
- **Roguelike / RPG:** Hero shows character in world with visible stats. Show item/loot variety and procedural generation if applicable.
- **Sandbox / Creative:** Hero needs an impressive player-created build. Suggest: "Capture a creative build that shows the tool's capabilities."

Capture strategies:

- **Browser games (Phaser, Three.js, PixiJS):** Start dev server, use Playwright. Execute JS to skip to gameplay (`page.evaluate('game.scene.start("Level1")')`), check for `?demo=true` URL params, simulate basic input via `page.keyboard` and `page.mouse`, capture canvas element directly with `page.locator('canvas').screenshot()`. For GIF: burst screenshots during simulated input, compose into GIF.
- **Native games (Godot, Pygame, Raylib, Bevy):** Check for `--screenshot` flag, demo mode, or headless render. Godot has `--headless` for some operations. Pygame can render to off-screen surface. Realistic fallback: provide manual capture instructions with specific guidelines for window size (1280x720), mid-action timing, and OS-specific capture keys.

### Visual Output / CV

1. **Hero: The output in action** (MUST) -- The visual result: annotated frame, generated image, rendered visualization. Must show a good result, not an edge case.
2. **Demo GIF/video (3-8s)** (MUST for real-time projects) -- Processing in real-time with input changing and output tracking/updating live. Proves it works in motion, not just on cherry-picked frames.
3. **Pipeline architecture** (SHOULD) -- Processing pipeline as a Mermaid diagram: input stages through to output.
4. **Input vs Output comparison** (SHOULD) -- Side-by-side: raw input on left, processed output on right. Shows the value the software adds.
5. **Output gallery / grid** (COULD) -- Multiple results in a grid showing different inputs and outputs, demonstrating breadth.

Sub-type rules:

- **Computer Vision / Pose Estimation / Detection:** Hero shows landmarks/bounding boxes overlaid on input. Use clean, well-lit sample input. GIF of tracking across motion is far more compelling than a static frame.
- **Image Generation / Style Transfer:** Hero shows generated/transformed output at full quality. Before/after comparison is the strongest format.
- **Data Visualization:** Hero shows a populated visualization with real or realistic data. Dark theme for developer-facing tools, light for business-facing.

Capture strategy: find sample input in test fixtures or example directories, find the entry point that produces visual output (grep for `imshow`, `imwrite`, `plt.savefig`), run with output capture, compose before/after comparison with Pillow.

### ML/AI Model (non-visual output)

1. **Architecture diagram** (MUST) -- Model/pipeline architecture as a Mermaid diagram, rendered to PNG.
2. **UI screenshot** (SHOULD, if UI exists) -- Interface showing a completed result. Start UI server, navigate, capture.
3. **Performance chart** (COULD) -- Benchmark results rendered via matplotlib.
4. **Terminal output** (COULD) -- Inference example showing input-to-output, rendered as styled HTML terminal.

### Mobile App

1. **Device screenshots** (MUST) -- Primary screen with realistic data loaded.

Capture strategy: manual instructions for most cases. Flutter projects can use `flutter screenshot` or integration test screenshots. React Native can use Detox screenshot utilities.

### Browser Extension

1. **Extension in browser** (MUST) -- The extension popup or panel active in the browser, showing its primary function.

Provide manual capture instructions: install in Chrome/Firefox, navigate to a page where the extension is useful, activate it, capture the browser window showing the extension popup + relevant page content, crop and save as `assets/screenshots/hero.png`.

### Bot

No screenshots typically needed. Suggest command output examples rendered as styled terminal images or embed chat message mockups. If the bot has a web dashboard, treat it as a web application capture.

### Documentation Site / SSG

1. **Hero: Generated output** (MUST) -- The rendered documentation site. Start the dev/build server, navigate to the landing page, capture with Playwright at 1280x800.
2. **Feature page** (COULD) -- An interior page showing search, sidebar navigation, or code highlighting.

### Other / Unknown

Use LLM inference to determine the most visually valuable aspects. Analyze the codebase for visual surface area, then score candidate shots.

Inference heuristics:

| Signal Found | What to Screenshot | Reasoning |
|---|---|---|
| Writes HTML/PDF/DOCX files | A rendered output document | The output IS the product |
| Has a `templates/` directory | A populated template output | Shows what users get |
| Produces audio/video | Waveform visualization or player screenshot | Show the output exists |
| Has an API with Swagger/OpenAPI spec | The Swagger UI | Interactive docs are impressive |
| Produces structured data (JSON, CSV, DB) | A table or visualization of the data | Make invisible output visible |
| Is a Jupyter notebook / data pipeline | A rendered notebook with charts | Convert to HTML, then Playwright |
| Is a GitHub Action | The action running in a workflow summary | Playwright at the GitHub URL |
| Processes email / messages | A formatted message output | Show the transformation |
| Nothing visual whatsoever | Architecture diagram only | Some projects genuinely do not need screenshots |

For each candidate, score by: explanatory power (does this image explain the project faster than words?), uniqueness (portability test -- would this image make sense in another project's README?), impressiveness (would this make someone try the project?), and feasibility (can we capture this automatically?).

Present the custom shot plan with reasoning before capturing.

---

## Phase 3: PREPARE

### 3a. Create output directory

```bash
mkdir -p <out>
```

### 3b. Start dev server (web apps)

Strategy in order:

1. `package.json` with dev/start/serve script: `npm run dev`
2. `docker-compose.yml`: `docker compose up -d`
3. Python framework: `python manage.py runserver` / `flask run` / `uvicorn main:app`
4. Makefile with run/dev/serve target: `make dev`

Wait for the server to respond (30-second timeout, polling every second).

### 3c. Seed sample data

Search for seed/demo/fixture scripts in package.json, Makefile, and Python files. Run the seed command if found. Never screenshot an empty state as the hero image.

### 3d. Detect routes (web apps)

Find available routes for multi-page capture: React/Next.js pages directory, Vue/Nuxt pages, Express/Flask/Django route definitions. Use these to identify the most important pages beyond the home page.

---

## Phase 4: CAPTURE

### 4a. Playwright web app capture

Reference script: `../../scripts/capture-web-app.py`

```python
from playwright.sync_api import sync_playwright
import os

OUT = "assets/screenshots"  # <out>; <draft-dir>/assets/screenshots on Path A
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        color_scheme="dark",
        device_scale_factor=2,  # Retina quality
    )
    page = ctx.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)  # Let animations settle
    page.screenshot(path=f"{OUT}/hero-dashboard.png", full_page=False)
    browser.close()
```

Key settings: `device_scale_factor: 2` for retina quality, `color_scheme: "dark"` forces dark mode via CSS media query, `wait_until: "networkidle"` ensures async data is loaded, `wait_for_timeout(2000)` lets transitions settle, `full_page: False` captures viewport only.

### 4b. VHS terminal recording

Reference script: `../../scripts/generate-tape.py`

When VHS is available, `python3 ../../scripts/generate-tape.py --command "mycommand --help" --output <out>/demo.gif` writes the `.tape` file and runs VHS (`--tape-only` writes the tape alone). The tape it writes looks like this:

```
Output <out>/demo.gif
Set FontSize 18
Set Width 900
Set Height 500
Set Theme "Dracula"
Set Padding 20
Set TypingSpeed 50ms

Type "mycommand --help"
Enter
Sleep 2s

Type "mycommand process input.txt"
Enter
Sleep 3s
```

Run a hand-written tape with `vhs <out>/demo.tape`.

### 4c. ANSI-to-HTML Playwright fallback (CLI tools without VHS)

Reference script: `../../scripts/capture-terminal.py`

Capture real command output, convert ANSI escape codes to styled HTML, then screenshot with Playwright:

```python
import subprocess, re, os
from playwright.sync_api import sync_playwright

ANSI_COLORS = {
    "31": "#ff5555", "32": "#50fa7b", "33": "#f1fa8c", "34": "#bd93f9",
    "35": "#ff79c6", "36": "#8be9fd", "37": "#f8f8f2", "0": None,
}

def ansi_to_html(text):
    def replace(m):
        c = m.group(1)
        return "</span>" if c == "0" else f'<span style="color:{ANSI_COLORS[c]}">' if c in ANSI_COLORS else ""
    return re.sub(r"\033\[(\d+)m", replace, text)

def capture_terminal(command, output_path):
    result = subprocess.run(command, capture_output=True, text=True)
    html = f'''<div style="background:#282a36; border-radius:12px; padding:20px;
      font-family:monospace; font-size:14px; color:#f8f8f2; width:860px;">
      <div style="margin-bottom:12px;"><span style="color:#ff5555">●</span>
      <span style="color:#f1fa8c">●</span> <span style="color:#50fa7b">●</span></div>
      <div><span style="color:#50fa7b">$</span> {" ".join(command)}</div>
      <pre style="white-space:pre-wrap">{ansi_to_html(result.stdout or result.stderr)}</pre></div>'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with sync_playwright() as p:
        page = p.chromium.launch(headless=True).new_page()
        page.set_content(html)
        page.locator("div").first.screenshot(path=output_path)
```

Alternatively, use `ansi2html` (`pip install ansi2html`) for more complete ANSI parsing with Dracula theme support.

### 4d. Mermaid diagram rendering

Reference script: `../../scripts/render-mermaid.py`

Two options:

**Option A: Inline Mermaid in README (zero files).** GitHub renders fenced `mermaid` code blocks natively. Preferred when no PNG file is needed.

**Option B: Render to PNG via Playwright.** Load HTML with the Mermaid JS CDN (`cdn.jsdelivr.net/npm/mermaid`), initialize with `theme: 'dark'`, place the diagram source in a `<div class="mermaid">`, wait for the SVG to render (`page.wait_for_selector(".mermaid svg")`), then screenshot the element with `page.locator(".mermaid").screenshot()`. See `../../scripts/render-mermaid.py` for the full implementation.

### 4e. Image composition (side-by-side, grid)

Reference script: `../../scripts/compose-images.py`

Use Pillow for before/after comparisons and grid layouts:

```python
from PIL import Image, ImageDraw

def compose_side_by_side(left_path, right_path, output_path,
                         left_label="Input", right_label="Output"):
    left, right = Image.open(left_path), Image.open(right_path)
    h = 400
    left = left.resize((int(left.width * h / left.height), h))
    right = right.resize((int(right.width * h / right.height), h))
    gap, label_h = 20, 40
    canvas = Image.new("RGB", (left.width + gap + right.width, h + label_h), "#0d1117")
    canvas.paste(left, (0, label_h))
    canvas.paste(right, (left.width + gap, label_h))
    draw = ImageDraw.Draw(canvas)
    draw.text((left.width // 2, 10), left_label, fill="#8b949e", anchor="mt")
    draw.text((left.width + gap + right.width // 2, 10), right_label, fill="#8b949e", anchor="mt")
    canvas.save(output_path)
```

For grids: resize all images to a uniform cell size, calculate row/column positions, paste onto a canvas. Same approach, varying the layout math.

---

## Phase 5: POST-PROCESS

### 5a. Optimize file sizes

Strip metadata with ImageMagick (`convert <file> -strip -quality 90 <file>`) and compress PNGs with pngquant (`pngquant --quality=65-90 --ext .png --force <file>`), in place under `<out>`.

### 5b. Generate light/dark variants

If both color schemes were captured, use the `<picture>` element with `<source media="(prefers-color-scheme: dark)">` and `<source media="(prefers-color-scheme: light)">` to serve the appropriate variant. Fall back to the dark variant in the `<img>` tag.

### 5c. Validate captures

Every captured image must pass before being used. Check: width >= 400px, pixel diversity > 10 unique colors (catches blank/error pages), file size between 1KB and 10MB. If validation fails, report the issue and do not include the image. A missing screenshot is better than a blank or broken one. Run `find <out> -maxdepth 1 \( -name '*.png' -o -name '*.gif' \) -exec python3 ../../scripts/validate-screenshots.py {} +`; the quoted patterns keep zsh from aborting when there are no GIFs.

---

## Phase 6: INTEGRATE

### Replace placeholders with image references

Path A: edit no README. Return the paths; write-readme places them in its draft using the rules below, with project paths (`assets/screenshots/hero.png`, not the `<draft-dir>` path).

Path B: parse `<!-- screenshot:{shot_id} | ... -->` placeholders in the README. For each placeholder with a matching captured image, replace with the appropriate markdown.

### Placement rules

1. **Hero screenshot** -- Immediately after description/badges, before installation
2. **Architecture diagram** -- After features, before detailed usage, or in a "How It Works" section
3. **Feature screenshots** -- In their respective feature sections, or in a collapsible "Screenshots" section
4. **CLI demo GIF** -- Immediately after description (GIFs are the hook for CLI tools)

### Markdown patterns

Hero image: `<p align="center"><img src="assets/screenshots/hero.png" alt="..." width="800"></p>`
CLI demo GIF: same pattern, `width="700"`, GIF format.
Feature gallery: wrap additional screenshots in `<details><summary>More Screenshots</summary>...</details>`.

### Alt text rules

Every image MUST have descriptive alt text. Describe what the screenshot shows, mention the project name, name the specific view or feature. Good: `"Uptime Kuma dashboard showing 12 monitored services with uptime percentages"`. Bad: `"screenshot"` or `""`.

---

## Money Shot Matrix

One table mapping each project type to its single most valuable screenshot.

| Project Type | The Money Shot | Why It Works |
|---|---|---|
| Web Application | Main dashboard, dark mode, populated with realistic sample data | Shows what users see on day 1. Populated data proves the tool is useful. |
| CLI Tool | Animated GIF of primary command, dark terminal, colorized output, full input-to-output cycle under 8 seconds | Motion captures attention. Full cycle communicates value instantly. |
| TUI Application | Full-screen TUI with all panels visible, populated with real data | Shows information density and layout. |
| Desktop Application | Full app window showing primary workflow with realistic content | Proves the app is polished and functional. |
| Game / Interactive | Gameplay mid-action: characters moving, world visible, HUD active | This is the back of the box. One frame that says "this is what playing feels like." |
| Visual Output / CV | The visual result the project produces: annotated frame, generated image, rendered visualization | This single image explains the entire project. Without it, the README is just words. |
| ML/AI Model | Architecture diagram showing the model/pipeline structure | Communicates technical sophistication when there is no visual output. |
| Mobile App | Device screenshot of the primary screen with realistic data | Shows the app in its natural context. |
| Browser Extension | Extension active in the browser showing its primary function | Shows where it lives and what it does. |
| Documentation Site / SSG | Rendered landing page of the generated documentation | Shows the quality of the output. |
| Bot | Command output examples rendered as styled terminal or chat mockup | Shows the bot working in context. |
| Framework | Polished example app built with the framework | Shows what is possible. |
| Library / Package | Architecture diagram or code example image (screenshots usually unnecessary) | Code examples in the README are better than images for libraries. |
| DevOps / Infrastructure | Architecture diagram of the system | Communicates what the tool manages. |
| Other / Unknown | Whatever the LLM infers as the most visually valuable aspect | Every shot must pass the portability test. |

---

## Screenshot Anti-Patterns

Avoid these:

1. **Empty state screenshots** -- No data populated. The app looks broken or useless.
2. **Login pages as hero** -- Nobody wants to see a login form. Show the product.
3. **Promotional banners instead of real screenshots** -- Marketing art is not a demo.
4. **Too many screenshots without organization** -- Use collapsible `<details>` sections after the first 2-3.
5. **Outdated screenshots showing old UI** -- Version-specific filenames or visibly stale design erodes trust.
6. **Low resolution or tiny images** -- Below 600px wide is unreadable. Always use `device_scale_factor: 2`.
7. **Screenshots that fail the portability test** -- If the image could appear in another project's README and make equal sense, it is not specific enough.
8. **Light mode only for developer tools** -- Dark mode is the default for developer-facing tools.
9. **Title screens as hero for games** -- The gameplay IS the product. Title screens are supplementary.
10. **Static screenshots for CLI tools** -- Motion (GIF) is far more effective than a still frame.

---

## Fallback Chain

When tools are missing, degrade gracefully:

| Missing Tool | Fallback | Result Quality |
|---|---|---|
| Playwright not installed | Mermaid diagrams in markdown, matplotlib charts, descriptive placeholders | Diagrams only, no app screenshots |
| VHS not installed | Playwright HTML terminal render (ANSI-to-HTML conversion) | Static terminal image instead of GIF |
| Freeze not installed | Playwright HTML render with highlight.js | Equivalent quality |
| ImageMagick not installed | Skip optimization, use raw captures | Larger file sizes |
| pngquant not installed | ImageMagick alone, or skip compression | Slightly larger PNGs |
| ffmpeg not installed | Skip GIF composition from frames, rely on VHS or Playwright | No burst-to-GIF |
| Pillow not installed | Skip image composition and validation | No before/after, no grids, no validation |
| Dev server will not start | Descriptive placeholder: `<!-- screenshot: start the app and capture the main view at 1280x800 -->` | Manual follow-up needed |
| App requires authentication | Check .env.example and docs for demo credentials; if none, leave placeholder with instructions | Manual follow-up needed |
| No sample input for visual output project | Check test fixtures, look for `--demo` flags, check for synthetic input generation; if nothing, leave placeholder describing the exact input needed | Manual follow-up needed |
| No visual component at all | Architecture diagram only | Perfectly fine -- some projects do not need screenshots |

---

## Capture Scripts Reference

Each script lives in the `scripts/` directory at the package root.

| Script | Path | Purpose |
|---|---|---|
| `capture-web-app.py` | `../../scripts/capture-web-app.py` | Start dev server, capture web app pages via Playwright with retina scaling, dark mode, networkidle wait |
| `generate-tape.py` | `../../scripts/generate-tape.py` | Write a VHS tape file for a command and run VHS to produce a demo GIF |
| `capture-terminal.py` | `../../scripts/capture-terminal.py` | ANSI-to-HTML conversion and Playwright screenshot fallback for CLI tools without VHS |
| `render-mermaid.py` | `../../scripts/render-mermaid.py` | Render Mermaid diagram source to PNG via Playwright with dark theme |
| `compose-images.py` | `../../scripts/compose-images.py` | Side-by-side comparisons, before/after compositions, and grid layouts using Pillow |
| `validate-screenshots.py` | `../../scripts/validate-screenshots.py` | Check captured images for minimum size, pixel diversity (not blank), and file size sanity |

---

## Image Dimensions Reference

Hero screenshots: display at 700-1024px (`width="800"` default). CLI demo GIF: 640-800px. Feature/secondary: 400-600px. Architecture diagrams: 600-800px. All Playwright captures use `device_scale_factor: 2` for retina-quality source images. The `width` attribute in markdown controls display size while preserving crispness on high-DPI screens.
