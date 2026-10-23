#!/usr/bin/env python3
"""Extract metadata from any package manifest and output JSON.

Supports: package.json, pyproject.toml, setup.py, setup.cfg, Cargo.toml,
go.mod, Gemfile, pom.xml, build.gradle, pubspec.yaml, composer.json,
CMakeLists.txt, Makefile, mix.exs.

Uses only stdlib + tomllib (Python 3.11+). Prints JSON to stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore[assignment]


def empty_metadata() -> dict:
    return {
        "name": None,
        "version": None,
        "description": None,
        "license": None,
        "dependencies": [],
        "scripts": {},
        "entry_points": [],
        "engines": {},
    }


def parse_package_json(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    meta["name"] = data.get("name")
    meta["version"] = data.get("version")
    meta["description"] = data.get("description")
    meta["license"] = data.get("license")
    deps = list(data.get("dependencies", {}).keys())
    deps += list(data.get("devDependencies", {}).keys())
    meta["dependencies"] = deps
    meta["scripts"] = data.get("scripts", {})
    if "bin" in data:
        b = data["bin"]
        if isinstance(b, str):
            meta["entry_points"] = [data.get("name", "")]
        elif isinstance(b, dict):
            meta["entry_points"] = list(b.keys())
    meta["engines"] = data.get("engines", {})
    return meta


def parse_pyproject_toml(path: str) -> dict:
    meta = empty_metadata()
    if tomllib is None:
        return meta
    with open(path, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    meta["name"] = project.get("name") or data.get("tool", {}).get("poetry", {}).get("name")
    meta["version"] = project.get("version") or data.get("tool", {}).get("poetry", {}).get("version")
    meta["description"] = project.get("description") or data.get("tool", {}).get("poetry", {}).get("description")
    lic = project.get("license")
    if isinstance(lic, dict):
        meta["license"] = lic.get("text") or lic.get("file")
    elif isinstance(lic, str):
        meta["license"] = lic
    deps = [str(d) for d in project.get("dependencies", [])]
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if isinstance(poetry_deps, dict):
        deps += [k for k in poetry_deps if k != "python"]
    meta["dependencies"] = deps
    scripts = project.get("scripts", {})
    meta["scripts"] = scripts
    eps = list(scripts.keys()) if scripts else []
    gui_scripts = project.get("gui-scripts", {})
    eps += list(gui_scripts.keys())
    meta["entry_points"] = eps
    python_req = project.get("requires-python")
    if python_req:
        meta["engines"]["python"] = python_req
    return meta


def parse_setup_py(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for field in ("name", "version", "description", "license"):
        m = re.search(rf'{field}\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            meta[field] = m.group(1)
    deps = re.findall(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if deps:
        meta["dependencies"] = re.findall(r'["\']([^"\']+)["\']', deps[0])
    eps = re.findall(r'console_scripts\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if eps:
        meta["entry_points"] = re.findall(r'["\']([^"\'=]+)', eps[0])
    return meta


def parse_setup_cfg(path: str) -> dict:
    meta = empty_metadata()
    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(path)
    if cfg.has_section("metadata"):
        meta["name"] = cfg.get("metadata", "name", fallback=None)
        meta["version"] = cfg.get("metadata", "version", fallback=None)
        meta["description"] = cfg.get("metadata", "description", fallback=None)
        meta["license"] = cfg.get("metadata", "license", fallback=None)
    if cfg.has_section("options"):
        deps = cfg.get("options", "install_requires", fallback="")
        meta["dependencies"] = [d.strip() for d in deps.splitlines() if d.strip()]
        python_req = cfg.get("options", "python_requires", fallback=None)
        if python_req:
            meta["engines"]["python"] = python_req
    if cfg.has_section("options.entry_points"):
        cs = cfg.get("options.entry_points", "console_scripts", fallback="")
        meta["entry_points"] = [
            line.split("=")[0].strip()
            for line in cs.splitlines()
            if "=" in line
        ]
    return meta


def parse_cargo_toml(path: str) -> dict:
    meta = empty_metadata()
    if tomllib is None:
        return meta
    with open(path, "rb") as f:
        data = tomllib.load(f)
    pkg = data.get("package", {})
    meta["name"] = pkg.get("name")
    meta["version"] = pkg.get("version")
    meta["description"] = pkg.get("description")
    meta["license"] = pkg.get("license")
    deps = list(data.get("dependencies", {}).keys())
    deps += list(data.get("dev-dependencies", {}).keys())
    meta["dependencies"] = deps
    if "rust-version" in pkg:
        meta["engines"]["rust"] = pkg["rust-version"]
    bins = data.get("bin", [])
    if isinstance(bins, list):
        meta["entry_points"] = [b.get("name", "") for b in bins if isinstance(b, dict)]
    return meta


def parse_go_mod(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
    if m:
        meta["name"] = m.group(1).split("/")[-1]
    m = re.search(r'^go\s+(\S+)', content, re.MULTILINE)
    if m:
        meta["engines"]["go"] = m.group(1)
    deps = re.findall(r'^\s+(\S+)\s+v[\d.]+', content, re.MULTILINE)
    meta["dependencies"] = deps
    return meta


def parse_gemfile(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    meta["dependencies"] = re.findall(r"gem\s+['\"]([^'\"]+)['\"]", content)
    # Try to find .gemspec for name/version
    import glob
    specs = glob.glob(os.path.join(os.path.dirname(path), "*.gemspec"))
    for spec in specs:
        with open(spec, encoding="utf-8") as f:
            sc = f.read()
        for field in ("name", "version", "summary", "license"):
            target = "description" if field == "summary" else field
            m = re.search(rf'\.{field}\s*=\s*["\']([^"\']+)["\']', sc)
            if m:
                meta[target] = m.group(1)
    return meta


def parse_pom_xml(path: str) -> dict:
    meta = empty_metadata()
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        ns = ""
        m = re.match(r'\{(.*?)\}', root.tag)
        if m:
            ns = m.group(1)

        def find(tag: str) -> str | None:
            el = root.find(f'{{{ns}}}{tag}' if ns else tag)
            return el.text if el is not None else None

        meta["name"] = find("artifactId")
        meta["version"] = find("version")
        meta["description"] = find("name") or find("description")
        lic_el = root.find(f'.//{{{ns}}}license/{{{ns}}}name' if ns else './/license/name')
        if lic_el is not None:
            meta["license"] = lic_el.text
        dep_path = f'.//{{{ns}}}dependency' if ns else './/dependency'
        deps = []
        for dep in root.findall(dep_path):
            aid = dep.find(f'{{{ns}}}artifactId' if ns else 'artifactId')
            if aid is not None and aid.text:
                deps.append(aid.text)
        meta["dependencies"] = deps
    except ET.ParseError:
        pass
    return meta


def parse_build_gradle(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    deps = re.findall(r"(?:implementation|api|compile)\s+['\"]([^'\"]+)['\"]", content)
    meta["dependencies"] = [d.split(":")[-2] if ":" in d else d for d in deps]
    m = re.search(r"version\s*=?\s*['\"]([^'\"]+)['\"]", content)
    if m:
        meta["version"] = m.group(1)
    m = re.search(r"group\s*=?\s*['\"]([^'\"]+)['\"]", content)
    if m:
        meta["name"] = m.group(1)
    return meta


def parse_pubspec_yaml(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for field in ("name", "version", "description"):
        m = re.search(rf'^{field}:\s*(.+)$', content, re.MULTILINE)
        if m:
            val = m.group(1).strip().strip("'\"")
            meta[field] = val
    dep_section = re.search(r'^dependencies:\s*\n((?:\s+.+\n)*)', content, re.MULTILINE)
    if dep_section:
        meta["dependencies"] = re.findall(r'^\s+(\w[\w_-]*):', dep_section.group(1), re.MULTILINE)
    env = re.search(r'^environment:\s*\n((?:\s+.+\n)*)', content, re.MULTILINE)
    if env:
        sdk_m = re.search(r'sdk:\s*(.+)', env.group(1))
        if sdk_m:
            meta["engines"]["dart"] = sdk_m.group(1).strip().strip("'\"")
    return meta


def parse_composer_json(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    meta["name"] = data.get("name")
    meta["version"] = data.get("version")
    meta["description"] = data.get("description")
    lic = data.get("license")
    meta["license"] = lic if isinstance(lic, str) else (lic[0] if isinstance(lic, list) and lic else None)
    deps = list(data.get("require", {}).keys())
    deps += list(data.get("require-dev", {}).keys())
    meta["dependencies"] = [d for d in deps if d != "php"]
    meta["scripts"] = data.get("scripts", {})
    php_req = data.get("require", {}).get("php")
    if php_req:
        meta["engines"]["php"] = php_req
    return meta


def parse_cmakelists(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'project\s*\(\s*(\w+)', content, re.IGNORECASE)
    if m:
        meta["name"] = m.group(1)
    m = re.search(r'VERSION\s+([\d.]+)', content)
    if m:
        meta["version"] = m.group(1)
    m = re.search(r'cmake_minimum_required\s*\(.*?VERSION\s+([\d.]+)', content, re.IGNORECASE)
    if m:
        meta["engines"]["cmake"] = m.group(1)
    deps = re.findall(r'find_package\s*\(\s*(\w+)', content)
    meta["dependencies"] = deps
    return meta


def parse_makefile(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    targets = re.findall(r'^([\w-]+)\s*:', content, re.MULTILINE)
    meta["scripts"] = {t: t for t in targets if t not in ("all", ".PHONY", ".DEFAULT")}
    m = re.search(r'PROJECT\s*[:?]?=\s*(\S+)', content)
    if m:
        meta["name"] = m.group(1)
    m = re.search(r'VERSION\s*[:?]?=\s*(\S+)', content)
    if m:
        meta["version"] = m.group(1)
    return meta


def parse_mix_exs(path: str) -> dict:
    meta = empty_metadata()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'app:\s*:(\w+)', content)
    if m:
        meta["name"] = m.group(1)
    m = re.search(r'version:\s*"([^"]+)"', content)
    if m:
        meta["version"] = m.group(1)
    m = re.search(r'description:\s*"([^"]+)"', content)
    if m:
        meta["description"] = m.group(1)
    deps = re.findall(r'\{:(\w+),', content)
    meta["dependencies"] = deps
    m = re.search(r'elixir:\s*"([^"]+)"', content)
    if m:
        meta["engines"]["elixir"] = m.group(1)
    return meta


MANIFEST_PARSERS = [
    ("package.json", parse_package_json),
    ("pyproject.toml", parse_pyproject_toml),
    ("setup.py", parse_setup_py),
    ("setup.cfg", parse_setup_cfg),
    ("Cargo.toml", parse_cargo_toml),
    ("go.mod", parse_go_mod),
    ("Gemfile", parse_gemfile),
    ("pom.xml", parse_pom_xml),
    ("build.gradle", parse_build_gradle),
    ("pubspec.yaml", parse_pubspec_yaml),
    ("composer.json", parse_composer_json),
    ("CMakeLists.txt", parse_cmakelists),
    ("Makefile", parse_makefile),
    ("mix.exs", parse_mix_exs),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract metadata from package manifests and output JSON."
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory to scan for manifests (default: current directory)",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Specific manifest file to parse (overrides auto-detection)",
    )
    args = parser.parse_args()

    if args.manifest:
        path = args.manifest
        basename = os.path.basename(path)
        for name, parse_fn in MANIFEST_PARSERS:
            if basename == name:
                try:
                    result = parse_fn(path)
                    json.dump(result, sys.stdout, indent=2)
                    print()
                    return
                except Exception as e:
                    print(f"Error parsing {path}: {e}", file=sys.stderr)
                    sys.exit(1)
        print(f"Unknown manifest type: {basename}", file=sys.stderr)
        sys.exit(1)

    # Auto-detect: try each manifest in priority order
    for name, parse_fn in MANIFEST_PARSERS:
        path = os.path.join(args.dir, name)
        if os.path.isfile(path):
            try:
                result = parse_fn(path)
                result["_manifest"] = name
                json.dump(result, sys.stdout, indent=2)
                print()
                return
            except Exception as e:
                print(f"Warning: failed to parse {name}: {e}", file=sys.stderr)
                continue

    # Nothing found
    result = empty_metadata()
    result["_manifest"] = None
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
