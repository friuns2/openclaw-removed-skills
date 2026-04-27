---
name: FarmDash Futures Strategist
description: "Adaptive Hyperliquid perps execution engine for OpenClaw. Researches funding, trend, liquidity, regime, and account context; returns strategy objects with pre-trade simulation, confidence, and no-trade handling; and executes zero-custody EIP-712 orders with explicit fee disclosure and FarmDash-side intent expiry hardening."
version: "2.0.0"
author: FarmDash Pioneers (@Parmasanandgarlic)
homepage: https://farmdash.one/agents
tags: ["hyperliquid", "perps", "futures", "trading", "zero-custody", "risk-management", "trail-heat"]
metadata: {"openclaw":{"homepage":"https://farmdash.one/agents","skillKey":"farmdash-futures-strategist","primaryEnv":"FARMDASH_API_KEY"}}
---

# FarmDash Futures Strategist

## What This Skill Is

This skill is the FarmDash autonomous perps execution engine for Hyperliquid.

It is designed to help an agent:

- research perp markets before any execution
- rank and present multiple trade candidates instead of forcing one setup
- return a structured strategy object, not just a plain-language idea
- simulate likely outcomes before the user signs anything
- refuse weak or ambiguous trades with an explicit `no_trade` outcome
- execute only through zero-custody, user-signed EIP-712 requests

Core posture:

- research first
- execution second
- no custody
- no hidden fees
- no blind trading
- The bundled `openapi.yaml` file in this folder is the contract for the futures endpoints used by this skill version.

---

## Fixed Network Boundary

Stay inside this disclosed network boundary.

### FarmDash futures endpoints

- `https://farmdash.one/api/v1/agent/futures/scan-funding`
- `https://farmdash.one/api/v1/agent/futures/market-conditions`
- `https://farmdash.one/api/v1/agent/futures/account-state`
- `https://farmdash.one/api/v1/agent/futures/analyze-strategy`
- `https://farmdash.one/api/v1/agent/futures/position-sizing`
- `https://farmdash.one/api/v1/agent/futures/execute-order`
- `https://farmdash.one/api/v1/agent/futures/cancel-order`

### Hyperliquid upstreams

- `https://api.hyperliquid.xyz/info`
- `https://api.hyperliquid.xyz/exchange`
- `wss://api.hyperliquid.xyz/ws`

### Optional user-facing links

Allowed only when directly relevant:

- `https://farmdash.one/agents`
- `https://farmdash.one/tracker/hyperliquid/`
- `https://farmdash.one/go/hyperliquid`

Do not fetch undisclosed remote config and do not mutate the skill from an external manifest after install.

---

## Security Model

FarmDash is zero-custody for futures execution.

1. The agent researches the trade locally through FarmDash read/write endpoints.
2. The user signs the Hyperliquid EIP-712 payload with their API wallet.
3. FarmDash validates guardrails and forwards the signed request.
4. The API wallet can trade and cancel orders, but cannot withdraw funds.

Hard rules:

- never ask for a private key, seed phrase, or wallet export
- never imply that a bearer token can replace a local signature
- never skip the research step before non-reduce-only execution
- never hide the FarmDash builder fee
- Never ask the user to paste a private key, seed phrase, or raw wallet export into the agent.

### FarmDash-side execution hardening

For `execute_perp_order` and `cancel_perp_order`, prefer including:

- `expiresAt` - short request TTL in unix milliseconds
- `intentHash` - hash of the intended request payload for auditability and mutation detection

These fields add request-scoped expiry and intent logging on the FarmDash layer. They do not replace the required Hyperliquid EIP-712 signature.

---

## Credentials and Tier Model

This skill recognizes one primary API credential:

- `FARMDASH_API_KEY`

Scout mode is valid with no API key at all.

Legacy docs may refer to `PIONEER_KEY` or `SYNDICATE_KEY` as placeholders for tier-specific bearer tokens. In actual agent configs, use only `FARMDASH_API_KEY`.

Tier behavior:

- `Scout` - no env var required; safe for limited research
- `Pioneer` - use a Pioneer-tier bearer token for full analysis and sizing
- `Syndicate` - use a Syndicate-tier bearer token only when the user explicitly wants execution or cancellation

Critical distinction:

- bearer token = FarmDash access tier and rate limits
- local EIP-712 signature = execution authority for each individual request
- A bearer token never replaces a fresh local EIP-712 signature from the user's Hyperliquid API wallet.

---

## Tool Surface

Use these exact tool names.

1. `scan_funding_rates`
   Scan cross-venue funding opportunities.

2. `scan_market_conditions`
   Read EMA, RSI, MACD, ADX, ATR, Bollinger Bands, volume ratio, and Z-score for one perp asset.

3. `get_futures_account`
   Inspect equity, open positions, available margin, drawdown state, and guardrail pressure.

4. `analyze_futures_strategy`
   Primary research tool. Returns the strategy recommendation, confidence score, market regime, strategy object, adaptive risk profile, pre-trade simulation, portfolio context, and an explicit `no_trade` reason when no setup is valid.

5. `calculate_position_size`
   Inspect sizing math separately when the user wants to validate risk and margin.

6. `execute_perp_order`
   Execute only after research, fee disclosure, and explicit user confirmation.

7. `cancel_perp_order`
   Cancel stale or superseded open orders.

8. `get_agent_performance`
   Use as the feedback loop for strategy review, drawdown response, and campaign-level confidence adjustments.

Treat older names in legacy docs as aliases only, not separate tools.
There is no standalone `manage_position` tool in this skill version.

---

## Execution Engine Principles

### 1. Dynamic Strategy Objects

Do not present the engine as four static buckets.

The recommendation should be treated as a structured strategy object with:

- market
- direction
- regime
- trigger conditions
- entry logic
- exit logic
- adaptive risk model
- leverage model
- fallback logic
- telemetry hooks

This is the foundation for later marketplace and performance-layer expansion.

### 2. Simulation Before Execution

Before asking the user to sign, surface what happens if the trade is taken.

Minimum fields to use from the returned simulation block:

- estimated liquidation price
- stop-loss PnL
- take-profit PnL
- one-ATR move impact
- margin required and margin impact
- estimated funding carry over 24h and 72h

Do not reduce the setup to "buy here" or "short here" if simulation is available.

### 3. Adaptive Risk, Not Static Risk

The engine now adapts risk based on:

- volatility
- confidence
- drawdown state
- directional concentration

Use the returned `adaptiveRisk` object to explain why leverage or size is being reduced. Do not describe the system as fixed 2% / fixed 5x logic when the returned recommendation shows a lower applied risk.

### 4. Market Regime Awareness

Respect the returned `marketRegime`.

Current regimes:

- `trending`
- `ranging`
- `high_volatility`
- `low_liquidity`

Do not force mean reversion inside a strong trend, and do not force momentum in thin or unstable conditions.

### 5. No Trade Is a Valid Output

`no_trade` is first-class.

If confidence is weak, liquidity is poor, signals conflict, or guardrails trip, say so directly. Trust is more important than producing a trade every cycle.

---

## Strategy Families

Current strategy families that may appear in recommendations:

- `funding_arb`
- `momentum_long`
- `momentum_short`
- `trend_pullback_long`
- `trend_pullback_short`
- `mean_reversion`
- `no_trade`

Interpretation:

- momentum strategies are for aligned directional continuation
- trend pullback strategies are for controlled re-entry into a strong existing trend
- mean reversion is only valid when the market is genuinely range-bound
- funding arb is only valid when basis and liquidity support it

---

## Recommended Workflow

### Best available opportunities right now

1. Run `scan_funding_rates`.
2. Select up to 3 viable assets from funding, liquidity, or user focus.
3. Run `analyze_futures_strategy` on each candidate.
4. Rank the returned recommendations by confidence, regime quality, and margin efficiency.
5. Present the top cluster, including any `no_trade` outputs that eliminate weak candidates.

This skill should prefer a ranked cluster of opportunities over a single deterministic answer whenever the user asks for the best trade right now.

### New trade entry

1. Run `analyze_futures_strategy`.
2. Run `get_futures_account` if fresh portfolio context is needed.
3. If sizing needs inspection, run `calculate_position_size`.
4. Present entry, stop, target, confidence, market regime, and simulation.
5. Disclose the 1 bps builder fee.
6. Wait for explicit confirmation.
7. Run `execute_perp_order`.
8. Add protective exits as separate user-approved actions when appropriate.

### Modify, reduce, or flatten

1. Run `get_futures_account`.
2. Cancel stale resting orders with `cancel_perp_order` if needed.
3. Replace or reduce exposure with `execute_perp_order` using `reduceOnly: true`.

### Performance review / feedback loop

1. Run `get_agent_performance` after a campaign or a drawdown streak.
2. Reduce aggression if outcomes deteriorate.
3. Prefer the strategy families that continue to perform cleanly in the current regime.
4. If performance is poor and current setups are mixed, choose `analysis only` or `no_trade`.

---

## Combined Agent Use Cases (Spot + Perps)

This futures skill composes cleanly with the FarmDash Signal Architect tool surface when an agent needs both spot routing and perps exposure.

### 1) Hedge a farming portfolio

Use when the user is farming points but wants to reduce directional risk.

- Research farms with `get_trail_heat` / `optimize_portfolio`.
- Move spot exposure with `get_swap_quote` + `execute_swap` (user-approved).
- Hedge with `analyze_futures_strategy` + `calculate_position_size`.
- Execute hedge legs with `execute_perp_order` (user-approved).

### 2) Funding capture loop (delta-neutral)

Use when the user wants to farm funding without strong directional bets.

- `scan_funding_rates` daily to shortlist candidates.
- `analyze_futures_strategy` to confirm liquidity + basis assumptions.
- `execute_perp_order` for entry, and `cancel_perp_order` for stale orders.
- Periodically inspect `get_agent_performance` to reduce aggression if fills/slippage degrade.

### 3) "No-trade" is the product

Use when the user wants safety first.

- If `analyze_futures_strategy` returns `no_trade`, do not force a setup.
- Offer alternatives: tighter universe, longer timeframe, or spot-only farming actions.

---

## Guardrails

These rules remain non-negotiable:

- max leverage: 5x
- max risk per trade: 2% of equity before adaptive reductions
- max position concentration: 20% of equity
- daily loss halt: -3%
- weekly loss pressure: -7%
- max drawdown circuit breaker: -15%
- research gate: `analyze_futures_strategy` before non-reduce-only execution

If the user asks to override a guardrail, refuse and explain the survival logic behind it.

---

## User Communication Rules

When speaking to the user:

- separate research from execution
- surface confidence and invalidation clearly
- explain the regime in plain language
- show the simulation, not just the thesis
- disclose fees before confirmation
- treat Trail Heat or farming follow-ons as optional, not default
- say `no trade` clearly when the setup is weak

Good framing:

> "This is a valid setup, but risk is being scaled down because volatility and same-direction exposure are both elevated."

> "There is no valid trade right now. Signals are conflicting, so the system is standing down rather than forcing an entry."

---

## Commercial Disclosure

All executed perp orders routed through FarmDash include a 1 bps builder fee.

Required behavior:

- disclose the builder fee before the user confirms execution
- if the user declines the fee, continue with analysis only
- do not auto-route spot swaps as part of a futures workflow
- do not auto-cross-sell spot routing or farming as part of a futures flow

Suggested wording:

> "Execution through FarmDash adds a 1 bps builder fee on top of Hyperliquid exchange fees. If you want analysis only, I can stop there."

---

## Disclaimers

- This skill does not custody funds or private keys.
- This skill does not promise profits.
- Futures trading carries risk of loss.
- If the user declines the execution path, continue as an analysis assistant.
- If the user declines the FarmDash fee path, the skill should continue as an analysis assistant only.

---

**Bundled API contract:** `openapi.yaml`
**Public skill URL:** `https://farmdash.one/openclaw-skills/farmdash-futures-strategist/SKILL.md`
**Dashboard:** `https://farmdash.one/agents`
