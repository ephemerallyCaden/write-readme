#!/usr/bin/env python3
"""Generate shields.io badge markdown for a project.

Takes owner, repo, ecosystem, package, license, and CI workflow as arguments.
Prints badge markdown lines to stdout. Max 6 badges, flat style.
"""
from __future__ import annotations

import argparse
import sys


ECOSYSTEM_VERSION_URLS: dict[str, str] = {
    "npm": "https://img.shields.io/npm/v/{package}",
    "pypi": "https://img.shields.io/pypi/v/{package}",
    "crates.io": "https://img.shields.io/crates/v/{package}",
    "go": "https://img.shields.io/github/v/tag/{owner}/{repo}",
    "rubygems": "https://img.shields.io/gem/v/{package}",
    "pub.dev": "https://img.shields.io/pub/v/{package}",
    "packagist": "https://img.shields.io/packagist/v/{package}",
    "maven": "https://img.shields.io/maven-central/v/{package}",
    "hex.pm": "https://img.shields.io/hexpm/v/{package}",
    "hackage": "https://img.shields.io/hackage/v/{package}",
}

ECOSYSTEM_DOWNLOAD_URLS: dict[str, str] = {
    "npm": "https://img.shields.io/npm/dm/{package}",
    "pypi": "https://img.shields.io/pypi/dm/{package}",
    "crates.io": "https://img.shields.io/crates/d/{package}",
    "rubygems": "https://img.shields.io/gem/dt/{package}",
    "pub.dev": "https://img.shields.io/pub/popularity/{package}",
    "packagist": "https://img.shields.io/packagist/dm/{package}",
    "hex.pm": "https://img.shields.io/hexpm/dt/{package}",
    "hackage": "https://img.shields.io/hackage-deps/v/{package}",
}

ECOSYSTEM_LINK_URLS: dict[str, str] = {
    "npm": "https://www.npmjs.com/package/{package}",
    "pypi": "https://pypi.org/project/{package}/",
    "crates.io": "https://crates.io/crates/{package}",
    "go": "https://pkg.go.dev/{package}",
    "rubygems": "https://rubygems.org/gems/{package}",
    "pub.dev": "https://pub.dev/packages/{package}",
    "packagist": "https://packagist.org/packages/{package}",
    "maven": "https://search.maven.org/artifact/{package}",
    "hex.pm": "https://hex.pm/packages/{package}",
    "hackage": "https://hackage.haskell.org/package/{package}",
}


def generate_badges(
    owner: str | None,
    repo: str | None,
    ecosystem: str | None,
    package: str | None,
    license_name: str | None,
    ci_workflow: str | None,
) -> list[str]:
    badges: list[str] = []

    # 1. License badge (always if owner/repo available)
    if license_name and owner and repo:
        url = f"https://img.shields.io/github/license/{owner}/{repo}?style=flat"
        badges.append(f"[![License]({url})](LICENSE)")
    elif license_name:
        url = f"https://img.shields.io/badge/license-{license_name}-blue?style=flat"
        badges.append(f"[![License]({url})](LICENSE)")

    # 2. CI badge (if workflow provided)
    if ci_workflow and owner and repo:
        workflow = ci_workflow.rstrip(".yml").rstrip(".yaml")
        workflow_file = ci_workflow if ci_workflow.endswith((".yml", ".yaml")) else f"{ci_workflow}.yml"
        url = (
            f"https://img.shields.io/github/actions/workflow/status/"
            f"{owner}/{repo}/{workflow_file}?style=flat&label=CI"
        )
        link = f"https://github.com/{owner}/{repo}/actions/workflows/{workflow_file}"
        badges.append(f"[![CI]({url})]({link})")

    # 3. Version badge (if ecosystem + package)
    eco_lower = ecosystem.lower() if ecosystem else ""
    if eco_lower in ECOSYSTEM_VERSION_URLS and package:
        url_template = ECOSYSTEM_VERSION_URLS[eco_lower]
        url = url_template.format(package=package, owner=owner or "", repo=repo or "")
        url += "?style=flat"
        link = ECOSYSTEM_LINK_URLS.get(eco_lower, "")
        if link:
            link = link.format(package=package, owner=owner or "", repo=repo or "")
        badges.append(f"[![Version]({url})]({link})" if link else f"![Version]({url})")

    # 4. Downloads badge (if ecosystem + package)
    if eco_lower in ECOSYSTEM_DOWNLOAD_URLS and package:
        url_template = ECOSYSTEM_DOWNLOAD_URLS[eco_lower]
        url = url_template.format(package=package, owner=owner or "", repo=repo or "")
        url += "?style=flat"
        badges.append(f"![Downloads]({url})")

    # Cap at 6
    return badges[:6]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate shields.io badge markdown for a project."
    )
    parser.add_argument("--owner", default=None, help="GitHub repository owner")
    parser.add_argument("--repo", default=None, help="GitHub repository name")
    parser.add_argument(
        "--ecosystem",
        default=None,
        help="Package ecosystem (npm, pypi, crates.io, go, rubygems, pub.dev, "
        "packagist, maven, hex.pm, hackage)",
    )
    parser.add_argument("--package", default=None, help="Package name in the ecosystem")
    parser.add_argument("--license", dest="license_name", default=None, help="License identifier (e.g., MIT)")
    parser.add_argument("--ci-workflow", default=None, help="CI workflow filename (e.g., ci.yml)")

    args = parser.parse_args()

    badges = generate_badges(
        owner=args.owner,
        repo=args.repo,
        ecosystem=args.ecosystem,
        package=args.package,
        license_name=args.license_name,
        ci_workflow=args.ci_workflow,
    )

    if not badges:
        print("<!-- No badges generated. Provide --owner/--repo or --ecosystem/--package. -->",
              file=sys.stderr)
        sys.exit(0)

    print(" ".join(badges))


if __name__ == "__main__":
    main()
