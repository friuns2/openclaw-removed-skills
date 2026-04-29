---
name: openclaw-cws-publisher
description: OpenClaw CWS Publisher is a public ClawHub Chrome Web Store publisher skill. Use it when the user says "chrome web store publisher", "extension release publisher", "CWS publisher", or wants to package a Chrome extension, scan tracked files for public-surface leaks, and render GitHub or ClawHub release metadata with explicit tags.
version: 0.2.4
homepage: https://github.com/zack-dev-cm/openclaw-cws-publisher
license: MIT
user-invocable: true
metadata: {"openclaw":{"homepage":"https://github.com/zack-dev-cm/openclaw-cws-publisher","skillKey":"openclaw-cws-publisher","requires":{"bins":["git","gh","npx"],"anyBins":["python3","python"]},"install":[{"kind":"brew","label":"Install GitHub CLI","formula":"gh","bins":["gh"]}]}}
---

# OpenClaw CWS Publisher

Search intent: `chrome web store publisher`, `extension release publisher`, `cws publisher`, `chrome extension publish`

## Goal

Prepare a Chrome extension repo for release with less metadata drift:

- package the extension
- scan tracked files for obvious leak risks
- detect repo-local reviewer gates
- generate GitHub metadata
- generate optional ClawHub metadata and explicit tags
- render reproducible publish commands

## Use This Skill When

- the user wants a Chrome extension repo prepared for GitHub release
- the user wants ClawHub tags and GitHub topics kept in sync
- the user wants a leakage check before public release
- the user already has a specific repo path to release

## Operating Order

1. Build the extension ZIP.
   - `python3 {baseDir}/scripts/build_extension_zip.py --extension-dir <repo>/extension --out <zip>`
2. Scan tracked files for obvious publish leaks.
   - `python3 {baseDir}/scripts/scan_publish_surface.py --root <repo> --json-out <json> --markdown-out <md>`
3. Generate launch metadata.
   - `python3 {baseDir}/scripts/generate_launch_manifest.py --repo-root <repo> --owner <github-owner> --public-site-base <https://public-site.example/> --out <json>`
   - If you already export `CWS_PUBLIC_SITE_BASE`, you can omit `--public-site-base` and the script will reuse that public reviewer-facing base.
4. Render publish commands.
   - `python3 {baseDir}/scripts/render_publish_commands.py --manifest <json> --out <md>`

## Rules

- Operate on the repo path the user named, not on arbitrary sibling directories.
- Inspect the ZIP intended for upload, not only the source tree, before calling a Chrome Web Store package ready.
- Do not publish when the leak scan has unresolved findings.
- Do not publish when the target repo has a reviewer gate and it fails.
- Keep GitHub topics and ClawHub tags explicit in the generated manifest.
- Use a dedicated public site base for support, privacy-policy, and reviewer-instructions links when the extension has one.
- If a Chrome Web Store draft is already pending review, do not recommend canceling or replacing it unless a verified acceptance blocker exists.
- Do not assume generated artifacts should be committed.

## Bundled Scripts

- `scripts/build_extension_zip.py`
- `scripts/scan_publish_surface.py`
- `scripts/generate_launch_manifest.py`
- `scripts/render_publish_commands.py`
