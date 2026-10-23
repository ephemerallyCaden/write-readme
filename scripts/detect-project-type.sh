#!/usr/bin/env bash
# detect-project-type.sh — Detect project type using the unified taxonomy (18 signals, first match wins).
# Prints the canonical type slug to stdout. Exit 0 on success.

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: detect-project-type.sh [--dir PATH] [--help]

Detect the project type of a codebase using the unified taxonomy.
Runs 18 detection signals in priority order; first match wins.

Options:
  --dir PATH   Directory to analyze (default: current directory)
  --help       Show this help message

Output:
  Prints the canonical type slug to stdout:
    game, visual, gen-ai, bot, browser-ext, mobile, desktop, tui,
    docs-site, web-app, api, cli, framework, ml, devops, educational,
    library, other
USAGE
    exit 0
}

DIR="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir) DIR="$2"; shift 2 ;;
        --help|-h) usage ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

cd "$DIR"

# Helper: search files for import/require patterns (case-insensitive grep, limited depth)
has_pattern() {
    grep -rl --include='*.py' --include='*.js' --include='*.ts' --include='*.tsx' \
         --include='*.jsx' --include='*.rs' --include='*.go' --include='*.rb' \
         --include='*.java' --include='*.dart' --include='*.cs' --include='*.lua' \
         --include='*.toml' --include='*.cfg' --include='*.txt' \
         -E "$1" . 2>/dev/null | head -1 | grep -q .
}

has_file() {
    test -e "$1"
}

has_any_file() {
    for f in "$@"; do
        if test -e "$f"; then return 0; fi
    done
    return 1
}

has_dir() {
    test -d "$1"
}

has_any_dir() {
    for d in "$@"; do
        if test -d "$d"; then return 0; fi
    done
    return 1
}

# Read package.json content once if it exists
PKG_JSON=""
if has_file "package.json"; then
    PKG_JSON=$(cat package.json 2>/dev/null || true)
fi

pkg_has_dep() {
    if [ -z "$PKG_JSON" ]; then return 1; fi
    echo "$PKG_JSON" | grep -qE "\"$1\"" 2>/dev/null
}

# --- Priority 1: Game / Interactive ---
if has_file "project.godot"; then echo "game"; exit 0; fi
if has_pattern 'import\s+pygame|from\s+pygame|import\s+arcade|from\s+arcade'; then echo "game"; exit 0; fi
if has_pattern 'import\s+raylib|from\s+raylib|use\s+bevy|bevy::prelude'; then echo "game"; exit 0; fi
if has_pattern 'require.*love|love\.(graphics|physics|window)'; then echo "game"; exit 0; fi
if has_pattern 'import.*Phaser|require.*phaser|from.*phaser'; then echo "game"; exit 0; fi
if has_pattern 'import.*PixiJS|require.*pixi\.js|from.*pixi\.js'; then echo "game"; exit 0; fi
if has_pattern 'import.*BABYLON|require.*babylonjs|from.*babylonjs'; then echo "game"; exit 0; fi
if has_any_dir "sprites" "levels" "textures"; then
    # Only count as game if asset dirs exist alongside game-like code
    if has_pattern 'player|enemy|sprite|collision|score|level'; then
        echo "game"; exit 0
    fi
fi

# --- Priority 2: Visual Output / CV ---
if has_pattern 'import\s+cv2|from\s+cv2|import\s+mediapipe|from\s+mediapipe|import\s+dlib'; then
    if has_pattern 'VideoCapture|imwrite|landmark|bounding.box|imshow'; then
        echo "visual"; exit 0
    fi
fi
if has_pattern 'import\s+matplotlib|from\s+matplotlib|import\s+plotly|from\s+plotly'; then
    if has_pattern 'import\s+pandas|from\s+pandas|DataFrame|read_csv|pipeline'; then
        echo "visual"; exit 0
    fi
fi
if has_pattern 'import.*d3|require.*d3|from.*d3-'; then echo "visual"; exit 0; fi
if has_pattern 'import.*chart\.js|require.*chart\.js'; then echo "visual"; exit 0; fi
if has_pattern 'import\s+bokeh|from\s+bokeh|import\s+seaborn|from\s+seaborn'; then
    if has_pattern 'DataFrame|read_csv|pipeline|data'; then
        echo "visual"; exit 0
    fi
fi

# --- Priority 3: Generative AI ---
if has_pattern 'import\s+diffusers|from\s+diffusers|StableDiffusion|comfyui'; then
    echo "gen-ai"; exit 0
fi

# --- Priority 4: Bot ---
if has_pattern 'import\s+discord|from\s+discord|require.*discord\.js|from.*discord\.js'; then
    echo "bot"; exit 0
fi
if has_pattern 'import.*telegram|from.*telegram|python-telegram-bot|telegraf'; then
    echo "bot"; exit 0
fi
if has_pattern 'slack.bolt|slack_bolt|from.*slack_sdk|import.*slack_sdk'; then
    echo "bot"; exit 0
fi
if has_pattern 'DISCORD_TOKEN|BOT_TOKEN|TELEGRAM_TOKEN|SLACK_BOT_TOKEN'; then
    echo "bot"; exit 0
fi

# --- Priority 5: Browser Extension ---
if has_file "manifest.json"; then
    if grep -qE '"(permissions|content_scripts|background)"' manifest.json 2>/dev/null; then
        echo "browser-ext"; exit 0
    fi
fi

# --- Priority 6: Mobile App ---
if has_file "pubspec.yaml"; then
    if has_any_dir "android" "ios"; then
        echo "mobile"; exit 0
    fi
fi
if pkg_has_dep "react-native"; then echo "mobile"; exit 0; fi
if has_any_dir "android" "ios"; then
    if find . -maxdepth 2 -name "*.xcodeproj" 2>/dev/null | head -1 | grep -q .; then
        echo "mobile"; exit 0
    fi
fi

# --- Priority 7: Desktop Application ---
if pkg_has_dep "electron"; then echo "desktop"; exit 0; fi
if has_file "src-tauri/tauri.conf.json" || has_file "tauri.conf.json"; then echo "desktop"; exit 0; fi
if has_pattern 'from\s+PyQt|import\s+PyQt|from\s+PySide|import\s+PySide'; then echo "desktop"; exit 0; fi
if has_pattern 'import.*QtWidgets|from.*QtWidgets|QApplication|QMainWindow'; then echo "desktop"; exit 0; fi
if has_pattern 'import\s+gi.*Gtk|from\s+gi.*Gtk|gtk::prelude'; then echo "desktop"; exit 0; fi
if has_pattern 'import\s+SwiftUI|import\s+Cocoa|import\s+AppKit'; then echo "desktop"; exit 0; fi
if has_pattern 'System\.Windows|WPF|WindowsForms'; then echo "desktop"; exit 0; fi
if find . -maxdepth 2 -name "*.desktop" 2>/dev/null | head -1 | grep -q .; then echo "desktop"; exit 0; fi

# --- Priority 8: TUI Application ---
if has_pattern 'from\s+textual|import\s+textual|from\s+blessed|import\s+blessed'; then echo "tui"; exit 0; fi
if has_pattern 'import.*tview|tview\.|bubbletea|tea\.Model'; then echo "tui"; exit 0; fi
if has_pattern 'import.*cursive|cursive::'; then echo "tui"; exit 0; fi
if has_pattern 'import.*crossterm|crossterm::'; then echo "tui"; exit 0; fi
if has_pattern 'import.*ncurses|ncurses\.h|initscr|curses\.wrapper'; then echo "tui"; exit 0; fi

# --- Priority 9: Documentation Site / SSG ---
if has_any_file "docusaurus.config.js" "docusaurus.config.ts"; then echo "docs-site"; exit 0; fi
if has_file "mkdocs.yml"; then echo "docs-site"; exit 0; fi
if has_any_file "vitepress" ".vitepress/config.js" ".vitepress/config.ts" ".vitepress/config.mts"; then echo "docs-site"; exit 0; fi
if has_any_file "astro.config.mjs" "astro.config.ts"; then
    # Astro can be a web app too — only classify as docs if content/ dir exists
    if has_dir "src/content" || has_dir "docs"; then echo "docs-site"; exit 0; fi
fi
if has_file "conf.py"; then
    if grep -qE 'extensions.*sphinx|sphinx' conf.py 2>/dev/null; then echo "docs-site"; exit 0; fi
fi

# --- Priority 10: Web Application ---
# Server framework + dev/start/serve script
HAS_SERVER=false
if pkg_has_dep "express" || pkg_has_dep "next" || pkg_has_dep "nuxt" || pkg_has_dep "svelte" || pkg_has_dep "@sveltejs/kit"; then
    HAS_SERVER=true
fi
if has_pattern 'from\s+fastapi|import\s+fastapi|from\s+flask|import\s+flask|from\s+django|import\s+django'; then
    HAS_SERVER=true
fi
if has_file "Gemfile" && grep -qE 'rails|sinatra' Gemfile 2>/dev/null; then HAS_SERVER=true; fi

if [ "$HAS_SERVER" = true ]; then
    HAS_START=false
    if [ -n "$PKG_JSON" ]; then
        if echo "$PKG_JSON" | grep -qE '"(dev|start|serve)"' 2>/dev/null; then
            HAS_START=true
        fi
    fi
    # Python projects with manage.py or main entry
    if has_file "manage.py" || has_file "app.py" || has_file "main.py"; then HAS_START=true; fi
    if has_file "Procfile"; then HAS_START=true; fi

    if [ "$HAS_START" = true ]; then
        # Check for frontend files to distinguish web-app from api
        HAS_FRONTEND=false
        if has_any_dir "pages" "components" "src/pages" "src/components" "templates" "public"; then
            HAS_FRONTEND=true
        fi
        if has_file "public/index.html" || has_file "index.html"; then HAS_FRONTEND=true; fi

        if [ "$HAS_FRONTEND" = true ]; then
            echo "web-app"; exit 0
        fi
    fi
fi

# --- Priority 11: API / Backend Service ---
if [ "$HAS_SERVER" = true ]; then
    echo "api"; exit 0
fi

# --- Priority 12: CLI Tool ---
if [ -n "$PKG_JSON" ]; then
    if echo "$PKG_JSON" | grep -qE '"bin"' 2>/dev/null; then echo "cli"; exit 0; fi
fi
if has_pattern 'argparse|click\.command|@click\.group|typer\.Typer'; then echo "cli"; exit 0; fi
if has_pattern 'console_scripts'; then echo "cli"; exit 0; fi
if has_file "Cargo.toml" && grep -qE '\[\[bin\]\]' Cargo.toml 2>/dev/null; then
    if has_pattern 'clap::Parser|structopt|#\[command\]'; then echo "cli"; exit 0; fi
fi
if has_pattern 'cobra\.Command|rootCmd|func.*main.*flag\.Parse'; then echo "cli"; exit 0; fi

# --- Priority 13: Framework ---
if has_pattern 'plugin|middleware|register.*hook|createApp|scaffold'; then
    if [ -n "$PKG_JSON" ] && echo "$PKG_JSON" | grep -qE '"create-' 2>/dev/null; then
        echo "framework"; exit 0
    fi
    if has_pattern 'plugin.*system|hook.*register|middleware.*chain|use.*middleware'; then
        echo "framework"; exit 0
    fi
fi

# --- Priority 14: ML/AI Model ---
if has_pattern 'import\s+torch|from\s+torch|import\s+tensorflow|from\s+tensorflow|import\s+jax|from\s+jax'; then
    if has_any_dir "models" "model" "checkpoints" "weights"; then
        echo "ml"; exit 0
    fi
    if has_pattern 'train|training|epoch|loss.*backward|optimizer\.step'; then
        echo "ml"; exit 0
    fi
fi

# --- Priority 15: DevOps / Infrastructure ---
if find . -maxdepth 3 -name "*.tf" 2>/dev/null | head -1 | grep -q .; then echo "devops"; exit 0; fi
if has_any_file "ansible.cfg" "playbook.yml"; then echo "devops"; exit 0; fi
if has_file "Chart.yaml" || has_dir "templates" && has_file "values.yaml"; then echo "devops"; exit 0; fi
if find . -maxdepth 3 -name "*.yaml" -exec grep -l 'apiVersion.*apps/v1\|kind:\s*Deployment\|kind:\s*Service' {} + 2>/dev/null | head -1 | grep -q .; then
    echo "devops"; exit 0
fi

# --- Priority 16: Educational / Awesome ---
REPO_NAME=$(basename "$(pwd)")
if echo "$REPO_NAME" | grep -qi '^awesome-'; then echo "educational"; exit 0; fi
if has_file "README.md"; then
    if grep -cE '^\s*[-*]\s+\[' README.md 2>/dev/null | awk '{if ($1 > 20) exit 0; else exit 1}'; then
        # Curated list with >20 link items and minimal source code
        SRC_COUNT=$(find . -maxdepth 2 \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | wc -l | tr -d ' ')
        if [ "$SRC_COUNT" -lt 3 ]; then
            echo "educational"; exit 0
        fi
    fi
fi

# --- Priority 17: Library / Package ---
if [ -n "$PKG_JSON" ]; then
    if echo "$PKG_JSON" | grep -qE '"(exports|main|module|types)"' 2>/dev/null; then
        echo "library"; exit 0
    fi
fi
if has_file "Cargo.toml" && grep -qE '^\[lib\]' Cargo.toml 2>/dev/null; then echo "library"; exit 0; fi
if has_file "pyproject.toml" || has_file "setup.py" || has_file "setup.cfg"; then
    # Python package without CLI entry points or server framework
    if ! has_pattern 'console_scripts|argparse|click\.command|typer\.Typer'; then
        if ! has_pattern 'from\s+fastapi|from\s+flask|from\s+django'; then
            echo "library"; exit 0
        fi
    fi
fi
if has_file "go.mod" && ! has_pattern 'func\s+main'; then echo "library"; exit 0; fi
if has_file "Gemfile" || find . -maxdepth 1 -name "*.gemspec" 2>/dev/null | head -1 | grep -q .; then
    echo "library"; exit 0
fi

# --- Priority 18: Other / Unknown ---
echo "other"
exit 0
