---
name: github-clawhub-launcher
description: GitHub + ClawHub Launcher is a public ClawHub release-launcher skill. Use it when the user says "github clawhub launcher", "repo release launcher", or wants to prepare, check, and publish a GitHub repo plus ClawHub package from one local project folder.
version: 1.0.4
homepage: https://github.com/zack-dev-cm/github-clawhub-launcher
license: MIT-0
user-invocable: true
metadata: {"openclaw":{"homepage":"https://github.com/zack-dev-cm/github-clawhub-launcher","skillKey":"github-clawhub-launcher","requires":{"bins":["git","gh","npx"],"anyBins":["python3","python"]},"install":[{"kind":"brew","label":"Install GitHub CLI","formula":"gh","bins":["gh"]}]}}
---

# GitHub + ClawHub Launcher

Search intent: `github clawhub launcher`, `release launcher`, `github repo publisher`, `clawhub publish flow`

## Goal

Turn a local public-skill project into a repeatable release flow:

- one machine-readable launch manifest
- one structural check before publish
- one rendered release-note draft
- one publish command sheet for GitHub and ClawHub

This skill is for launch preparation and execution order, not leak detection.
Use `publish-guard` first when you need a public-surface audit.

## Use This Skill When

- the user wants to publish a local repo to GitHub and ClawHub together
- the project already has a public `README.md` and a skill folder
- you want a release manifest instead of free-form publish notes
- you need a clean command plan for `gh repo create`, `gh release create`, and `clawhub publish`
- you want GitHub topics, ClawHub tags, version, slug, and changelog text kept in one place

## Quick Start

1. Initialize the launch manifest.
   - Use `python3 {baseDir}/scripts/init_launcher_manifest.py --out <json> --repo-name <repo> --skill-path skill/<slug> --slug <slug> --version 1.0.0 --name <public name> --description <one-line pitch>`.
   - Add repeatable `--topic` and `--tag` flags for GitHub and ClawHub metadata.

2. Check the public release surface.
   - Use `python3 {baseDir}/scripts/check_launcher_surface.py --manifest <json> --repo-root <repo> --out <json>`.
   - Fix missing `README.md`, `LICENSE`, `SKILL.md`, `agents/openai.yaml`, bad semver, or weak description text before publishing.

3. Render release notes.
   - Use `python3 {baseDir}/scripts/render_release_notes.py --manifest <json> --out <md>`.
   - Keep the notes short and aligned with the manifest instead of retyping the release story.

4. Render the publish command sheet.
   - Use `python3 {baseDir}/scripts/render_launcher_commands.py --manifest <json> --repo-root <repo> --out <md>`.
   - Review the generated commands before running them.

5. Publish in order.
   - Commit local changes.
   - Create or connect the GitHub repo.
   - Push `main`.
   - Create the GitHub release.
   - Publish the ClawHub package.

## Operating Rules

### Manifest rules

- Keep GitHub and ClawHub names aligned unless there is a deliberate slug mismatch.
- Keep the one-line description public-facing and product-facing.
- Use semver for the package version and GitHub release tag.

### Structure rules

- Do not publish without `README.md`, `LICENSE`, `SKILL.md`, and `agents/openai.yaml`.
- Keep the skill folder path explicit in the manifest.
- Prefer one repo for one public package unless you have a clear reason to bundle more.

### Publish rules

- Run a public-surface audit before the launcher if the repo was recently rewritten.
- Create release notes from the manifest so the story stays consistent across GitHub and ClawHub.
- Keep GitHub topics and ClawHub tags short and concrete.
- Publish from a clean branch state when possible.

## Bundled Scripts

- `scripts/init_launcher_manifest.py`
  - Create a machine-readable manifest for GitHub repo metadata, ClawHub package metadata, tags, and changelog text.
- `scripts/check_launcher_surface.py`
  - Validate the local repo structure and basic metadata before publishing.
- `scripts/render_release_notes.py`
  - Render concise release notes from the manifest.
- `scripts/render_launcher_commands.py`
  - Render a ready-to-run GitHub and ClawHub publish command sheet from the manifest.
