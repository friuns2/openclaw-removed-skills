---
name: sota-agent
description: SOTA Agent is a public ClawHub SOTA-campaign skill for CV and DS work. Use it when the user says "sota agent", "state of the art benchmark scouting", or wants SOTA-focused CV and data-science campaigns across OpenClaw notebooks, GUI-heavy workflows, and GPU VMs.
version: 1.4.2
homepage: https://zack-dev-cm.github.io/
user-invocable: true
metadata: {"openclaw":{"homepage":"https://zack-dev-cm.github.io/","skillKey":"sota-agent","requires":{"anyBins":["python3","python"]}}}
---

# SOTA Agent

Search intent: `sota agent`, `state of the art benchmark scouting`, `cv benchmark campaign`, `gpu vm research workflow`

## Goal

Turn a vague "beat the benchmark" request into a disciplined campaign:

- fixed target metric and split
- explicit literature and leaderboard snapshot
- bounded reproduction plan
- explicit browser, notebook, or VM execution lane
- GUI evidence when notebook or browser state matters
- ablations that answer one question at a time
- promotion only when the claim survives review

This skill is the frontier-planning and candidate-selection layer.
For browser evidence, VM execution, and promotion artifacts, pair it with
`data-science-cv-repro-lab` instead of letting the campaign drift into ad hoc runs.

## Use This Skill When

- the user wants a CV or DS system pushed toward state-of-the-art results
- the task involves reproducing or surpassing recent papers
- the workflow needs paper triage, leaderboard tracking, or claim review
- the workflow includes OpenClaw, Colab, Kaggle, browser-only notebook actions, or GUI-heavy pages
- the user needs experiment management across browser research, notebooks, local runs, and long GPU jobs
- the user wants GPU VM or notebook watchdog logic, artifact pulls, or browser evidence for a SOTA candidate
- the question is whether a candidate is a real SOTA step or only noise, leakage, or benchmark overfitting

If the campaign includes serious execution or release review, use this skill to choose and rank candidates,
then use `data-science-cv-repro-lab` as the execution lane.

## Quick Start

1. Freeze the claim target before touching recipes.
   - Name the task, dataset, metric, split, and target score.
   - Name the current trusted baseline.
   - Name the claim threshold for "match", "beat", or "not enough".

2. Initialize the campaign records immediately.
   - Use `python3 {baseDir}/scripts/init_sota_campaign.py --root <dir> --campaign-id <id> --title <title>`.
   - Use `python3 {baseDir}/scripts/init_sota_leaderboard_snapshot.py --out <json> --task <task> --dataset <dataset> --metric <metric> --split <split>`.
   - Use `python3 {baseDir}/scripts/init_sota_paper_triage.py --out <json> --campaign-id <id> --task <task>`.
   - Use `python3 {baseDir}/scripts/init_sota_program.py --out <json> --campaign-id <id> --task <task> --dataset <dataset> --metric <metric> --split <split>` when you need one machine-readable benchmark, rerun, delegation, and auth plan.
   - Use `python3 {baseDir}/scripts/init_sota_candidate_card.py --out <json> --candidate-id <id> --campaign-id <id> --objective <goal>`.
   - If execution review depends on synced QA runs, runtime sweeps, or benchmark panels, store the paired `data-science-cv-repro-lab` review dashboard path in the program and candidate records before the claim review starts.
   - If the execution path depends on a real browser or notebook UI, use `python3 {baseDir}/scripts/init_sota_browser_run_card.py --out <json> --target-url <url>`.
   - If the browser or notebook surface needs manual or visual QA, use `python3 {baseDir}/scripts/init_sota_validation_scorecard.py --out <json> --scorecard-id <id> --surface <surface>`.
   - If a Colab, Kaggle, or notebook export bundle matters, use `python3 {baseDir}/scripts/init_sota_artifact_manifest.py --out <json> --bundle-root <dir>`.
   - If a long GPU VM run is involved, use `python3 {baseDir}/scripts/init_sota_vm_bootstrap_manifest.py --out <json> --output-root <run_root> --model-family <name> --command python train.py --epochs 40`.

3. Separate the campaign roles even if one agent performs all of them.
   - Scout: papers, leaderboards, repos, and benchmark rules.
   - Reproducer: baseline and top-paper reproduction.
   - Ablator: controlled change sets and compute allocation.
   - Reviewer: contamination, metric drift, and claim integrity.
   - Promoter: final claim or hold decision.
   - Keep the benchmark definition and final claim wording fixed.
   - Use bounded scouting and review lanes for literature triage, repo inspection, per-paper extraction, and hard-case review.
   - For repeated audits, batch over a manifest or CSV instead of free-form context accumulation.

4. Pick the execution lane explicitly.
   - Browser or GUI lane: OpenClaw, Colab, Kaggle, or another real browser session when notebook UI state matters.
   - Colab or notebook GPU lane: runtime selection, smoke validation, artifact export, and browser evidence.
   - GPU VM lane: long runs with heartbeats, watchdogs, sync, and auto-stop policy.
   - Local lane: cheap falsification, tiny reruns, and artifact review.

5. Keep file writes inside one campaign workspace.
   - Create one dedicated campaign root and keep every `--out`, `--bundle-root`, and `--output-root` path under it.
   - Do not point the bundled scripts at unrelated home-directory or system paths.
   - Treat `scripts/sota_public_safety.py` as the canonical public-redaction layer for URLs, refs, and paths.

6. Work the SOTA ladder in order.
   - Freeze the benchmark definition and auth rule before using more compute.
   - Reproduce the trusted baseline first.
   - Reproduce one relevant reference result or a close public checkpoint.
   - Build a hypothesis backlog from literature gaps, not vibes.
   - Run narrow ablations before broad recipe churn.
   - Stress the best candidate on the fixed review surfaces.

7. Claim only on full-surface wins.
   - Fixed benchmark score
   - Reproduced baseline delta
   - Compute or cost context
   - Browser or GUI evidence if that lane mattered
   - Failure-case review
   - Exact evidence bundle
   - Render the final review with `python3 {baseDir}/scripts/render_sota_claim_summary.py --candidate-card <json> --out <md>`.

## Operating Rules

### Campaign rules

- One campaign has one target benchmark contract.
- Do not let the target metric or split drift midstream.
- Keep a short hypothesis backlog and kill low-information ideas quickly.
- Record why each experiment exists before running it.

### Codex multi-agent rules

- Main thread owns the benchmark contract, stop conditions, and final claim decision.
- Subagents should do bounded work only: scout, reproduce, ablate, or review.
- Do not let one exploratory thread silently rewrite the campaign contract.
- For repeated claim checks or literature extraction, prefer manifest-driven fanout over conversational drift.

### Literature rules

- Read only the papers or repos that change the candidate plan.
- Extract the minimum useful fields: task, metric, split, data, compute, architecture, augmentations, training tricks, and caveats.
- Prefer a reproduced strong baseline over copying five tricks from five papers without control.
- Do not treat leaderboard rows as ground truth without checking task definition and split rules.

### Ablation rules

- Change one meaningful variable at a time when the goal is causal understanding.
- If several knobs move together, label the run as a package change, not an ablation.
- Keep one canonical baseline recipe alive for comparison.
- Require the first winning candidate to survive at least one rerun or adjacent-seed check before escalating the claim.

### Compute rules

- Spend cheap compute on reproduction and short falsification first.
- Do not push a long run unless the hypothesis would matter if it wins.
- Record training cost, wall time, and hardware for every serious candidate.
- Cut branches that cannot plausibly clear the target with the remaining budget.

### OAuth and auth rules

- Use ChatGPT or Codex OAuth-backed sessions as the default and preferred path.
- Prefer Codex multi-agent or app-server workflows over orchestrators that require paid API keys.
- Do not require or recommend `OPENAI_API_KEY`, other vendor API keys, or paid inference APIs as the default campaign runtime path.
- If a third-party framework only works through paid API keys, treat it as reference material unless it can run fully through local tools and OAuth-backed Codex sessions.

### OpenClaw browser rules

- Use OpenClaw for public papers, leaderboards, docs, notebook-only steps, and GUI-heavy flows when the browser lane adds evidence.
- Prefer direct public URLs over uploads or private sessions.
- Capture leaderboard, notebook, or GUI evidence as notes, screenshots, and exact URLs when they are part of the claim path.
- Fail hard on dead browser attach, missing notebook readiness, or unavailable requested model or runtime mode.
- Treat screenshots and GUI evidence as supporting artifacts, not the claim itself.
- Do not use browser-only summaries as the claim itself; claims still require benchmark artifacts.

### Colab and notebook GPU rules

- Select the accelerator explicitly before running expensive cells.
- Run a smoke cell that proves imports, runtime, data mounts, and export paths all work.
- Keep one stable export root and pull the artifact manifest plus at least one preview back locally.
- Add the browser run card and validation scorecard when the notebook GUI is part of the evaluation story.

### GPU VM rules

- Create a named run root before launch.
- Write a machine-readable VM bootstrap manifest before long runs.
- Run long jobs under a heartbeat, session, or supervisor so liveness is explicit.
- Sync metrics, summaries, and checkpoints back to a trusted store on a schedule.
- Do not promote directly from live VM state; promote from synced artifacts and review evidence.

### Claim safety rules

- No SOTA claim without a fixed metric, split, and baseline.
- No SOTA claim on a contaminated benchmark or hidden train-on-test path.
- If the execution story depends on a dashboard or synced review surface, keep the dashboard path, source audit, and leakage audit in the claim packet.
- If a candidate wins only on one slice while regressing important surfaces, hold it.
- Report uncertainty honestly: "best internal result so far" is not the same as "new SOTA".
- Small deltas need rerun or adjacent-seed support before they become claim language.

## References

Read only the reference that matches the task:

- `references/sota-campaign-playbook.md`
  - Full campaign structure, role separation, and stop conditions.
- `references/sota-program-rules.md`
  - Rules for queues, stage discipline, ablations, and promotion gating.
- `references/campaign-harness-and-oauth-stack.md`
  - What to reuse from Codex subagents, harness engineering, OpenEvolve, Symphony, Paperclip, and OptiLLM under an OAuth-only campaign rule.
- `references/benchmark-discipline.md`
  - How to avoid contamination, metric drift, and invalid comparisons.
- `references/paper-triage.md`
  - How to filter papers and extract only decision-relevant details.
- `references/openclaw-research-lane.md`
  - How to use OpenClaw productively for public literature and leaderboard work.
- `references/openclaw-browser-lane.md`
  - How to run GUI-heavy notebook, browser, and screenshot-based execution safely.
- `references/colab-vm-operations.md`
  - How to manage Colab, Kaggle, and GPU VM execution lanes with smoke tests and artifact discipline.
- `references/claim-safety.md`
  - Review rules for whether a candidate deserves a SOTA claim at all.
- `references/public-safety.md`
  - Publication review rules for secrets, private refs, and raw notebook paths.

## Bundled Scripts

- `scripts/sota_public_safety.py`
  - Pure local helpers for path, URL, ref, env, and command redaction. No network I/O or subprocess execution.
- `scripts/init_sota_campaign.py`
  - Create a reusable campaign folder with benchmark, program, agent, research, leaderboard, plan, ablation, evidence, and claim files.
- `scripts/init_sota_program.py`
  - Create a machine-readable program record with the fixed benchmark, baselines, rerun policy, bounded subagent roles, and OAuth rules.
- `scripts/init_sota_leaderboard_snapshot.py`
  - Create a machine-readable snapshot of the target benchmark contract and current reference scores.
- `scripts/init_sota_paper_triage.py`
  - Create a machine-readable literature queue for paper screening and extraction.
- `scripts/init_sota_browser_run_card.py`
  - Create a sanitized browser evidence record for OpenClaw, Colab, Kaggle, or other notebook UI runs.
- `scripts/init_sota_validation_scorecard.py`
  - Create a machine-readable GUI or notebook validation scorecard when visible state matters to the campaign.
- `scripts/init_sota_artifact_manifest.py`
  - Create a machine-readable export-bundle manifest for notebook or VM artifact pulls with redacted public path metadata.
- `scripts/init_sota_candidate_card.py`
  - Create a machine-readable card for a serious candidate, its execution lane, auth mode, and claim state.
- `scripts/init_sota_candidate.py`
  - Create a machine-readable candidate record with change set, risks, and redacted public artifact refs.
- `scripts/init_sota_ablation_queue.py`
  - Create a focused ablation queue for one candidate family.
- `scripts/init_sota_vm_bootstrap_manifest.py`
  - Create a machine-readable bootstrap manifest for long GPU VM or cluster runs with public-release redaction.
- `scripts/update_sota_scoreboard.py`
  - Refresh a ranked scoreboard for a fixed metric and goal direction.
- `scripts/init_sota_review_packet.py`
  - Join the core artifacts for a promotion, hold, or cut decision.
- `scripts/render_sota_claim_summary.py`
  - Render a concise markdown review from the machine-readable candidate card.
- `scripts/render_sota_program_summary.py`
  - Render a concise markdown summary from the program, candidate, scoreboard, and review packet.
