---
name: pixcli
version: 2.3.3
description: Creative toolkit for AI agents — generate images, videos, voiceover,
  music, and sound effects, then assemble polished output via Remotion. Uses the
  pixcli CLI (published npm package "pixcli") for all generation. Remotion handles
  video assembly with 6 bundled templates.
install: npx --yes pixcli --version
env:
  - PIXCLI_API_KEY
allowed-tools:
  Bash(pixcli *),
  Bash(npx --yes pixcli *),
  Bash(npx pixcli *),
  Bash(npx --yes remotion *),
  Bash(npx remotion *),
  Bash(npm install),
  Bash(npm run verify),
  Bash(npm run typecheck),
  Bash(npm run render),
  Bash(npm run render *),
  Bash(mkdir *),
  Bash(cp *),
  Bash(cp -r *),
  Bash(ffmpeg *),
  Bash(ffprobe *),
  Read,
  Write
argument-hint: <command> [options]
metadata:
  openclaw:
    emoji: 🎨
    primaryEnv: PIXCLI_API_KEY
    primaryCredential: PIXCLI_API_KEY
    providerEnv:
      - PIXCLI_API_KEY
    requires:
      env:
        - PIXCLI_API_KEY
      anyBins:
        - node
        - npx
    homepage: https://pixcli.shellbot.sh
    tags:
      - creative
      - image
      - video
      - audio
      - remotion
      - production
---

# pixcli

Creative toolkit for AI agents. Generate images, videos, voiceover, music, and sound effects — then assemble polished output via Remotion.

**Philosophy:** The CLI handles complexity (task classification, prompt enrichment, model selection). You just describe what you want.

## Requirements

| Requirement | Value | Notes |
|---|---|---|
| **Primary credential** | `PIXCLI_API_KEY` | **Required.** Covers all capabilities (image, video, voice, music, SFX). Obtain at https://pixcli.shellbot.sh |
| **Runtime** | Node.js ≥ 18 | `node` and `npx` must be on PATH |
| **CLI package** | `pixcli` (npm) | Installed at runtime via `npx --yes pixcli`. Published package: [npmjs.com/package/pixcli](https://www.npmjs.com/package/pixcli). Source: [github.com/shellbot-ai/pixcli](https://github.com/shellbot-ai/pixcli) |
| **Remotion** (optional) | `remotion` (npm) | Only needed for video assembly from bundled templates. Installed via `npm install` inside template dirs — the templates' `package.json` declares all deps (`remotion`, `react`, `react-dom`, `@remotion/*`). No arbitrary package installs. |

### What runs at runtime and why

- **`npx --yes pixcli <command>`**: Downloads + caches the `pixcli` CLI from npm on first invocation, then runs it. All subsequent calls use the cached binary. The `--yes` flag is required in agent contexts to avoid interactive prompts. `pixcli` is an HTTP client — it sends prompts to the pixcli API (`https://pixcli.shellbot.sh/api/v1/*`), polls for completion, and downloads the resulting files. It does not execute arbitrary code.
- **`npx --yes remotion <command>`**: Same pattern for the Remotion video renderer. Only used when assembling final videos from generated assets using the bundled templates.
- **`npm install`** (no arguments): Runs inside a copied template directory to install the dependencies declared in that template's `package.json`. The agent never passes package names to `npm install` — only hydrates declared deps.
- **`ffmpeg` / `ffprobe`**: Local-only media operations (trim, merge, scale, get info). No network access.

### What does NOT run

- No bare `npx <arbitrary-package>` — only `npx pixcli` and `npx remotion`
- No `npm install <package-name>` — only bare `npm install`
- No `node <script>` — the agent never executes arbitrary JavaScript
- No `npm publish`, `npm config`, or any npm command beyond `install` and `run <script>`

## Setup

### 1. Use the CLI

AI agents should always run pixcli via `npx --yes pixcli` — it's in the scoped allowlist and requires no global install:

```bash
npx --yes pixcli image "a red fox in a forest"
```

Humans who prefer a global install for interactive terminals can optionally run `npm install -g pixcli` once outside the agent — the agent doesn't need (or have permission for) that command.

> **Important for AI agents:** `npx` prompts for confirmation before installing packages. The `--yes` flag auto-accepts. Without it, the command will hang waiting for input. Always use `npx --yes pixcli` in non-interactive contexts.

> **Always use `--json`:** All commands support `--json` which suppresses spinners and human-readable output, returning only structured JSON to stdout. This minimizes token consumption and gives you machine-parseable results. Alternatively, set `PIXCLI_JSON=1` once to enable JSON mode for all commands without passing the flag each time.

### 2. Authenticate

```bash
export PIXCLI_API_KEY="px_live_..."
```

Get your API key at https://pixcli.shellbot.sh. The key covers all capabilities: images, video, voice, music, and sound effects.

### 3. Verify

```bash
pixcli --version
pixcli image "test: a simple blue circle on white background" -o test.png
```

## Agent execution: long-running jobs

Video generation can take **1–10+ minutes** (Seedance, Kling, Veo). This matters for agents because:

- The CLI blocks synchronously while polling for completion
- Agent tool-call timeouts (typically 2–5 minutes) can kill the process before the video is ready
- Wasted tokens: spinner updates every 2 seconds don't print in `--json` mode, but the blocking wait wastes wall-clock budget

### The recommended pattern: submit → check (non-blocking)

All generation commands support `--no-wait` which **returns immediately after submission** with the `job_id`. The agent can then check status as often as needed with the non-blocking `pixcli job` command.

```bash
# 1. ALWAYS set these at the start of your session
export PIXCLI_JSON=1       # suppress spinners, return only JSON
export PIXCLI_API_KEY="px_live_..."

# 2. Submit a video job (returns in ~3-10s instead of 5-10 min)
npx --yes pixcli video "A cinematic product orbit, soft lighting" \
  --from product.png --no-wait
# Output: {"job_id":"abc123", "status":"submitted", "check_command":"pixcli job abc123 --json", ...}

# 3. Do other work, then check status (instant, non-blocking)
npx --yes pixcli job abc123
# Output: {"status":"processing", "current_step":1, "total_steps":2}

# 4. When ready, wait + download
npx --yes pixcli job abc123 --wait -o output.mp4
# Output: {"status":"completed", "files":[...], "cost":150000}
```

### When to use `--no-wait` vs default (blocking)

| Scenario | Use | Why |
|----------|-----|-----|
| **Image generation** (~10-30s) | Default (no `--no-wait`) | Fast enough that blocking is fine |
| **Video generation** (1-10min) | `--no-wait` + poll later | Avoid tool-call timeout, do parallel work |
| **Music/voice/sfx** (~10-60s) | Default usually fine | Short. Use `--no-wait` if batching many |
| **Parallel pipeline** (image → video → extend) | `--no-wait` for each video step | Submit all, poll all, download all |
| **Quick iteration/draft** | Default with `-q draft` | Draft quality is 2-5x faster |

### Token consumption

| Mode | Tokens returned | Blocking time |
|------|-----------------|---------------|
| No `--json` | 500-1000+ (spinner updates, human text) | Full wait |
| `--json` (blocking) | 50-100 (clean JSON only) | Full wait |
| `--json --no-wait` | 50-80 (submit response only) | 3-10s (submission only) |
| `pixcli job <id> --json` | 30-60 (status check) | Instant |

**Always** set `PIXCLI_JSON=1` at the start of your agent session. This single environment variable suppresses spinners, human-readable text, and progress updates for ALL pixcli commands — reducing token cost by ~90%.

### Timeout recovery

If a blocking call times out (either the agent's tool timeout or the CLI's internal 10-minute limit), the job is **still running on the server**. The JSON error output includes recovery commands:

```json
{
  "job_id": "abc123",
  "status": "timeout",
  "error": "CLI poll timeout — job still running on server",
  "check_command": "pixcli job abc123 --json",
  "wait_command": "pixcli job abc123 --wait --json"
}
```

Parse `check_command` and execute it to recover. The server never loses a job — it runs to completion regardless of whether the CLI is connected.

### Parallel video pipeline example

Generate 3 video clips simultaneously without blocking between them:

```bash
# Submit all three (each returns in ~5s)
npx --yes pixcli video "Product hero orbit" --from hero.png --no-wait -o hero.mp4
npx --yes pixcli video "Lifestyle scene, natural light" --from lifestyle.png --no-wait -o lifestyle.mp4
npx --yes pixcli video "App demo, smooth scroll" --from demo.png --no-wait -o demo.mp4

# Parse job IDs from each output
# Then poll all three:
npx --yes pixcli job $JOB_1
npx --yes pixcli job $JOB_2
npx --yes pixcli job $JOB_3

# When all are "completed", download:
npx --yes pixcli job $JOB_1 --wait -o hero.mp4
npx --yes pixcli job $JOB_2 --wait -o lifestyle.mp4
npx --yes pixcli job $JOB_3 --wait -o demo.mp4
```

This produces 3 videos in the time it takes to render 1 — ~5-8 minutes total instead of ~15-24 minutes sequential.

## Commands

### `pixcli image <prompt>` — Generate images

```bash
pixcli image "Studio product shot of wireless earbuds, soft lighting, white background" --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --ratio <ratio>` | `1:1` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3` |
| `-q, --quality <level>` | `standard` | Quality: `draft`, `standard`, `high` |
| `-t, --transparent` | `false` | Transparent background (PNG) |
| `-n, --count <number>` | `1` | Number of images (1-4) |
| `--from <path-or-url>` | — | Source image for image-to-image or reference generation (repeatable, up to 5: `--from a.png --from b.png`) |
| `--search` | `false` | Enable Google Search grounding for real-world accuracy (logos, brands, current events). Only with Nano Banana models |
| `-m, --model <model>` | auto | Specific model ID |
| `-o, --output <path>` | auto | Output file or directory |
| `--json` | `false` | Machine-readable JSON output |
| `--no-wait` | `false` | Submit and return immediately (use `pixcli job <id>` to check later) |
| `--no-enrich` | — | Skip prompt enrichment |

**Models:** `flux-pro`, `flux-dev`, `seedream-v5`, `nano-banana-pro` (Google Direct), `nano-banana-2` (Google Direct), `nano-banana-pro-fal` / `nano-banana-2-fal` (same models via fal), `nano-banana-pro-or` / `nano-banana-2-or` (via OpenRouter — requires `x-openrouter-key`), `imagen-4`, `imagen-4-fast`, `gpt-image-1` (OpenRouter). Use `pixcli models --type image` for the live list.

### `pixcli edit <prompt>` — Edit images

```bash
pixcli edit "Remove the background" -i product.jpg -o product-nobg.png --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --image <path-or-url>` | **required** | Source image (repeatable: `-i a.png -i b.png`) |
| `-q, --quality <level>` | `standard` | Quality: `draft`, `standard`, `high` |
| `-m, --model <model>` | auto | Specific model ID |
| `-o, --output <path>` | auto | Output file or directory |
| `--json` | `false` | Machine-readable JSON output |
| `--no-wait` | `false` | Submit and return immediately |
| `--no-enrich` | — | Skip prompt enrichment |

**Models:** `seedream-v5-edit`, `phota-enhance`, `rembg`, `recraft-upscale`, `aura-sr`

### `pixcli video <prompt>` — Generate video

```bash
# Image-to-video (recommended: generate still first, then animate)
pixcli video "Slow camera orbit around the product" --from product.png -o reveal.mp4 --json

# Text-to-video (generates image automatically, then animates)
pixcli video "A cat walking through a garden at sunset" -o cat.mp4 --json

# Extend an existing video
pixcli video "The cat jumps over a fence" --from cat.mp4 --extend -o cat-extended.mp4 --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `--from <path-or-url>` | — | Source image (I2V) or video (extend). **Repeatable** for multi-reference models (Seedance reference / Omni): `--from a.png --from b.png`. Single-reference models receive the first one and ignore the rest. |
| `--to <path-or-url>` | — | End image — video transitions from `--from` to `--to` (Kling/PixVerse transition models) |
| `--negative <prompt>` | — | Negative prompt describing what to avoid |
| `--audio` | `false` | Enable native audio generation (BGM, SFX, dialogue) on supported models |
| `-d, --duration <seconds>` | `5` | Duration: 1-15 seconds |
| `-r, --ratio <ratio>` | `16:9` | Aspect ratio: `16:9`, `9:16`, `1:1`, `4:3`, `3:4` |
| `-q, --quality <level>` | `standard` | Quality: `draft`, `standard`, `high` |
| `-m, --model <model>` | auto | Specific model ID |
| `-o, --output <path>` | auto | Output file (.mp4) |
| `--json` | `false` | Machine-readable JSON output |
| `--no-wait` | `false` | Submit and return immediately (recommended for video — avoids 10min blocking) |
| `--extend` | `false` | Extend the source video instead of I2V |
| `--storyboard` | `false` | Generate a still frame with Nano Banana first, then animate it. Opt-in for tight visual control over the opening frame (brand shots, hero compositions). Adds ~5s + one extra credit. Default text-to-video is single-step T2V. |

**Models — fal backend**: `veo31-lite-i2v` (default I2V, Veo 3.1 Lite), `veo31-lite-t2v` (default T2V, Veo 3.1 Fast), `veo31-lite-transition` (start→end frame), `kling-o3-pro-i2v` (cinematic, best quality), `kling-o3-pro-t2v`, `kling-o3-standard-i2v`, `kling-o3-standard-t2v`, `kling-v3-pro-i2v`, `veo3-i2v` (premium, native audio + lipsync), `veo3-t2v`, `pixverse-v6-i2v` / `-t2v` / `-transition` / `-extend` (stylized, audio, multi-clip), `ltx-t2v` (budget T2V), `ltx-extend-video` (budget extension, native audio), `wan-v2-i2v` (cheap motion), `minimax-i2v` (fast, avoid for faces), `grok-extend-video`

**Models — muapi backend (Seedance 2 family)**: `seedance-2-t2v` / `-fast`, `seedance-2-i2v` / `-fast`, `seedance-2-omni` / `-fast` (multimodal: up to 9 image refs + 3 audio refs via `@image1..@image9` / `@audio1..@audio3`), `seedance-2-first-last-frame` / `-fast`. **VIP / 2K tier** (priority routing, 2K resolution, ~50% premium): `seedance-2-vip-t2v` / `-fast`, `seedance-2-vip-i2v` / `-fast`, `seedance-2-vip-first-last-frame` / `-fast`, `seedance-2-vip-omni` / `-fast`. Routing is automatic: mention "seedance" / "bytedance" / "doubao" in the prompt, use the `@image1`/`@audio1`/`@character:id` grammar, or pass `--quality draft` (routes to `-fast`). See `references/seedance-playbook.md` for the full prompt playbook.

**Opinionated approach:** Always generate a still first with `pixcli image`, review it, then animate with `pixcli video --from`. This gives you control over the starting frame.

**Logo animations (brand reveals / intros / bumpers):** pass `--from logo.png` and mention both "logo"/"brand" AND an animation intent ("reveal", "intro", "bumper", "animate") in the prompt — the API auto-detects this and swaps in a specialist Motion Logo Director that emits a 6-stage timeline with sound design, music, and optional voiceover. See `references/seedance-logo-motion.md` for the full playbook.

### Video prompting — the core formula

Every video prompt should follow this structure:

```
Subject → Action → Environment → Camera → Style → Constraints
```

**Target 60–100 words.** Shorter = vague. Longer = conflicting instructions that degrade coherence.

| # | Element | Rule | Good example |
|---|---------|------|--------------|
| 1 | **Subject** | Describe visual features explicitly | *A woman in her 30s, short black hair, red wool coat* |
| 2 | **Action** | Concrete verbs + quantify intensity | *walks briskly* — not *walks* |
| 3 | **Environment** | Lighting + atmosphere + time of day | *rain-slicked Tokyo street at night, neon reflections on wet pavement* |
| 4 | **Camera** | **One instruction only** — never chain moves | *slow push-in* — never *push then pan then orbit* |
| 5 | **Style** | Specific aesthetics only | *cinematic, shallow depth of field, film grain* |
| 6 | **Constraints** | Say what you want, not what you don't | *smooth motion, stable framing* |

**The 10 rules that always apply:**

1. **One camera move per shot. Always.** Combining causes jitter.
2. **Separate subject motion from camera motion.** ✅ "The dancer spins. Camera holds fixed." ❌ "Spinning camera around a dancing person."
3. **For I2V, only describe what changes** — the image carries composition and identity. Add `Preserve composition and colors.`
4. **Use physical verbs** — `melt`, `fracture`, `snap open` > `becomes` / `transforms`.
5. **Lighting is your biggest quality lever** — always name the light (`golden hour`, `rim light`, `natural window light`, `neon`, `soft diffused`, `dramatic stage lighting`).
6. **Write on a timeline for 10s+ clips** — break into 3–5 time-coded beats: `[0s–3s]:`, `[3s–7s]:`, etc.
7. **Every asset gets a job** — if a file has no role, it's noise. Be explicit about what each `--from` / `--to` does.
8. **Put negatives in `--negative`**, not in the main prompt.
9. **For video extend, `-d` is the NEW duration**, not the total.
10. **Draft before hero** — always iterate with `-q draft` (auto-routes to 480p Seedance or ltx-t2v) before burning credits on a full render.

Read `references/seedance-playbook.md` for the complete playbook — camera movement catalog, lighting table, timeline prompting templates, multimodal role assignment, and 10+ ready-to-paste command recipes.

### `pixcli voice <text>` — Text-to-speech

```bash
pixcli voice "Welcome to the future of productivity." -o voiceover.mp3 --json
pixcli voice "Bienvenidos al futuro." --voice Sarah --language es -o vo-spanish.mp3 --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `--voice <name>` | `Rachel` | Voice preset: Rachel, Aria, Roger, Sarah, Laura, Charlie, George, Callum, River, Liam, Charlotte, Alice, Matilda, Will, Jessica, Eric, Chris, Brian, Daniel, Lily, Bill |
| `--language <code>` | auto | ISO 639-1 language code (en, es, fr, de, ja, etc.) |
| `-o, --output <path>` | auto | Output file (.mp3) |
| `--json` | `false` | Machine-readable JSON output |

### `pixcli music <prompt>` — Generate music

```bash
pixcli music "Subtle ambient electronic, minimal beats, corporate technology feel" -d 45 -o bg-music.mp3 --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --duration <seconds>` | `30` | Duration: 3-120 seconds |
| `-o, --output <path>` | auto | Output file (.mp3) |
| `--json` | `false` | Machine-readable JSON output |

### `pixcli sfx <prompt>` — Generate sound effects

```bash
pixcli sfx "Smooth cinematic whoosh transition" -d 1.5 -o whoosh.mp3 --json
pixcli sfx "Soft digital click, subtle UI interaction" -d 0.5 -o click.mp3 --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --duration <seconds>` | `5` | Duration: 0.5-22 seconds |
| `-o, --output <path>` | auto | Output file (.mp3) |
| `--json` | `false` | Machine-readable JSON output |

### `pixcli models` — List available models

```bash
# Every model, grouped by type
pixcli models --json

# Only Seedance
pixcli models --search seedance --json

# Only video models routed through muapi
pixcli models --type video --backend muapi --json
```

| Option | Description |
|--------|-------------|
| `-t, --type <kind>` | `image` \| `video` \| `audio` |
| `-b, --backend <name>` | `fal` \| `muapi` \| `google-direct` \| `openrouter` |
| `-p, --provider <name>` | Upstream provider: `fal` \| `google` \| `bytedance` \| `elevenlabs` \| `openai` \| `xai` \| `muapi` |
| `-c, --capability <cap>` | `text-to-video` \| `image-to-video` \| `edit` \| `upscale` \| `bg-removal` \| `lipsync` \| `music` \| `sound-effects` \| `text-to-speech` \| `video-extend` \| `enhance` |
| `-s, --search <term>` | Substring match on id, name, or strengths |
| `--json` | Machine-readable JSON output |

Backs onto `GET /api/v1/models?type=...&backend=...&search=...`. Use this to discover model ids before passing them to `-m` on any generation command.

### `pixcli job <id>` — Check job status and download results

```bash
# Check status of a job
pixcli job abc123 --json

# Wait for completion and download
pixcli job abc123 --wait -o output.mp4 --json
```

| Option | Default | Description |
|--------|---------|-------------|
| `--wait` | `false` | Wait for the job to complete before returning |
| `-o, --output <path>` | auto | Output file path for downloaded result |
| `--json` | `false` | Machine-readable JSON output |

**Use case:** Recover timed-out jobs. Video generation can take 5-8 minutes — if the CLI times out, it prints the job ID and a recovery command. Run `pixcli job <id> --wait` to pick up where you left off.

### Global options

| Option | Description |
|--------|-------------|
| `--key <api_key>` | Override `PIXCLI_API_KEY` env var |
| `--api-url <url>` | Override API URL (default: `https://pixcli.shellbot.sh`) |
| `--json` | Machine-readable JSON output (or set `PIXCLI_JSON=1` once for all commands) |
| `--no-wait` | Submit the job and return immediately with the `job_id` — don't poll for completion. Available on: `image`, `edit`, `video`, `voice`, `music`, `sfx` |
| `--version` | Show CLI version |
| `--help` | Show help |

Read `references/command-reference.md` for the full parameter reference.

---

## Opinionated creative workflow

### The full production pipeline

1. **Generate** scene stills with `pixcli image` — use `-n 4` for variations, pick the best. Use `--search` for real-world accuracy (correct logos, current brands). Use `--from` with multiple images to blend references
2. **Edit** heroes with `pixcli edit` — upscale, remove backgrounds, enhance
3. **Animate** 2-3 hero stills with `pixcli video --from` — cinematic motion for key moments
4. **Generate** voiceover with `pixcli voice` — one file per scene
5. **Generate** background music with `pixcli music` — one track for the full composition
6. **Generate** sound effects with `pixcli sfx` — transition whooshes, UI sounds (use sparingly)
7. **Assemble** everything in Remotion — timing, text, transitions, branding, audio mix
8. **Render** final video with `npx remotion render`

### When to use AI video vs Remotion

**Use `pixcli video` for:**
- Hero moments: product reveals, cinematic openings, emotional beats (3-8s clips)
- Organic motion that's hard to code: water, fire, fabric, hair, camera orbits
- Image-to-video: animate a still into a living scene
- Transition inserts: short clips between Remotion scenes

**Use Remotion for:**
- Text animations, captions, kinetic typography
- Precise timing synced to voiceover
- Brand overlays, logos, consistent color grading
- Data visualizations, metric counters, charts
- Scene transitions (cuts, wipes, dissolves — deterministic)
- Final assembly: compositing AI video clips + stills + audio + text

**The ideal combined workflow:**
1. Generate scene stills with `pixcli image` (consistency via shared style prompts)
2. Animate 2-3 hero stills with `pixcli video --from` (cinematic motion)
3. Generate voiceover + music + SFX
4. Assemble everything in Remotion (timing, text, transitions, audio mix)

### Audio layering strategy

- **Voiceover** at volume 1.0 — clear, intelligible, primary channel
- **Music** at 0.15-0.25 — duck under voiceover, never compete
- **SFX** sparse and purposeful — only when they reinforce movement
- Avoid dense music during problem framing

### Quality tiers

- **`draft`** — Fast iteration, concepting, throwaway tests
- **`standard`** — Good for most production work (default)
- **`high`** — Hero shots, final delivery assets

---

## ffmpeg local editing

Use ffmpeg for quick video/audio edits without a full Remotion project. These run locally — no API calls needed.

### Video operations

```bash
# Trim video (extract 5 seconds starting at 2s)
ffmpeg -i input.mp4 -ss 00:00:02 -to 00:00:07 -c copy trimmed.mp4

# Split video at a timestamp
ffmpeg -i input.mp4 -t 5 -c copy first-half.mp4
ffmpeg -i input.mp4 -ss 5 -c copy second-half.mp4

# Merge videos (create filelist.txt first)
echo "file 'clip1.mp4'" > filelist.txt
echo "file 'clip2.mp4'" >> filelist.txt
ffmpeg -f concat -safe 0 -i filelist.txt -c copy merged.mp4

# Scale video to 1080p
ffmpeg -i input.mp4 -vf "scale=1920:1080" -c:a copy scaled.mp4
```

### Audio operations

```bash
# Add audio track to video
ffmpeg -i video.mp4 -i music.mp3 -c:v copy -c:a aac -shortest output.mp4

# Replace audio track
ffmpeg -i video.mp4 -i new-audio.mp3 -c:v copy -c:a aac -map 0:v -map 1:a output.mp4

# Mix voiceover + music (music ducked to 20%)
ffmpeg -i voiceover.mp3 -i music.mp3 -filter_complex "[1:a]volume=0.2[music];[0:a][music]amix=inputs=2:duration=longest" mixed.mp3

# Extract audio from video
ffmpeg -i video.mp4 -vn -acodec copy audio.aac

# Get media info
ffprobe -v quiet -print_format json -show_streams input.mp4
```

---

## Remotion video production

Remotion is the source of truth for timing, layout, animation, and render. Use `pixcli` to generate the visual and audio assets, then assemble everything in Remotion.

### Bootstrapping a Remotion project

```bash
cp -r assets/templates/cinematic-product-16x9 ./my-video
cd ./my-video && npm install
npx remotion studio     # Preview
npx remotion render src/index.ts MainComposition out/video.mp4  # Render
```

### Templates

| Template | Best for | Aspect |
|----------|----------|--------|
| `aida-classic-16x9` | Product marketing (AIDA framework) | 1920x1080 |
| `cinematic-product-16x9` | Premium product launches | 1920x1080 |
| `saas-metrics-16x9` | B2B SaaS, dashboard metrics | 1920x1080 |
| `mobile-ugc-9x16` | Reels, TikTok, Stories | 1080x1920 |
| `blank-16x9` | Custom projects | 1920x1080 |
| `explainer-16x9` | How-it-works, tutorials | 1920x1080 |

### Integrating AI video clips in Remotion

Use `OffthreadVideo` for AI-generated clips inside Remotion compositions:

```tsx
import { OffthreadVideo, Sequence, Audio, Img, staticFile } from "remotion";

// AI video clip as a hero moment
<Sequence from={0} durationInFrames={150}>
  <OffthreadVideo src={staticFile("assets/hero-reveal.mp4")} />
</Sequence>

// AI-generated still as background
<Sequence from={150} durationInFrames={120}>
  <Img src={staticFile("assets/scene-solution.png")} style={{ width: "100%", height: "100%" }} />
</Sequence>

// Voiceover + music
<Audio src={staticFile("audio/voiceover.mp3")} volume={1} />
<Audio src={staticFile("audio/music.mp3")} volume={0.2} />
```

### Remotion principles

- Keep all Remotion packages on the same pinned version
- Transitions: 8-18 frames, purposeful (not decorative)
- Load fonts explicitly with `@remotion/google-fonts`
- Always run `npm run verify` before `npm run render`
- Load reference rules from `references/remotion-rules/` as needed

Read `references/remotion-playbook.md` for detailed Remotion implementation guidance.

---

## Output convention

- `pixcli` downloads generated files to the current directory (or path specified with `-o`)
- Use `--json` for machine-readable output (pipe to `jq` or parse in scripts)
- All operations are synchronous from the CLI perspective (the CLI handles async polling internally)
- Video jobs may take 1-8 minutes (the CLI shows progress). If a job times out, use `pixcli job <id> --wait` to recover

## References

### Creative guidance
- `references/command-reference.md` — Full parameter docs for all pixcli commands
- `references/creative-guidelines.md` — Quality standards for productions
- `references/prompt-cookbook.md` — Proven prompt patterns for every task
- `references/seedance-playbook.md` — Video prompting masterclass (Seedance 2 + all video models): 6-element formula, camera catalog, lighting table, timeline prompting, multimodal role assignment, 10+ ready-to-paste recipes
- `references/seedance-logo-motion.md` — **Logo animation specialist playbook.** Use when the user provides a logo image + asks for a brand reveal / intro / bumper. Auto-activated by the API when `--from logo.png` is combined with logo+motion keywords.
- `references/workflow-recipes.md` — End-to-end recipe examples
- `references/ancillary-assets.md` — Asset generation strategy for Remotion scenes

### Remotion
- `references/remotion-playbook.md` — Remotion implementation guide
- `references/template-showcase.md` — Template selector guide
- `references/remotion-rules-index.md` — Index of 30+ Remotion rule files
- `references/remotion-rules/` — Detailed rules (animations, audio, text, transitions, etc.)

### Templates
- `assets/templates/aida-classic-16x9/`
- `assets/templates/cinematic-product-16x9/`
- `assets/templates/saas-metrics-16x9/`
- `assets/templates/mobile-ugc-9x16/`
- `assets/templates/blank-16x9/`
- `assets/templates/explainer-16x9/`
