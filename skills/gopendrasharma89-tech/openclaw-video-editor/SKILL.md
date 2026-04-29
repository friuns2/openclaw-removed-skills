---
name: openclaw-video-editor
description: A practical video editing skill for OpenClaw built on ffmpeg, ffprobe, and python3. Provides honest, tested workflows for common edits: subtitle generation, background blur, color grading, audio normalization, scene-detected highlight reels, and watermarking. No external API calls, no hidden network behavior.
license: MIT
metadata: {"openclaw":{"requires":{"bins":["ffmpeg","ffprobe","python3"]},"primaryEnv":null,"homepage":"https://clawhub.ai/gopendrasharma89-tech/openclaw-video-editor"}}
---

# openclaw-video-editor

A focused, honest video editing skill for OpenClaw. It wraps `ffmpeg`, `ffprobe`, and small Python helpers around real, working workflows. No misleading claims, no external API calls, no hidden network behavior.

## What this skill does

This skill helps the agent run common video edits using only locally installed tools (`ffmpeg`, `ffprobe`, `python3`). It ships:

- A subtitle generator (`scripts/generate_srt.py`) that converts Whisper / Deepgram / AssemblyAI / generic word-timing JSON into `.srt`, `.vtt`, or `.ass`.
- A scene-detected highlight reel builder (`scripts/highlight_reel.py`) that picks key moments using ffmpeg scene-change scores.
- A color grading helper (`scripts/apply_lut.py`) that applies `.cube` LUT files or named filter presets.
- A dependency check (`scripts/check_deps.sh`) so the agent can confirm `ffmpeg`/`ffprobe`/`python3` exist before running any command.
- A small library of correct, tested ffmpeg one-liners below.

This skill does not perform AI-based subject masking, voice cloning, or generative video. If you want those, use a dedicated tool — this skill is intentionally limited to honest local processing.

## What this skill does not do

To set expectations clearly:

- It does not include AI background removal. The blur workflow below is a `boxblur` filter, not subject segmentation.
- It does not include a transcription model. It only formats word-level timings into subtitle files. Pair it with a transcription tool to get the JSON input.
- It does not call any external service. All commands run locally on the machine where `ffmpeg` is installed.

## Required binaries

Before running any workflow, the agent should confirm dependencies:

```bash
bash scripts/check_deps.sh
```

This returns a non-zero exit code if `ffmpeg`, `ffprobe`, or `python3` is missing. The agent should surface a clear error to the user instead of attempting commands that will fail.

## Workflows

### 1. Generate subtitles from a transcript

```bash
python3 scripts/generate_srt.py transcript.json subtitles.srt
python3 scripts/generate_srt.py transcript.json subtitles.vtt
python3 scripts/generate_srt.py transcript.json subtitles.ass --font Helvetica --fontsize 28
```

Tunable flags: `--max-chars`, `--max-words`, `--max-duration`. Useful for non-English languages where line lengths differ.

### 2. Burn subtitles into a video

```bash
ffmpeg -i input.mp4 -vf "subtitles=subtitles.srt:force_style='Alignment=2,MarginV=30,Outline=2,Shadow=1'" -c:a copy output.mp4
```

`Alignment=2` is bottom-center. Use `Alignment=8` for top-center when the bottom of the frame has important action.

### 3. Background blur (not segmentation)

A real shallow-depth-of-field look without green screen requires AI segmentation, which this skill does not include. What it does provide is honest full-frame blur, useful as a privacy filter:

```bash
ffmpeg -i input.mp4 -vf "boxblur=20:1" -c:a copy blurred.mp4
```

If you already have a binary alpha matte (`mask.mp4`, where the subject is white and the background is black, frame-aligned to `input.mp4`), you can composite a blurred background behind the original subject:

```bash
ffmpeg -i input.mp4 -i mask.mp4 \
  -filter_complex "[0:v]boxblur=20:1[bg];[0:v][1:v]alphamerge[fg];[bg][fg]overlay=format=auto" \
  -c:a copy composited.mp4
```

This only works if a per-frame alpha matte already exists. Producing the matte itself is out of scope.

### 4. Color grading

Two options.

Honest filter presets (no LUT file required):

```bash
# Warmer, more saturated look
ffmpeg -i input.mp4 -vf "eq=contrast=1.1:saturation=1.2,colorbalance=rs=0.1:gs=0.0:bs=-0.05" -c:a copy graded.mp4

# Desaturated black & white
ffmpeg -i input.mp4 -vf "hue=s=0,eq=contrast=1.2:brightness=-0.02" -c:a copy bw.mp4
```

Real LUT (when you have a `.cube` file):

```bash
python3 scripts/apply_lut.py input.mp4 lut.cube graded.mp4
# or directly:
ffmpeg -i input.mp4 -vf "lut3d=lut.cube" -c:a copy graded.mp4
```

`.cube` LUT files are the only way to get accurate cinematic looks. The filter-based "presets" above are approximations.

### 5. Audio normalization (broadcast loudness)

Two-pass loudnorm targeting EBU R128 (-23 LUFS):

```bash
# Pass 1: measure
ffmpeg -i input.mp4 -af "loudnorm=I=-23:LRA=7:tp=-2:print_format=json" -f null - 2> loudnorm.log

# Pass 2: apply with measured values
# Read the input_i / input_tp / input_lra / input_thresh / target_offset values from loudnorm.log
ffmpeg -i input.mp4 \
  -af "loudnorm=I=-23:LRA=7:tp=-2:measured_I=<input_i>:measured_TP=<input_tp>:measured_LRA=<input_lra>:measured_thresh=<input_thresh>:offset=<target_offset>:linear=true" \
  -c:v copy normalized.mp4
```

For online platforms, `-14 LUFS` is the common spec instead of `-23 LUFS`.

### 6. Highlight reel via scene detection

```bash
python3 scripts/highlight_reel.py input.mp4 highlight.mp4 --duration 30 --threshold 0.4
```

Uses `ffprobe`/`ffmpeg` scene-change scores to pick clip boundaries, then assembles a short reel up to the requested duration.

### 7. Watermark

```bash
# Bottom-right text watermark
ffmpeg -i input.mp4 -vf "drawtext=text='@yourhandle':x=w-tw-20:y=h-th-20:fontsize=24:fontcolor=white@0.7:box=1:boxcolor=black@0.4:boxborderw=8" -c:a copy watermarked.mp4

# Image overlay (logo)
ffmpeg -i input.mp4 -i logo.png -filter_complex "[0:v][1:v]overlay=W-w-20:20" -c:a copy watermarked.mp4
```

### 8. Format conversions and resizes

```bash
# 1080p H.264 with reasonable quality
ffmpeg -i input.mp4 -vf "scale=-2:1080" -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 160k output_1080p.mp4

# Vertical 9:16 crop for shorts
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy vertical.mp4
```

## Safety notes

- All workflows are local. No part of this skill calls a remote API or sends data anywhere.
- `ffmpeg` filtergraphs in this skill never use `subprocess` from inside Python with shell-evaluated user input. The Python helpers shell-quote arguments via `shlex` and reject paths containing shell metacharacters.
- The skill never modifies system configuration, environment variables, or other plugins. It only reads input files and writes output files at paths the user provides.

## Limitations

- The skill assumes inputs are valid video/audio files reachable on the local filesystem.
- Two-pass loudness normalization is described but not automated end-to-end; the agent must read the measurement output and pass values into the second pass.
- The blur compositing workflow only works when a per-frame matte already exists. Generating the matte requires a separate segmentation tool.

## License

MIT. See `LICENSE` for the full text.
