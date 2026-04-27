[🇺🇸 English](#english) · [🇨🇳 中文](#chinese)

---

<a name="english"></a>

# Antalpha Wallet Guard

> v2.0.0 · Comprehensive Web3 Security — Token Risk, Phishing Detection, Rug Pull, Approval Scan

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/AntalphaAI/wallet-guard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Chain: Multi-EVM](https://img.shields.io/badge/chain-Multi--EVM-purple.svg)](https://ethereum.org)
[![Data: GoPlus](https://img.shields.io/badge/data-GoPlus%20Security-green.svg)](https://gopluslabs.io)

---

## What Is This?

**Antalpha Wallet Guard** is a comprehensive Web3 security skill for AI agents, powered by the GoPlus Security API. It provides 6 categories of on-chain security detection to protect users from token scams, malicious addresses, dangerous approvals, NFT risks, phishing sites, and Rug Pulls.

v2.0.0 upgrades from a single approval-scan workflow to a full MCP tool suite — giving your AI agent real-time, multi-dimensional security intelligence.

## Features

- 🔍 **Token Contract Risk** — detect honeypot, hidden mint, abnormal tax, trading restrictions (20+ checks)
- 🚨 **Malicious Address Check** — identify phishing wallets, hackers, sanctioned addresses, scam entities
- 🛡️ **Approval Risk Scan** — ERC20/ERC721/ERC1155 combined scan, flag unlimited and suspicious approvals
- 🖼️ **NFT Security** — detect NFT contract risks (transfer lock, blacklist mechanisms, upgrade risk)
- 🌐 **Phishing Site Detection** — verify a URL before connecting your wallet
- 💣 **Rug Pull Detection** — DeFi contract Rug Pull risk assessment (Beta)
- 🔑 **GoPlus Auth** — dual-step authentication with auto-renewal; falls back to public API gracefully
- ⚡ **In-Memory Cache** — per-tool TTL cache reduces redundant API calls
- 🌍 **Multi-Chain** — Ethereum, BSC, Polygon, Base
- 🌐 **Language-Adaptive** — responds in the user's language (English, Chinese, and more)

## MCP Tools

| Tool | Capability |
|------|-----------|
| `wallet-guard-token-security` | ERC20 contract risk (honeypot, hidden mint, tax, etc.) |
| `wallet-guard-address-security` | Malicious address / blacklist detection |
| `wallet-guard-approval-security` | Wallet approval risk scan (ERC20 + NFT) |
| `wallet-guard-nft-security` | NFT contract risk detection |
| `wallet-guard-phishing-site` | Phishing website detection |
| `wallet-guard-rugpull-detection` | DeFi Rug Pull risk detection (Beta) |

## Supported Chains

| Chain | chainId | Status |
|-------|---------|--------|
| Ethereum Mainnet | `1` | ✅ Supported |
| BNB Smart Chain (BSC) | `56` | ✅ Supported |
| Polygon | `137` | ✅ Supported |
| Base | `8453` | ✅ Supported |
| Other EVM chains | — | 🔜 Coming soon |

## Installation

This skill connects to the Antalpha AI MCP server.

```bash
# Install via clawhub
clawhub install antalpha-wallet-guard
```

Or clone manually:

```bash
git clone https://github.com/AntalphaAI/wallet-guard.git
```

**Optional environment variables** (falls back to GoPlus public API if not set):

```
GOPLUS_APP_KEY=your_app_key
GOPLUS_SECRET_KEY=your_secret_key
```

## Usage Examples

**Token contract scan:**
```
Is this token safe to buy? Contract: 0xYourTokenAddress on Ethereum
```

**Address check:**
```
Is 0x742d35Cc6634C0532925a3b844Bc454e4438f44e a safe address to send funds to?
```

**Approval scan:**
```
Scan my wallet for dangerous approvals: 0xYourWalletAddress
```

**NFT safety check:**
```
Check if this NFT collection is safe: 0xNFTContractAddress on Ethereum
```

**Phishing check:**
```
Is https://uniswap-airdrop.com a phishing site?
```

**Rug Pull check:**
```
Does this DeFi contract have Rug Pull risk? 0xContractAddress on BSC
```

## Example Output

**When danger is found (approval scan):**

```
🚨 High Risk Detected

[Ethereum]
Token: USDC
Spender: 0x6c96...1dee
Risk: Unlimited approval

[BSC]
Token: BUSD
Spender: 0x1234...5678
Risk: Unlimited approval + suspicious contract

🏥 Doctor's advice: Please immediately use Revoke.cash, search for the contract address, and Revoke the access!

Data provided by Antalpha AI data aggregation.
```

**When wallet is clean:**

```
✅ Your wallet is extremely healthy!
No high-risk issues found across Ethereum, BSC, Polygon, or Base. Keep up the good on-chain habits!

Data provided by Antalpha AI data aggregation.
```

## Architecture (v2.0.0)

```
WalletGuardModule (NestJS)
├── GoplusAuthService    ← dual-step auth, token auto-renewal, concurrency lock
├── GoplusCacheService   ← in-memory TTL cache per tool
├── GoplusApiService     ← GoPlus API wrapper (6 endpoints + unified error handling)
└── WalletGuardTools     ← 6 MCP tools registration
```

## Security Notes

- Results are security guidance, not a cryptographic guarantee of wallet safety
- A clean scan does not mean the wallet is risk-free across all attack surfaces
- If the API is unavailable, the skill fails gracefully and suggests manual revocation via [Revoke.cash](https://revoke.cash)
- F6 dApp Security has been removed (GoPlus paid-only endpoint)
- F7 Rug Pull Detection is Beta — results may have limited accuracy

## Changelog

### v2.0.0 (2026-04-20)
- Upgraded to MCP tool-based architecture (6 MCP tools via Antalpha AI server)
- Added: `wallet-guard-token-security` — ERC20 contract risk detection (20+ checks)
- Added: `wallet-guard-address-security` — malicious address / blacklist detection (12+ risk types)
- Added: `wallet-guard-nft-security` — NFT contract risk detection
- Added: `wallet-guard-phishing-site` — phishing website detection
- Added: `wallet-guard-rugpull-detection` — DeFi Rug Pull risk detection (Beta)
- Upgraded: `wallet-guard-approval-security` to GoPlus v2 API, now supports ERC20 + ERC721 + ERC1155 combined scan
- Added: GoPlus dual-step authentication (App Key + Secret → Bearer Token) with auto-renewal and concurrency lock
- Added: In-memory TTL cache layer with per-tool independent TTL configuration
- Removed: F6 dApp Security (GoPlus paid-only endpoint, code 4033)

### v1.1.0 — Multi-Chain Support
- Added support for BNB Smart Chain (56), Polygon (137), and Base (8453)
- When no chain is specified, all four supported chains are scanned sequentially
- Refined high-risk detection: introduced `doubt_list` / `trust_list` signals
- Clarified numeric unlimited approval threshold: > 2^96 treated as unlimited
- Translation and footer fixes

### v1.0.0 — Initial Release
- Ethereum mainnet approval scan via GoPlus Security API
- High-risk detection: unlimited approvals, closed-source contracts, malicious behavior tags
- Language-adaptive output, defensive validation, mandatory source attribution footer

## Maintainer

**Antalpha** — [https://antalpha.com](https://antalpha.com)

Built with ❤️ for safer Web3.

---

<a name="chinese"></a>

# Antalpha Wallet Guard（钱包守卫）

> v2.0.0 · 全面 Web3 安全防护 — 代币风险、钓鱼检测、Rug Pull、授权扫描

[![版本](https://img.shields.io/badge/版本-2.0.0-blue.svg)](https://github.com/AntalphaAI/wallet-guard)
[![协议](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![链](https://img.shields.io/badge/链-多EVM链-purple.svg)](https://ethereum.org)
[![数据](https://img.shields.io/badge/数据-GoPlus%20Security-green.svg)](https://gopluslabs.io)

---

## 这是什么？

**Antalpha Wallet Guard** 是一个基于 GoPlus Security API 的 AI Agent Web3 安全 Skill，提供 6 大类链上安全检测能力，全面保护用户免受代币合约风险、恶意地址、危险授权、NFT 风险、钓鱼网站和 Rug Pull 的侵害。

v2.0.0 从单一授权扫描升级为完整 MCP 工具套件，为你的 AI Agent 提供实时、多维度的安全情报。

## 功能特性

- 🔍 **代币合约风险** — 检测貔貅盘、隐藏铸币、税率异常、交易限制等 20+ 项风险
- 🚨 **恶意地址检测** — 识别钓鱼钱包、黑客地址、制裁地址、诈骗实体
- 🛡️ **授权风险扫描** — ERC20/ERC721/ERC1155 三合一扫描，标记无限额及可疑授权
- 🖼️ **NFT 安全检测** — 检测 NFT 合约风险（转移锁定、黑名单机制、升级风险）
- 🌐 **钓鱼网站检测** — 连接钱包前先验证网站安全性
- 💣 **Rug Pull 检测** — DeFi 合约跑路风险评估（Beta）
- 🔑 **GoPlus 鉴权** — 双步鉴权 + 自动续期；无 Key 时自动降级到公共 API
- ⚡ **内存缓存** — 各工具独立 TTL，减少重复 API 调用
- 🌍 **多链支持** — 以太坊、BSC、Polygon、Base
- 🌐 **语言自适应** — 自动识别用户语言，支持中文、英文等多语言回复

## MCP 工具列表

| 工具 | 功能说明 |
|------|---------|
| `wallet-guard-token-security` | ERC20 合约风险检测（貔貅、隐藏铸币、税率等）|
| `wallet-guard-address-security` | 恶意地址/黑名单检测 |
| `wallet-guard-approval-security` | 钱包授权风险扫描（ERC20 + NFT）|
| `wallet-guard-nft-security` | NFT 合约风险检测 |
| `wallet-guard-phishing-site` | 钓鱼网站检测 |
| `wallet-guard-rugpull-detection` | DeFi Rug Pull 风险检测（Beta）|

## 支持的链

| 链 | chainId | 状态 |
|----|---------|------|
| 以太坊主网（Ethereum） | `1` | ✅ 已支持 |
| BNB Smart Chain（BSC） | `56` | ✅ 已支持 |
| Polygon | `137` | ✅ 已支持 |
| Base | `8453` | ✅ 已支持 |
| 其他 EVM 链 | — | 🔜 即将支持 |

## 安装方式

此 Skill 连接 Antalpha AI MCP 服务器。

```bash
# 通过 clawhub 安装
clawhub install antalpha-wallet-guard
```

或手动克隆：

```bash
git clone https://github.com/AntalphaAI/wallet-guard.git
```

**可选环境变量**（不配置则自动降级到 GoPlus 公共 API）：

```
GOPLUS_APP_KEY=your_app_key
GOPLUS_SECRET_KEY=your_secret_key
```

## 使用方式

**代币合约安全检测：**
```
这个代币安全吗？合约地址：0x你的代币地址，以太坊链
```

**地址安全检测：**
```
这个地址安全吗？0x742d35Cc6634C0532925a3b844Bc454e4438f44e
```

**授权扫描：**
```
帮我扫描这个钱包的危险授权：0x你的钱包地址
```

**NFT 安全检测：**
```
这个 NFT 合约安全吗？0xNFT合约地址
```

**钓鱼网站检测：**
```
https://uniswap-airdrop.com 是钓鱼网站吗？
```

**Rug Pull 检测：**
```
这个 DeFi 合约有跑路风险吗？0x合约地址，BSC 链
```

## 输出示例

**发现风险时（授权扫描）：**

```
🚨 检测到高危授权

【以太坊】
Token：USDC
授权方：0x6c96...1dee
风险：无限额授权

【BSC】
Token：BUSD
授权方：0x1234...5678
风险：无限额授权 + 可疑合约

🏥 医生建议：请立即前往 Revoke.cash，搜索该合约地址并撤销授权！

数据来源：Antalpha AI 数据聚合
```

**钱包安全时：**

```
✅ 钱包非常健康！
在以太坊、BSC、Polygon、Base 上均未发现高危风险，继续保持良好的链上习惯！

数据来源：Antalpha AI 数据聚合
```

## 系统架构（v2.0.0）

```
WalletGuardModule（NestJS）
├── GoplusAuthService    ← 双步鉴权、Token 自动续期、并发锁
├── GoplusCacheService   ← 各工具独立 TTL 内存缓存
├── GoplusApiService     ← GoPlus API 封装（6 个接口 + 统一错误处理）
└── WalletGuardTools     ← 6 个 MCP Tool 注册
```

## 安全说明

- 扫描结果为安全建议，不构成钱包安全的密码学保证
- 扫描结果干净 ≠ 钱包在所有攻击面上都安全
- 若 API 不可用，Skill 会安全降级，引导用户前往 [Revoke.cash](https://revoke.cash) 手动操作
- F6 dApp Security 已移除（GoPlus 付费专属接口）
- F7 Rug Pull Detection 为 Beta 版，结果准确性可能不稳定

## 更新日志

### v2.0.0（2026-04-20）
- 升级为 MCP Tool 架构（6 个工具，通过 Antalpha AI MCP 服务器提供）
- 新增：`wallet-guard-token-security` — ERC20 合约风险检测（20+ 检测项）
- 新增：`wallet-guard-address-security` — 恶意地址/黑名单检测（12+ 风险类型）
- 新增：`wallet-guard-nft-security` — NFT 合约风险检测
- 新增：`wallet-guard-phishing-site` — 钓鱼网站检测
- 新增：`wallet-guard-rugpull-detection` — DeFi Rug Pull 风险检测（Beta）
- 升级：`wallet-guard-approval-security` 至 GoPlus v2 API，支持 ERC20/ERC721/ERC1155 三合一扫描
- 新增：GoPlus 双步鉴权（App Key + Secret → Bearer Token），内置自动续期与并发锁
- 新增：各接口独立 TTL 内存缓存层
- 移除：F6 dApp Security（GoPlus 付费专属接口，code 4033）

### v1.1.0 — 多链支持
- 新增 BNB Smart Chain（56）、Polygon（137）、Base（8453）支持
- 未指定链时自动扫描全部四条链
- 重构高危检测规则：引入 `doubt_list` / `trust_list` 信号
- 明确无限额授权数值阈值（> 2^96）
- 翻译和 Footer 修复

### v1.0.0 — 首次发布
- 基于 GoPlus Security API 的以太坊主网授权扫描
- 高危检测：无限额授权、非开源合约、恶意行为标签
- 语言自适应输出，防御性校验，强制数据来源署名

## 维护团队

**Antalpha** — [https://antalpha.com](https://antalpha.com)

用 ❤️ 为更安全的 Web3 而构建。
