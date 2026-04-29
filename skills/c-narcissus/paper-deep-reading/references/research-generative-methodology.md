# Research-Generative Methodology

Use this reference when the user wants more than grounded verification.
Its goal is to turn a paper reading into a **research-generation exercise** while keeping every important statement source-aware.

The core move is:

> Read the paper as a hidden design path.

## 1. Research Equation

Compress the paper into:

`old success + broken assumption + hard setting + borrowed tool + surrogate mechanism`

Useful questions:

- What important paradigm already worked?
- What hidden assumption made it work?
- In what realistic setting does that assumption fail?
- What neighboring method almost transfers?
- What missing mechanism `Y` blocks direct transfer?
- What surrogate `Z` does the paper build instead?

## 2. How the Direction Was Likely Found

Use evidence-backed phrasing:

- "The authors likely noticed that ..."
- "A plausible thinking path is ..."
- "The setup suggests ..."

Try to reconstruct:

- starting dissatisfaction
- tempting transferred method
- blocking constraint
- replacement logic

## 3. How the Story Was Built

Look for:

`challenge -> failure mode -> design principle -> module -> ablation`

Strong papers often create a loop instead of a bag of tricks.
Explain whether one module creates the resource that the next module needs.

## 4. Method Deep Reading

For each module, reconstruct:

`failure + ideal unavailable solution + available proxy + design choice + hidden assumption + risk`

The most useful framing is usually:

> This module is not just a trick; it is a surrogate for the missing mechanism `Y`.

## 5. Reverse Citation Logic

Treat citations as narrative functions:

- field anchor
- limitation evidence
- method ancestor
- neighboring inspiration
- baseline pressure
- protocol justification
- contrast boundary

Explain what permission each key citation gives the paper.

## 6. Experiments as Story Evidence

Read each result as:

`claim + counterfactual + metric + stress condition`

Ask:

- what claim it supports
- what alternative explanation it rules out
- which module it validates
- whether the stress condition really matches the paper's target difficulty

## 7. Story Pattern Worth Learning

Extract one reusable pattern, such as:

- replacement story
- three-module story
- two-axis empty cell
- closed-loop contribution
- hidden-assumption break

## 8. Weakness to New Idea Conversion

Use:

`future work = current method + violated assumption + new mechanism`

For each strong weakness, ask what next paper becomes possible if the key hidden assumption fails harder.

## 9. Writing Rules

Prefer phrasing like:

- "A plausible author-side thinking path is ..."
- "This module is best understood as a surrogate for ..."
- "The citation is not ornamental; it functions as ..."
- "This weakness can be converted into a new research direction ..."

Avoid:

- restating the abstract
- listing sections without causal explanation
- paraphrasing equations without saying why they exist
- speaking as if private author intent were directly observed
