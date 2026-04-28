from __future__ import annotations

import argparse

from common import dump_text, load_json


def render_reviewer_gate_section(manifest: dict) -> str:
    gate = manifest.get("reviewer_gate") or {}
    lines = ["## Reviewer Gate", "", "```bash"]
    if gate.get("script"):
        lines.append(f"python3 {gate['script']} --repo-root . --skip-codex")
    if gate.get("pre_push_hook"):
        lines.append("git config core.hooksPath .githooks")
        lines.append("# The full gate will run on push through .githooks/pre-push")
    if not gate.get("script") and not gate.get("pre_push_hook"):
        lines.append("# no repo-local reviewer gate detected")
    lines.append("```")
    return "\n".join(lines)


def render_commands(manifest: dict) -> str:
    repo_owner = manifest.get("repo_owner", "example-org")
    repo_name = manifest["repo_name"]
    github_description = manifest.get("github_description", "")
    github_homepage = manifest.get("github_homepage", "")
    github_topics = manifest.get("github_topics", [])
    release = manifest["release"]
    topic_lines = "\n".join(
        f'gh repo edit {repo_owner}/{repo_name} --add-topic "{topic}"'
        for topic in github_topics
    ) or "# add topics if you need them"
    homepage_line = (
        f'gh repo edit {repo_owner}/{repo_name} --homepage "{github_homepage}"'
        if github_homepage
        else "# set a homepage if the project has one"
    )

    sections = [f"""# Publish Commands

{render_reviewer_gate_section(manifest)}

## GitHub

```bash
git init
git add .
git commit -m "{release['title']}"
gh repo create {repo_owner}/{repo_name} --public --source=. --remote=origin --push
gh repo edit {repo_owner}/{repo_name} --description "{github_description}"
{homepage_line}
{topic_lines}
gh release create {release['tag']} --title "{release['title']}" --notes-file dist/github-release-notes.md
```
"""]

    clawhub = manifest.get("clawhub")
    if clawhub:
        tags = clawhub.get("tags", [])
        tag_flags = f' \\\n  --tags "{",".join(tags)}"' if tags else ""
        sections.append(
            f"""## ClawHub

```bash
(cd skill/openclaw-cws-publisher && npx --yes clawhub publish "$PWD" \\
  --slug {clawhub['slug']} \\
  --name "{clawhub['name']}" \\
  --version {clawhub['version']} \\
  --changelog "{release['title']}"{tag_flags})
```
"""
        )
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render GitHub and ClawHub publish commands from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    dump_text(args.out, render_commands(load_json(args.manifest)))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
