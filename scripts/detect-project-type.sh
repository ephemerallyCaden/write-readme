#!/usr/bin/env bash
# detect-project-type.sh — Detect project type using the unified taxonomy (20 signals, first match wins).
# Prints the canonical type slug to stdout. Exit 0 on success.

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: detect-project-type.sh [--dir PATH] [--help]

Detect the project type of a codebase using the unified taxonomy.
Runs 20 detection signals in priority order; first match wins.

Options:
  --dir PATH   Directory to analyze (default: current directory)
  --help       Show this help message

Output:
  Prints the canonical type slug to stdout:
    dotfiles, hardware, game, visual, gen-ai, bot, browser-ext, mobile, desktop, tui,
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

# Helper: search source files for an import/require pattern.
# Uses grep -q (stops at the first match) rather than piping into head: under
# pipefail, a grep killed by SIGPIPE after head exits made the check fail.
has_pattern() {
    grep -rqE --include='*.py' --include='*.js' --include='*.ts' --include='*.tsx' \
         --include='*.jsx' --include='*.rs' --include='*.go' --include='*.rb' \
         --include='*.java' --include='*.dart' --include='*.cs' --include='*.lua' \
         --include='*.toml' --include='*.cfg' --include='*.txt' \
         -e "$1" . 2>/dev/null
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
    grep -qE "\"$1\"" <<<"$PKG_JSON" 2>/dev/null
}

REPO_NAME=$(basename "$(pwd)")
REMOTE_NAME=$(git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#.*[/:]##' || true)

has_manifest() {
    has_any_file package.json pyproject.toml setup.py setup.cfg Cargo.toml go.mod \
        Gemfile pom.xml build.gradle build.gradle.kts composer.json pubspec.yaml \
        mix.exs Package.swift
}

# Count files at the root (dotted or not) that are personal rc files
count_rc_files() {
    local n=0 f
    for f in zshrc bashrc bash_profile profile zprofile zshenv vimrc gvimrc \
             tmux.conf gitconfig inputrc wezterm.lua alacritty.yml alacritty.toml \
             xinitrc Xresources; do
        if has_any_file ".$f" "$f"; then n=$((n + 1)); fi
    done
    if has_any_file "nvim/init.lua" "nvim/init.vim" ".config/nvim/init.lua" ".config/nvim/init.vim"; then
        n=$((n + 1))
    fi
    echo "$n"
}

# --- Priority 1: Personal config / dotfiles ---
NAMES_LC=$(printf '%s %s' "$REPO_NAME" "$REMOTE_NAME" | tr '[:upper:]' '[:lower:]')
if ! has_manifest && [[ "$NAMES_LC" == *dotfiles* ]]; then
    echo "dotfiles"; exit 0
fi
if has_any_file ".chezmoiroot" ".chezmoiignore" ".chezmoi.toml.tmpl" ".chezmoi.yaml.tmpl" \
    "install.conf.yaml" ".stow-local-ignore"; then
    echo "dotfiles"; exit 0
fi
if [ "$(find . -maxdepth 1 -name 'dot_*' 2>/dev/null | wc -l | tr -d ' ')" -ge 2 ]; then
    echo "dotfiles"; exit 0
fi
if has_file "configuration.yaml"; then
    if has_file "automations.yaml" || grep -qE '^homeassistant:' configuration.yaml 2>/dev/null; then
        echo "dotfiles"; exit 0
    fi
fi
if ! has_manifest && [ "$(count_rc_files)" -ge 3 ]; then echo "dotfiles"; exit 0; fi

# --- Priority 2: Hardware / Embedded ---
if find . -maxdepth 2 -not -path './node_modules/*' -not -path './.git/*' \
    \( -name 'platformio.ini' -o -name '*.kicad_pro' -o -name '*.kicad_pcb' \
       -o -name '*.kicad_sch' -o -iname 'bom.csv' \) -print -quit 2>/dev/null | grep -q .; then
    echo "hardware"; exit 0
fi
if find . -maxdepth 2 -name '*.ino' -not -path './examples/*' -not -path './node_modules/*' \
    -print -quit 2>/dev/null | grep -q .; then
    echo "hardware"; exit 0
fi

# --- Priority 3: Game / Interactive ---
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

# --- Priority 4: Visual Output / CV ---
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

# --- Priority 5: Generative AI ---
if has_pattern 'import\s+diffusers|from\s+diffusers|StableDiffusion|comfyui'; then
    echo "gen-ai"; exit 0
fi

# --- Priority 6: Bot ---
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

# --- Priority 7: Browser Extension ---
if has_file "manifest.json"; then
    if grep -qE '"(permissions|content_scripts|background)"' manifest.json 2>/dev/null; then
        echo "browser-ext"; exit 0
    fi
fi

# --- Priority 8: Mobile App ---
if has_file "pubspec.yaml"; then
    if has_any_dir "android" "ios"; then
        echo "mobile"; exit 0
    fi
fi
if pkg_has_dep "react-native"; then echo "mobile"; exit 0; fi
if has_any_dir "android" "ios"; then
    if find . -maxdepth 2 -name "*.xcodeproj" -print -quit 2>/dev/null | grep -q .; then
        echo "mobile"; exit 0
    fi
fi

# --- Priority 9: Desktop Application ---
if pkg_has_dep "electron"; then echo "desktop"; exit 0; fi
if has_file "src-tauri/tauri.conf.json" || has_file "tauri.conf.json"; then echo "desktop"; exit 0; fi
if has_pattern 'from\s+PyQt|import\s+PyQt|from\s+PySide|import\s+PySide'; then echo "desktop"; exit 0; fi
if has_pattern 'import.*QtWidgets|from.*QtWidgets|QApplication|QMainWindow'; then echo "desktop"; exit 0; fi
if has_pattern 'import\s+gi.*Gtk|from\s+gi.*Gtk|gtk::prelude'; then echo "desktop"; exit 0; fi
if has_pattern 'import\s+SwiftUI|import\s+Cocoa|import\s+AppKit'; then echo "desktop"; exit 0; fi
if has_pattern 'System\.Windows|WPF|WindowsForms'; then echo "desktop"; exit 0; fi
if find . -maxdepth 2 -name "*.desktop" -print -quit 2>/dev/null | grep -q .; then echo "desktop"; exit 0; fi

# --- Priority 10: TUI Application ---
if has_pattern 'from\s+textual|import\s+textual|from\s+blessed|import\s+blessed'; then echo "tui"; exit 0; fi
if has_pattern 'import.*tview|tview\.|bubbletea|tea\.Model'; then echo "tui"; exit 0; fi
if has_pattern 'import.*cursive|cursive::'; then echo "tui"; exit 0; fi
if has_pattern 'import.*crossterm|crossterm::'; then echo "tui"; exit 0; fi
if has_pattern 'import.*ncurses|ncurses\.h|initscr|curses\.wrapper'; then echo "tui"; exit 0; fi

# --- Priority 11: Documentation Site / SSG ---
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

# --- Priority 12: Web Application ---
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
        if grep -qE '"(dev|start|serve)"' <<<"$PKG_JSON" 2>/dev/null; then
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

# --- Priority 13: API / Backend Service ---
if [ "$HAS_SERVER" = true ]; then
    echo "api"; exit 0
fi

# --- Priority 14: CLI Tool ---
if [ -n "$PKG_JSON" ]; then
    if grep -qE '"bin"' <<<"$PKG_JSON" 2>/dev/null; then echo "cli"; exit 0; fi
fi
if has_pattern 'argparse|click\.command|@click\.group|typer\.Typer'; then echo "cli"; exit 0; fi
if has_pattern 'console_scripts'; then echo "cli"; exit 0; fi
if has_file "Cargo.toml" && grep -qE '\[\[bin\]\]' Cargo.toml 2>/dev/null; then
    if has_pattern 'clap::Parser|structopt|#\[command\]'; then echo "cli"; exit 0; fi
fi
if has_pattern 'cobra\.Command|rootCmd|func.*main.*flag\.Parse'; then echo "cli"; exit 0; fi

# --- Priority 15: Framework ---
if has_pattern 'plugin|middleware|register.*hook|createApp|scaffold'; then
    if [ -n "$PKG_JSON" ] && grep -qE '"create-' <<<"$PKG_JSON" 2>/dev/null; then
        echo "framework"; exit 0
    fi
    if has_pattern 'plugin.*system|hook.*register|middleware.*chain|use.*middleware'; then
        echo "framework"; exit 0
    fi
fi

# --- Priority 16: ML/AI Model ---
if has_pattern 'import\s+torch|from\s+torch|import\s+tensorflow|from\s+tensorflow|import\s+jax|from\s+jax'; then
    if has_any_dir "models" "model" "checkpoints" "weights"; then
        echo "ml"; exit 0
    fi
    if has_pattern 'train|training|epoch|loss.*backward|optimizer\.step'; then
        echo "ml"; exit 0
    fi
fi

# --- Priority 17: DevOps / Infrastructure ---
if find . -maxdepth 3 -name "*.tf" -print -quit 2>/dev/null | grep -q .; then echo "devops"; exit 0; fi
if has_any_file "ansible.cfg" "playbook.yml"; then echo "devops"; exit 0; fi
if has_file "Chart.yaml" || has_dir "templates" && has_file "values.yaml"; then echo "devops"; exit 0; fi
if find . -maxdepth 3 -name "*.yaml" -exec grep -q 'apiVersion.*apps/v1\|kind:\s*Deployment\|kind:\s*Service' {} \; -print -quit 2>/dev/null | grep -q .; then
    echo "devops"; exit 0
fi

# --- Priority 18: Educational / Awesome ---
if grep -qi '^awesome-' <<<"$REPO_NAME"; then echo "educational"; exit 0; fi
if has_file "README.md"; then
    if grep -cE '^\s*[-*]\s+\[' README.md 2>/dev/null | awk '{if ($1 > 20) exit 0; else exit 1}'; then
        # Curated list with >20 link items and minimal source code
        SRC_COUNT=$(find . -maxdepth 2 \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | wc -l | tr -d ' ')
        if [ "$SRC_COUNT" -lt 3 ]; then
            echo "educational"; exit 0
        fi
    fi
fi

# --- Priority 19: Library / Package ---
if [ -n "$PKG_JSON" ]; then
    if grep -qE '"(exports|main|module|types)"' <<<"$PKG_JSON" 2>/dev/null; then
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
if has_file "Gemfile" || find . -maxdepth 1 -name "*.gemspec" -print -quit 2>/dev/null | grep -q .; then
    echo "library"; exit 0
fi

# --- Priority 20: Other / Unknown ---
echo "other"
exit 0
