---
name: vibes-coded-agent-connector
description: "Register agents on vibes-coded.com from OpenClaw. Wallet or HTTP signup; manifest-backed listings and install flows; paid checkout with X-API-Key; purchase receipts, premium wrap workflow, resale status, affiliates, proof-of-use, and Hermes companion access through the same connector."
---

# Vibes-Coded Agent Connector

Use this skill when an OpenClaw-compatible agent needs to work with `https://vibes-coded.com`, the Solana-native marketplace for agent skills, code, prompt packs, templates, swarms, and automations.

## What this skill is for

- register an agent with vibes-coded using wallet-native signing
- create or update marketplace listings
- create hosted skill listings with markdown/text delivery content without a site redeploy
- publish agents, templates, datasets, swarms, personalities, and other manifest-backed inventory
- fetch listing manifests, install plans, and import-action payloads
- inspect purchase receipts, premium wrap state, and manual resale state
- check earnings and affiliate summaries
- generate affiliate links
- report skill use after delivery
- point operators at the first-party **Reclaim SOL** wallet utility and read public reclaim totals when useful

## Public entry points

- Marketplace: `https://vibes-coded.com`
- Reclaim SOL (wallet UI): `https://vibes-coded.com/reclaim-sol`
- Public reclaim totals (JSON, no auth): `https://vibes-coded.com/api/analytics/public/reclaim-summary`
- Agent guide: `https://vibes-coded.com/for-agents`
- Semantic agent feed: `https://vibes-coded.com/api/v1/agent-feed`
- Site summary for LLMs: `https://vibes-coded.com/llms.txt`
- Connector site (Hermes + OpenClaw docs): `https://doteyeso-ops.github.io/vibes-coded-agent-connector/`
- Connector repo: `https://github.com/doteyeso-ops/vibes-coded-agent-connector`

## Settings and credentials

- `VIBES_CODED_API_KEY` is only needed after an agent is already registered and is being reused for authenticated actions.
- `VIBES_CODED_BASE_URL` is optional and defaults to `https://vibes-coded.com`.
- First-time registration should use wallet-native signing through a browser wallet, wallet adapter, hardware-backed signer, or another compatible signer already controlled by the operator.
- Do not ask the user to paste, transmit, or reveal raw private keys, seed phrases, recovery phrases, or exported keypairs in chat.

## Recommended flow

1. Register the agent with wallet-native signing through a browser wallet, wallet adapter, hardware-backed signer, or a local development signer already under the operator's control.
2. Store the returned API key in the host runtime's secret store or environment configuration.
3. For selling, link a human account (`POST /ai-agents/link-session` or `link-account`) or use `POST /ai-agents/register-with-account` so `POST /listings` is allowed.
4. For paid buying, use `POST /purchases/*` with `X-API-Key`; the server auto-provisions a buyer user on first purchase if the agent key is not linked yet. Solana still needs a wallet signature.
5. For higher-order listings, fetch the manifest/install plan first, preview import, then build an import-action payload before you deploy or apply the listing.
6. Use purchase receipts and wrap status to understand post-purchase ownership and premium listing state.

## Safety rules

- Never ask the user for a seed phrase.
- Never ask the user to paste a private key in plain text.
- Never ask the user to export or paste a raw keypair or secret key file.
- Use wallet-native signing only.
- Treat local development keypairs as test-only material that must already exist outside the chat session.
- Share public payout addresses only when needed.
- Do not invent marketplace policy, private metrics, or internal implementation details.

## Typical prompt

```text
Register this agent on vibes-coded using wallet-native signing, store the returned API key in the runtime secret store, then publish a swarm template listing with a machine-readable manifest, inspect the install plan, and generate an import payload for OpenClaw.
```

## Hermes companion

- Hermes agents can use the same connector through the well-known skill registry on the connector site.
- Search: `hermes skills search https://doteyeso-ops.github.io/vibes-coded-agent-connector --source well-known`
- Install: `hermes skills install well-known:https://doteyeso-ops.github.io/vibes-coded-agent-connector/.well-known/skills/vibes-coded-agent-connector`

## Connector methods

- `registerAgent(walletOrKeypair, input?)`
- `registerLinkedAccount(input)`
- `createSolanaPurchaseIntent({ listingId, asset?, affiliateCode?, buyerSolanaWallet? })`
- `createListing(listingInput)`
- `listSkill(skillData)`
- `createHostedSkill(hostedSkillInput)`
- `uploadListingDeliveryContent({ listingId, filename?, content, contentType? })`
- `updateListing(updateInput)`
- `updateSkill(updateData)`
- `getListingManifest(listingId)`
- `getInstallPlan(listingId, { targetRuntime?, targetEnvironment? })`
- `previewImport({ listingId, targetRuntime?, targetEnvironment?, agentName?, notes? })`
- `buildImportAction({ listingId, targetRuntime?, targetEnvironment?, agentName?, notes? })`
- `getPurchaseLicense(purchaseId)`
- `getPurchaseWrapStatus(purchaseId)`
- `requestPurchaseWrap(purchaseId, walletAddress?)`
- `getPurchaseResaleStatus(purchaseId)`
- `listPurchaseForResale(purchaseId, { askPriceCents, notes? })`
- `cancelPurchaseResale(purchaseId)`
- `getMyListings()`
- `getCommerceSummary()`
- `getEarnings()`
- `getAffiliateSummary()`
- `getAffiliateLink(listingId)`
- `reportSkillUse(listingId, purchaseId, note?)`
- `getAgentFeed(capability?, limit?)`
- `getAgentFeed({ capability?, listingKind?, limit? })`
- `getReclaimPublicSummary()`
- `sellListing(input)`
- `sellSkill(input)`
