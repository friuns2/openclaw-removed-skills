# Theme CSS

## Theme Resolution Order

When a theme name is specified (via `--theme` flag or frontmatter `theme:`), resolve it in this order:

1. **Custom theme directory:** Check `themes/[theme-name]/` (relative to skill directory, i.e. `~/.claude/skills/report-creator/themes/`)
   - If `themes/[theme-name]/theme.css` exists → use it as the theme CSS (skip step 2 below)
   - If `themes/[theme-name]/reference.md` exists (and no `theme.css`) → read it, derive `:root` CSS variables from the color/typography/layout sections, generate a `:root { ... }` block
   - If both exist → `theme.css` takes priority; `reference.md` is ignored
2. **Built-in theme:** Fall back to `templates/themes/[theme-name].css`
3. **Unknown theme:** Warn the user, fall back to `corporate-blue`

Directories starting with `_` in `themes/` are ignored (example/template directories).

## CSS Assembly Order (Built-in Themes)

For built-in themes, assemble CSS in `<style>` in this order:
1. Read `templates/themes/[theme-name].css` — **split at `/* === POST-SHARED OVERRIDE */` marker**
2. Embed everything **before** the marker (variables + base styles)
3. Embed `templates/themes/shared.css` in full
4. From `[theme-name].css` — embed everything **after** the marker (overrides + enhancements)
5. If `theme_overrides` is set in frontmatter, append `:root { ... }` override block last

**Critical:** Do NOT load the entire theme file in one block. The POST-SHARED section must load AFTER shared.css to properly override shared defaults.

## CSS Assembly Order (Custom Themes)

For custom themes, assemble CSS in `<style>` in this order:
1. Read `templates/themes/minimal.css` as the **base** — embed everything before `/* === POST-SHARED OVERRIDE */`
2. Read `templates/themes/shared.css` — embed in full
3. From `minimal.css` — embed everything after `/* === POST-SHARED OVERRIDE */` (if present)
4. Append the custom theme's `:root { ... }` block (from `theme.css` or derived from `reference.md`) — this overrides the base variables
5. If `theme_overrides` is set in frontmatter, append that last

Using `minimal` as the base ensures all shared components render correctly even if the custom theme only defines a subset of variables.

## Built-in Theme Names

`corporate-blue`, `minimal`, `dark-tech`, `dark-board`, `data-story`, `newspaper`, `regular-lumen`

**Themes with POST-SHARED OVERRIDE sections:** `dark-board`, `data-story`, `newspaper`, `regular-lumen`

**Special code block note:** `dark-tech` and `dark-board` use `github-dark.min.css` instead of `github.min.css` for highlight.js.