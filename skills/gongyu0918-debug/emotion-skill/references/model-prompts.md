# Model Prompts

Use the semantic pass only when `analysis.semantic_pass` is `fast`.
Emotion collection runs through four concurrent signals: front labels, a runtime-only review pass, dialogue history, and time or runtime pressure.
During cold start, the review pass can run on each turn. Stable users get a very short shadow review.

## 1. Fast Screen Prompt

```text
Classify current user work-state for an agent runtime.
Prioritize delay against the user's baseline, same-issue pressure, hang/stuck wording, terse abrupt replies, and success/guard signals.
Return JSON only:
{"m":"urgent","labels":["urgent"],"emotion_vector":{"urgency":0.0,"frustration":0.0,"confusion":0.0,"skepticism":0.0,"satisfaction":0.0,"cautiousness":0.0,"openness":0.0},"why":["delay"]}
```

Rules:

- Labels stay within `urgent`, `frustrated`, `confused`, `skeptical`, `satisfied`, `cautious`, `exploratory`, `neutral`.
- `emotion_vector` keeps only emotion axes. Do not use production, money, permission, deletion, or compliance domain words as direct emotion evidence.
- Use `usr.prior` and `usr.persona` as low-weight priors.
- Treat `still not fixed`, `same issue`, `stuck`, long delay, repeated emphasis, and abrupt short replies as strong task-state cues.
- Treat nonstandard punctuation, deliberate typos, nonstandard spelling, textisms, and rhythmic pauses as low-confidence surface cues that need support from delay, retries, contradiction, or repeated failure.
- Respect `usr.delay`, `usr.work`, `usr.terse`, and `usr.polite` as baseline hints instead of treating all users the same.
- Keep the answer short and machine-readable.

## 2. Fast Confirmation Prompt

```text
Fuse the rule screen with runtime pressure.
Return JSON only:
{"m":"urgent","labels":["urgent"],"conf":0.0,"emotion_vector":{"urgency":0.0,"frustration":0.0,"confusion":0.0,"skepticism":0.0,"satisfaction":0.0,"cautiousness":0.0,"openness":0.0},"acts":["act-first"]}
```

Rules:

- Prefer working-state pressure over surface politeness.
- Keep `cautious` tied to care language, boundary language, and verification-first language.
- Keep `skeptical` tied to evidence requests, contradiction, and challenge language.
- Use `fine.`, `sure...`, `whatever`, `行吧`, `算了`, `呵`, `……`, `..`, `. . .`, and abrupt half-cut turns as weak stance cues, then confirm them against runtime pressure.
- Recent success plus guard wording should raise `satisfied`.

## 3. Compact Overlay Prompt

Use the compact overlay as the default injected state block:

```text
<state mode=urgent route=steer main=1 hb=defer parallel=0 style=act_then_brief verify=high upd=15s probe=0 sem=fast>
signals:delay_pressure,repeated_user_emphasis; actions:act-first,short-first-reply
</state>
```

This block is short enough for turn-local system or developer injection.

## 4. Review Pass Prompt

```text
Run a runtime-only follow-up review for the latest user message.
Decompose latent affect and stance cues for long-term calibration.
Extract the exact wording, hedge, correction, punctuation, tempo clue, or stance marker that carries emotion.
Return JSON only:
{"emotion_vector":{"urgency":0.0,"frustration":0.0,"confusion":0.0,"skepticism":0.0,"satisfaction":0.0,"cautiousness":0.0,"openness":0.0},"labels":["skeptical"],"confidence":0.0,"emotionality":0.0,"composition":{"urgency":0.0,"frustration":0.0,"confusion":0.0,"skepticism":0.0,"satisfaction":0.0,"cautiousness":0.0,"openness":0.0},"cue_spans":[{"text":"不一定","signal":"skepticism","kind":"hedge","strength":0.4}],"notes":["light hedge"]}
```

Rules:

- Keep this pass focused on emotion wording and stance signals.
- Look for hedges, soft corrections, repeated emphasis, impatience punctuation, abrupt closure, scope protection, evidence-seeking language, dismissive short phrases, deliberate misspellings, textisms, and rhythmic pause markers.
- Use `front_weight`, `posthoc_weight`, and `front_consistency` only as calibration hints.
- Cold start favors richer review decomposition. High long-run consistency compresses the pass into a short shadow review instead of turning it off.
- `emotionality` means the share of the sentence that carries emotional or stance pressure.
- `composition` is the normalized share across emotion axes. Keep it short and machine-readable.
