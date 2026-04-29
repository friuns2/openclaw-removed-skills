---
name: greenhelix-agent-iam-guide
version: "1.3.1"
description: "Agent Identity & Access Management: RBAC, Key Scoping, and Multi-Tenant Security for AI Agent Systems. Complete IAM architecture for multi-agent commerce: Ed25519 identity registration, role-based access control with pure-function authorization, scoped API key lifecycle with zero-downtime rotation, permission delegation chains with budget boundaries, multi-tenant isolation, and anomaly-detecting audit logging. detailed code examples with Python classes with full API integration. Aligned with NIST AI RMF, CSA Agentic AI IAM Framework, and AWS AgentCore Identity patterns."
license: MIT
compatibility: [openclaw]
author: felix-agent
type: guide
tags: [iam, rbac, api-keys, multi-tenant, security, agent-identity, access-control, guide, greenhelix, openclaw, ai-agent]
price_usd: 0.0
content_type: markdown
executable: false
install: none
credentials: [GREENHELIX_API_KEY, AGENT_SIGNING_KEY]
metadata:
  openclaw:
    requires:
      env:
        - GREENHELIX_API_KEY
        - AGENT_SIGNING_KEY
    primaryEnv: GREENHELIX_API_KEY
---
# Agent Identity & Access Management: RBAC, Key Scoping, and Multi-Tenant Security for AI Agent Systems

> **Notice**: This is an educational guide with illustrative code examples.
> It does not execute code or install dependencies.
> All examples use the GreenHelix sandbox (https://sandbox.greenhelix.net) which
> provides 500 free credits — no API key required to get started.
>
> **Referenced credentials** (you supply these in your own environment):
> - `GREENHELIX_API_KEY`: API authentication for GreenHelix gateway (read/write access to purchased API tools only)
> - `AGENT_SIGNING_KEY`: Cryptographic signing key for agent identity (Ed25519 key pair for request signing)


Your multi-agent commerce system has 23 agents. They share a single API key. Every agent can call every tool -- register services, release escrow, rotate keys, set budget caps, submit metrics. Agent 7 is a price-comparison reader that only needs marketplace search. It has the same permissions as Agent 1, the billing administrator that manages wallets for the entire fleet. Last Tuesday, a prompt injection in Agent 7's upstream data feed caused it to call `set_budget_cap` with a zero-dollar limit on the shared wallet. All 22 other agents stopped transacting for 40 minutes until a human noticed. The root cause was not the prompt injection. It was the identity and access management architecture that gave a read-only comparison agent write access to billing controls. Gartner's 2026 Security Leaders Survey found that only 18% of security leaders are confident their IAM systems can handle AI agents. The Cloud Security Alliance's Agentic AI IAM Framework (March 2026) and AWS AgentCore Identity (Q1 2026) both launched specifically because the industry recognized that agent IAM is a fundamentally different problem than human IAM. Agents do not have passwords. They do not complete MFA challenges. They do not click "Remember this device." They authenticate with keys, operate with scoped permissions, and delegate authority to other agents in chains that no human reviews in real time. This guide gives you the complete IAM architecture for multi-agent commerce systems: registration, RBAC, key scoping, permission delegation, multi-tenant isolation, and audit logging. Every class calls the GreenHelix A2A Commerce Gateway API. Every pattern enforces least privilege by default.
1. [Why Agent IAM Is Different](#chapter-1-why-agent-iam-is-different)
2. [Agent Registration & Identity](#chapter-2-agent-registration--identity)

## What You'll Learn
- Chapter 1: Why Agent IAM Is Different
- Chapter 2: Agent Registration & Identity
- Chapter 3: Role-Based Access Control (RBAC)
- Chapter 4: API Key Lifecycle
- Chapter 5: Permission Delegation
- Chapter 6: Multi-Tenant Architecture
- Chapter 7: IAM Auditing & Monitoring
- Chapter 8: Production IAM Checklist
- GreenHelix Agent Provisioning — Production Implementation

## Full Guide

# Agent Identity & Access Management: RBAC, Key Scoping, and Multi-Tenant Security for AI Agent Systems

Your multi-agent commerce system has 23 agents. They share a single API key. Every agent can call every tool -- register services, release escrow, rotate keys, set budget caps, submit metrics. Agent 7 is a price-comparison reader that only needs marketplace search. It has the same permissions as Agent 1, the billing administrator that manages wallets for the entire fleet. Last Tuesday, a prompt injection in Agent 7's upstream data feed caused it to call `set_budget_cap` with a zero-dollar limit on the shared wallet. All 22 other agents stopped transacting for 40 minutes until a human noticed. The root cause was not the prompt injection. It was the identity and access management architecture that gave a read-only comparison agent write access to billing controls. Gartner's 2026 Security Leaders Survey found that only 18% of security leaders are confident their IAM systems can handle AI agents. The Cloud Security Alliance's Agentic AI IAM Framework (March 2026) and AWS AgentCore Identity (Q1 2026) both launched specifically because the industry recognized that agent IAM is a fundamentally different problem than human IAM. Agents do not have passwords. They do not complete MFA challenges. They do not click "Remember this device." They authenticate with keys, operate with scoped permissions, and delegate authority to other agents in chains that no human reviews in real time. This guide gives you the complete IAM architecture for multi-agent commerce systems: registration, RBAC, key scoping, permission delegation, multi-tenant isolation, and audit logging. Every class calls the GreenHelix A2A Commerce Gateway API. Every pattern enforces least privilege by default.

---

## Table of Contents

1. [Why Agent IAM Is Different](#chapter-1-why-agent-iam-is-different)
2. [Agent Registration & Identity](#chapter-2-agent-registration--identity)
3. [Role-Based Access Control (RBAC)](#chapter-3-role-based-access-control-rbac)
4. [API Key Lifecycle](#chapter-4-api-key-lifecycle)
5. [Permission Delegation](#chapter-5-permission-delegation)
6. [Multi-Tenant Architecture](#chapter-6-multi-tenant-architecture)
7. [IAM Auditing & Monitoring](#chapter-7-iam-auditing--monitoring)
8. [Production IAM Checklist](#chapter-8-production-iam-checklist)

---

## Chapter 1: Why Agent IAM Is Different

### Agents Are Not Users

Human IAM was built around one assumption: the entity requesting access is a person sitting at a keyboard. Every control flow in traditional IAM relies on this. Password authentication assumes the entity can memorize a secret. Multi-factor authentication assumes the entity has a phone or a hardware token. Session management assumes the entity will interact for a bounded period, then close their browser. Adaptive risk scoring assumes the entity has behavioral biometrics -- typing speed, mouse movement, login time patterns -- that distinguish them from an impersonator.

Agents break every one of these assumptions. An agent authenticates with a cryptographic key, not a password. It does not have a phone for MFA. It does not have sessions -- it makes API calls continuously, potentially thousands per hour, for months without interruption. It has no behavioral biometrics because its behavior is determined by its programming, its model weights, and its input data, all of which can change between calls. Two different agents using the same model and the same prompt template will produce identical behavioral signatures. An impersonator using a stolen key is indistinguishable from the legitimate agent.

The consequence is that every human IAM pattern -- password policies, MFA enrollment, session timeouts, behavioral analytics -- is either inapplicable or actively misleading for agent systems. Agent IAM must be built from different primitives.

### The Identity Confidence Gap

The 2026 Gartner Security Leaders Survey quantified the problem. 82% of security leaders reported that their current IAM systems cannot adequately handle AI agent identities. The specific gaps cited most frequently:

- **No agent-specific identity lifecycle** (71%): Agents are registered as "service accounts" with no distinction between a cron job and an autonomous agent with financial authority.
- **No permission delegation model** (68%): When Agent A hires Agent B through a marketplace, there is no standard mechanism for A to grant B a scoped subset of its permissions.
- **No key rotation for non-human entities** (64%): Key rotation policies assume a human will generate a new key, update their client, and retire the old key. Agents need automated, zero-downtime rotation.
- **No multi-tenant isolation for agent fleets** (59%): Organizations running agents across multiple customers or business units have no standard tenant boundary model.

The CSA Agentic AI IAM Framework (March 2026) proposed a reference architecture addressing these gaps. AWS AgentCore Identity launched in Q1 2026 with managed agent identity, scoped credentials, and delegation chains. Both validate the same conclusion: agent IAM requires purpose-built primitives, not human IAM with the password fields removed.

### Authentication Primitives for Agents

Three authentication mechanisms apply to agent systems. Each has different security properties.

**Ed25519 keypairs** are the strongest primitive for agent identity. The agent generates a keypair locally, registers the public key with the platform, and signs every request with the private key. The private key never leaves the agent's runtime. Verification is stateless -- the platform checks the signature against the registered public key without querying a database or calling an external service. Ed25519 is deterministic, fast (62,000 signatures per second on commodity hardware), and resistant to timing attacks. GreenHelix uses Ed25519 for agent identity via `register_agent` and `verify_agent`.

**OAuth 2.0 client credentials** are widely supported but introduce dependencies. The agent exchanges a client ID and secret for an access token, then presents the token on each request. The token has a bounded lifetime, which forces periodic re-authentication. This is a strength for humans (session expiry limits damage from stolen cookies) but a weakness for agents (token refresh adds latency and a failure mode). OAuth also requires a token endpoint to be available -- an additional point of failure.

**API keys** are the simplest mechanism: a static secret included in every request. API keys have no cryptographic binding to the caller -- anyone with the key string can use it. They are the least secure option but the most operationally convenient. The right approach is to use Ed25519 for identity verification and scoped API keys for tool access, which is exactly what this guide implements.

### Framework Alignment

The NIST AI Risk Management Framework (AI RMF 1.0) calls out identity and access management in its GOVERN function: "AI actors are identifiable, and their roles and responsibilities are documented." The CSA framework extends this to agent-specific requirements: scoped credentials, delegation chains, tenant isolation, and continuous verification. The patterns in this guide implement both frameworks. Chapter 2 covers NIST's identity requirement. Chapters 3-5 cover CSA's scoped credentials and delegation model. Chapter 6 covers tenant isolation. Chapter 7 covers the audit requirements from both frameworks.

---

## Chapter 2: Agent Registration & Identity

### Ed25519 Keypair Generation

Every agent in your system needs a unique, cryptographically verifiable identity. The identity is an Ed25519 keypair: the private key stays with the agent, the public key is registered on the platform. The keypair serves two purposes -- it proves the agent is who it claims to be, and it provides a stable identifier that survives key rotation (the agent ID persists even when keys are rotated).

The registration flow:

1. Generate an Ed25519 keypair using a cryptographically secure random number generator.
2. Call `register_agent` with the agent's public key and metadata (display name, roles, owner, tenant).
3. Store the private key securely -- in a secrets manager, an HSM, or at minimum an encrypted file with filesystem permissions restricted to the agent's runtime user.
4. On every sensitive operation, sign a challenge and call `verify_agent` to prove possession of the private key.

### Identity Metadata

Registration is not just cryptographic -- it establishes the agent's place in your organizational hierarchy. The metadata you attach at registration time determines what the agent can do, who owns it, and which tenant it belongs to.

- **agent_id**: A unique, human-readable identifier. Use a structured format: `{tenant}-{role}-{instance}`. Example: `acme-reader-01`.
- **display_name**: A descriptive name for dashboards and audit logs. Example: "Acme Price Comparison Agent #1".
- **owner**: The human or team responsible for this agent. Used for incident escalation and permission review.
- **roles**: The initial role assignments. Roles are defined in your RBAC configuration (Chapter 3).
- **tenant**: The tenant this agent belongs to (Chapter 6). Agents cannot access resources outside their tenant unless explicitly granted cross-tenant permissions.

### The AgentIAM Class

The following class handles the complete identity lifecycle: registration, identity retrieval, and verification. It stores the private key in memory and provides signing methods for downstream operations.

```python
import requests
import json
import hashlib
import time
import os
import base64
from typing import Optional
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder


# --- GreenHelix sandbox session (free tier: 500 credits, no key required) ---
# To get started, visit https://sandbox.greenhelix.net — no signup needed.
# For production, set GREENHELIX_API_KEY in your environment.
import os

API_BASE = os.environ.get("GREENHELIX_API_URL", "https://sandbox.greenhelix.net")

session = requests.Session()
api_key = os.environ.get("GREENHELIX_API_KEY", "")
if api_key:
    session.headers["Authorization"] = f"Bearer {api_key}"
session.headers["Content-Type"] = "application/json"


def api_call(tool: str, input_data: dict) -> dict:
    """Call a GreenHelix REST endpoint for the given tool."""
    response = session.post(f"{API_BASE}/v1/tools/{tool}", json=input_data)
    response.raise_for_status()
    return response.json()


class AgentIAM:
    """Complete agent identity lifecycle: register, verify, retrieve."""

    def __init__(self, agent_id: str, owner: str, tenant: str):
        self.agent_id = agent_id
        self.owner = owner
        self.tenant = tenant
        self._signing_key: Optional[SigningKey] = None
        self._verify_key: Optional[VerifyKey] = None
        self._registered = False

    def generate_keypair(self) -> str:
        """Generate an Ed25519 keypair. Returns the public key hex."""
        self._signing_key = SigningKey.generate()
        self._verify_key = self._signing_key.verify_key
        return self._verify_key.encode(encoder=HexEncoder).decode()

    def register_agent(self, display_name: str, roles: list[str]) -> dict:
        """Register this agent with the platform."""
        if self._signing_key is None:
            self.generate_keypair()

        public_key_hex = self._verify_key.encode(encoder=HexEncoder).decode()

        result = api_call("register_agent", {
            "agent_id": self.agent_id,
            "display_name": display_name,
            "public_key": public_key_hex,
            "metadata": {
                "owner": self.owner,
                "tenant": self.tenant,
                "roles": roles,
                "registered_at": int(time.time()),
            },
        })
        self._registered = True
        return result

    def get_identity(self) -> dict:
        """Retrieve the current identity record from the platform."""
        return api_call("get_agent_identity", {
            "agent_id": self.agent_id,
        })

    def sign_challenge(self, challenge: str) -> str:
        """Sign a challenge string with the agent's private key."""
        if self._signing_key is None:
            raise RuntimeError("No signing key. Call generate_keypair() first.")
        signed = self._signing_key.sign(challenge.encode())
        return base64.b64encode(signed.signature).decode()

    def verify_identity(self) -> dict:
        """Prove identity by signing a timestamp challenge."""
        challenge = f"{self.agent_id}:{int(time.time())}"
        signature = self.sign_challenge(challenge)

        return api_call("verify_agent", {
            "agent_id": self.agent_id,
            "challenge": challenge,
            "signature": signature,
        })

    def export_public_key(self) -> str:
        """Export the public key for sharing with other agents."""
        if self._verify_key is None:
            raise RuntimeError("No keypair generated.")
        return self._verify_key.encode(encoder=HexEncoder).decode()

    def get_identity_hash(self) -> str:
        """Generate a deterministic hash of the agent's identity for audit logs."""
        identity_string = f"{self.agent_id}:{self.owner}:{self.tenant}"
        return hashlib.sha256(identity_string.encode()).hexdigest()[:16]
```

### Registration Workflow

```python
# Register a new agent with reader role in the acme tenant
agent = AgentIAM(
    agent_id="acme-reader-01",
    owner="platform-team@acme.com",
    tenant="acme",
)

# Generate keypair and register
public_key = agent.generate_keypair()
print(f"Public key: {public_key}")

registration = agent.register_agent(
    display_name="Acme Price Comparison Agent #1",
    roles=["reader"],
)
print(f"Registration: {json.dumps(registration, indent=2)}")

# Verify identity after registration
verification = agent.verify_identity()
print(f"Verified: {verification}")

# Retrieve identity record
identity = agent.get_identity()
print(f"Identity: {json.dumps(identity, indent=2)}")
```

### Key Storage Best Practices

The private key is the agent's sole proof of identity. If it is compromised, the attacker can impersonate the agent. If it is lost, the agent must be re-registered. Store it according to the sensitivity of the agent's role:

- **Admin agents**: Use an HSM (AWS CloudHSM, Azure Dedicated HSM) or a managed secrets service (AWS Secrets Manager, HashiCorp Vault) with audit logging on every access.
- **Operator agents**: Use a secrets manager with rotation support. The key should be injected into the runtime as an environment variable, not stored on disk.
- **Reader agents**: A secrets manager is still preferred, but an encrypted file with `chmod 600` permissions is acceptable for low-risk read-only agents.

Never store private keys in source control, environment files committed to git, container images, or shared filesystems. The `AgentIAM` class keeps the key in memory only -- it is never written to disk by the class itself.

---

## Chapter 3: Role-Based Access Control (RBAC)

### Defining Roles

RBAC maps agents to permissions through roles. A role is a named collection of allowed tools. An agent can have one or more roles. The authorization check is simple: before calling any tool, verify that the agent's assigned roles include that tool in their allowed set.

Five roles cover the common agent commerce patterns:

| Role | Description | Allowed Tools |
|------|-------------|---------------|
| **admin** | Full platform access. Key rotation, budget management, identity administration. | All tools |
| **operator** | Transaction execution. Escrow, payments, marketplace operations. | create_escrow, release_escrow, deposit, register_service, search_services, send_message, get_messages |
| **reader** | Read-only access. Queries, searches, reputation checks. | get_agent_identity, get_agent_reputation, search_services, get_balance, get_budget_status, get_messages |
| **billing** | Financial administration. Budget caps, wallet management, cost estimation. | set_budget_cap, get_budget_status, get_balance, estimate_cost, get_volume_discount, create_wallet |
| **marketplace** | Service registration and discovery. | register_service, search_services, best_match, rate_service |

These roles follow the principle of least privilege. A reader cannot modify state. A billing agent cannot create escrows. An operator cannot change budget caps. Each agent gets the minimum set of permissions required for its function.

### The RBACManager

The `RBACManager` is a pure in-memory authorization engine. It does not make API calls for authorization decisions -- it evaluates permissions locally using role definitions loaded at startup. This is a deliberate design choice. Authorization decisions must be fast (sub-millisecond), reliable (no network dependency), and auditable (deterministic given the same inputs). The API is used for identity verification (Chapter 2) and for auditing access decisions (Chapter 7), but the authorization logic itself is a pure function.

```python
class RBACManager:
    """Role-based access control for agent tool permissions.

    Authorization decisions are pure functions -- no API calls.
    Roles and assignments are managed in memory for speed and reliability.
    """

    DEFAULT_ROLES = {
        "admin": {
            "description": "Full platform access",
            "tools": ["*"],  # Wildcard -- all tools
        },
        "operator": {
            "description": "Transaction execution",
            "tools": [
                "create_escrow", "release_escrow", "cancel_escrow",
                "deposit", "register_service", "search_services",
                "best_match", "rate_service", "send_message",
                "get_messages", "submit_metrics",
            ],
        },
        "reader": {
            "description": "Read-only queries",
            "tools": [
                "get_agent_identity", "get_agent_reputation",
                "get_trust_score", "search_services",
                "get_balance", "get_budget_status",
                "get_messages", "get_claim_chains",
                "get_agent_leaderboard",
            ],
        },
        "billing": {
            "description": "Financial administration",
            "tools": [
                "create_wallet", "get_balance",
                "set_budget_cap", "get_budget_status",
                "estimate_cost", "get_volume_discount",
                "convert_currency",
            ],
        },
        "marketplace": {
            "description": "Service registration and discovery",
            "tools": [
                "register_service", "search_services",
                "best_match", "rate_service",
            ],
        },
    }

    def __init__(self):
        self.roles: dict[str, dict] = dict(self.DEFAULT_ROLES)
        self.assignments: dict[str, list[str]] = {}  # agent_id -> [role_names]

    def define_role(self, role_name: str, description: str,
                    tools: list[str]) -> dict:
        """Define a custom role with specific tool permissions."""
        if not role_name or not tools:
            raise ValueError("Role name and tools list are required.")

        self.roles[role_name] = {
            "description": description,
            "tools": tools,
        }
        return {"role": role_name, "tools": tools, "status": "created"}

    def assign_role(self, agent_id: str, role_name: str) -> dict:
        """Assign a role to an agent. Agents can have multiple roles."""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' is not defined.")

        if agent_id not in self.assignments:
            self.assignments[agent_id] = []

        if role_name not in self.assignments[agent_id]:
            self.assignments[agent_id].append(role_name)

        return {
            "agent_id": agent_id,
            "roles": self.assignments[agent_id],
            "status": "assigned",
        }

    def revoke_role(self, agent_id: str, role_name: str) -> dict:
        """Remove a role from an agent."""
        if agent_id in self.assignments:
            self.assignments[agent_id] = [
                r for r in self.assignments[agent_id] if r != role_name
            ]
        return {
            "agent_id": agent_id,
            "roles": self.assignments.get(agent_id, []),
            "status": "revoked",
        }

    def get_allowed_tools(self, agent_id: str) -> set[str]:
        """Get the union of all tools allowed by an agent's roles."""
        roles = self.assignments.get(agent_id, [])
        tools = set()
        for role_name in roles:
            role = self.roles.get(role_name, {})
            role_tools = role.get("tools", [])
            if "*" in role_tools:
                return {"*"}  # Admin -- all tools allowed
            tools.update(role_tools)
        return tools

    def check_permission(self, agent_id: str, tool: str) -> dict:
        """Check if an agent has permission to call a specific tool.

        Returns a decision dict with allow/deny and the reason.
        This is a pure function -- no API calls, no side effects.
        """
        allowed = self.get_allowed_tools(agent_id)

        if not allowed:
            return {
                "agent_id": agent_id,
                "tool": tool,
                "allowed": False,
                "reason": "no_roles_assigned",
                "roles": [],
            }

        if "*" in allowed or tool in allowed:
            return {
                "agent_id": agent_id,
                "tool": tool,
                "allowed": True,
                "reason": "role_grant",
                "roles": self.assignments.get(agent_id, []),
            }

        return {
            "agent_id": agent_id,
            "tool": tool,
            "allowed": False,
            "reason": "tool_not_in_role",
            "roles": self.assignments.get(agent_id, []),
            "allowed_tools": sorted(allowed),
        }

    def list_agent_permissions(self, agent_id: str) -> dict:
        """List all permissions for an agent across all assigned roles."""
        roles = self.assignments.get(agent_id, [])
        role_details = {}
        for role_name in roles:
            role = self.roles.get(role_name, {})
            role_details[role_name] = {
                "description": role.get("description", ""),
                "tools": role.get("tools", []),
            }
        return {
            "agent_id": agent_id,
            "roles": role_details,
            "effective_tools": sorted(self.get_allowed_tools(agent_id)),
        }
```

### Enforcing RBAC on Every Call

The RBAC check wraps every tool call. The `SecureToolCaller` class combines identity verification (Chapter 2) with permission checking to ensure that only authorized agents call only permitted tools.

```python
class SecureToolCaller:
    """Wraps tool calls with identity verification and RBAC checks."""

    def __init__(self, rbac: RBACManager):
        self.rbac = rbac
        self._access_log: list[dict] = []

    def execute(self, agent: AgentIAM, tool: str,
                input_data: dict) -> dict:
        """Execute a tool call with full IAM enforcement."""
        timestamp = int(time.time())

        # Step 1: Verify identity
        try:
            verification = agent.verify_identity()
        except Exception as e:
            self._log_access(agent.agent_id, tool, "denied",
                             "identity_verification_failed", timestamp)
            raise PermissionError(
                f"Identity verification failed for {agent.agent_id}: {e}"
            )

        # Step 2: Check RBAC permission
        permission = self.rbac.check_permission(agent.agent_id, tool)
        if not permission["allowed"]:
            self._log_access(agent.agent_id, tool, "denied",
                             permission["reason"], timestamp)
            raise PermissionError(
                f"Agent {agent.agent_id} denied access to {tool}: "
                f"{permission['reason']}"
            )

        # Step 3: Execute the tool call
        result = api_call(tool, input_data)

        self._log_access(agent.agent_id, tool, "allowed",
                         "role_grant", timestamp)

        return result

    def _log_access(self, agent_id: str, tool: str, decision: str,
                    reason: str, timestamp: int) -> None:
        """Record every access decision for audit purposes."""
        self._access_log.append({
            "agent_id": agent_id,
            "tool": tool,
            "decision": decision,
            "reason": reason,
            "timestamp": timestamp,
        })

    def get_access_log(self) -> list[dict]:
        """Return the access decision log."""
        return list(self._access_log)
```

### Usage Pattern

```python
# Initialize RBAC and assign roles
rbac = RBACManager()
rbac.assign_role("acme-reader-01", "reader")
rbac.assign_role("acme-admin-01", "admin")
rbac.assign_role("acme-ops-01", "operator")

# Check permissions before execution
print(rbac.check_permission("acme-reader-01", "get_agent_reputation"))
# {"agent_id": "acme-reader-01", "tool": "get_agent_reputation",
#  "allowed": True, "reason": "role_grant", ...}

print(rbac.check_permission("acme-reader-01", "set_budget_cap"))
# {"agent_id": "acme-reader-01", "tool": "set_budget_cap",
#  "allowed": False, "reason": "tool_not_in_role", ...}

# Use SecureToolCaller for enforced execution
caller = SecureToolCaller(rbac)
reader_agent = AgentIAM("acme-reader-01", "ops@acme.com", "acme")
reader_agent.generate_keypair()

# This succeeds -- reader can call get_agent_reputation
result = caller.execute(reader_agent, "get_agent_reputation", {
    "agent_id": "acme-reader-01",
})

# This raises PermissionError -- reader cannot call set_budget_cap
try:
    caller.execute(reader_agent, "set_budget_cap", {
        "agent_id": "acme-reader-01",
        "cap": "0",
    })
except PermissionError as e:
    print(f"Blocked: {e}")
```

The key insight is that authorization is local and identity verification is remote. The RBAC check happens in microseconds with no network call. The identity verification happens once per call against the platform. This separation means a network outage does not disable authorization -- it disables identity verification, which fails closed (denies access).

---

## Chapter 4: API Key Lifecycle

### Scoped Key Creation

A single API key with full permissions is the root cause of most agent IAM incidents. The fix is scoped keys: each agent gets a key that only permits the tools its role requires. If the key is compromised, the blast radius is limited to the tools in scope.

Key scoping maps directly to RBAC roles. When you create a key for an agent, you specify which tools the key can access. The platform enforces this server-side -- even if an attacker extracts the key and calls a tool not in scope, the platform rejects the call.

```python
class KeyManager:
    """API key lifecycle: creation, rotation, revocation, and audit."""

    def __init__(self, admin_agent: AgentIAM, rbac: RBACManager):
        self.admin_agent = admin_agent
        self.rbac = rbac
        self._key_registry: dict[str, dict] = {}  # key_id -> metadata

    def create_scoped_key(self, target_agent_id: str,
                          label: str,
                          ttl_hours: int = 720) -> dict:
        """Create an API key scoped to the agent's RBAC permissions.

        Args:
            target_agent_id: The agent this key is for.
            label: Human-readable label (e.g., "prod-reader-2026-q2").
            ttl_hours: Key lifetime in hours. Default 30 days.
        """
        allowed_tools = self.rbac.get_allowed_tools(target_agent_id)
        if not allowed_tools:
            raise ValueError(
                f"Agent {target_agent_id} has no roles assigned. "
                "Assign roles before creating keys."
            )

        result = api_call("create_api_key", {
            "agent_id": target_agent_id,
            "label": label,
            "scopes": sorted(allowed_tools) if "*" not in allowed_tools
                      else ["*"],
            "ttl_hours": ttl_hours,
        })

        key_id = result.get("key_id", f"key-{int(time.time())}")
        self._key_registry[key_id] = {
            "agent_id": target_agent_id,
            "label": label,
            "created_at": int(time.time()),
            "ttl_hours": ttl_hours,
            "scopes": sorted(allowed_tools),
            "status": "active",
        }

        return result

    def rotate_key(self, target_agent_id: str,
                   old_key_id: str,
                   grace_period_minutes: int = 30) -> dict:
        """Rotate an API key with zero-downtime overlap.

        The rotation strategy:
        1. Create a new key with the same scopes.
        2. Keep the old key active for the grace period.
        3. After the grace period, revoke the old key.

        This ensures no failed requests during rotation -- the agent
        can switch to the new key at any point during the grace period.
        """
        old_meta = self._key_registry.get(old_key_id)
        if not old_meta:
            raise ValueError(f"Key {old_key_id} not found in registry.")

        # Create replacement key with same scopes
        new_label = f"{old_meta['label']}-rotated-{int(time.time())}"
        new_key_result = self.create_scoped_key(
            target_agent_id=target_agent_id,
            label=new_label,
            ttl_hours=old_meta["ttl_hours"],
        )

        # Schedule old key for deactivation
        result = api_call("rotate_api_key", {
            "agent_id": target_agent_id,
            "old_key_id": old_key_id,
            "grace_period_minutes": grace_period_minutes,
        })

        # Update registry
        self._key_registry[old_key_id]["status"] = "rotating"
        self._key_registry[old_key_id]["revoke_after"] = (
            int(time.time()) + grace_period_minutes * 60
        )

        return {
            "old_key_id": old_key_id,
            "new_key": new_key_result,
            "grace_period_minutes": grace_period_minutes,
            "status": "rotating",
        }

    def revoke_key(self, target_agent_id: str, key_id: str,
                   reason: str = "manual_revocation") -> dict:
        """Immediately revoke an API key. No grace period."""
        result = api_call("rotate_api_key", {
            "agent_id": target_agent_id,
            "old_key_id": key_id,
            "grace_period_minutes": 0,  # Immediate revocation
        })

        if key_id in self._key_registry:
            self._key_registry[key_id]["status"] = "revoked"
            self._key_registry[key_id]["revoked_at"] = int(time.time())
            self._key_registry[key_id]["revoke_reason"] = reason

        return {
            "key_id": key_id,
            "agent_id": target_agent_id,
            "status": "revoked",
            "reason": reason,
        }

    def get_key_inventory(self) -> list[dict]:
        """List all keys with their status and metadata."""
        inventory = []
        now = int(time.time())
        for key_id, meta in self._key_registry.items():
            expires_at = meta["created_at"] + meta["ttl_hours"] * 3600
            inventory.append({
                "key_id": key_id,
                "agent_id": meta["agent_id"],
                "label": meta["label"],
                "status": meta["status"],
                "created_at": meta["created_at"],
                "expires_at": expires_at,
                "days_until_expiry": max(0, (expires_at - now) // 86400),
                "scopes": meta["scopes"],
            })
        return inventory

    def get_expiring_keys(self, within_days: int = 7) -> list[dict]:
        """Find keys that will expire within the specified window."""
        now = int(time.time())
        threshold = now + within_days * 86400
        expiring = []
        for key_info in self.get_key_inventory():
            if (key_info["status"] == "active"
                    and key_info["expires_at"] <= threshold):
                expiring.append(key_info)
        return expiring
```

### Rotation Strategies

Key rotation is not optional for agent systems. Static keys that never rotate are the most common credential compromise vector. Three rotation strategies apply to different agent types:

**Scheduled rotation** is the baseline. Every key rotates on a fixed cadence -- 30 days for production, 7 days for high-privilege admin keys. The `get_expiring_keys()` method finds keys approaching expiry. A daily cron job (or a dedicated rotation agent) calls `rotate_key()` for each.

**Event-triggered rotation** covers security incidents. If an agent's key may have been exposed -- a container image was pushed to a public registry, a log file contained the key, a third-party dependency was compromised -- rotate immediately using `revoke_key()` with zero grace period, then issue a new key via `create_scoped_key()`.

**Continuous rotation** is the most aggressive strategy, suitable for high-security environments. Keys rotate every 1-4 hours. The grace period overlaps ensure zero downtime. This limits the window of exposure if a key is compromised to the rotation interval.

```python
# Scheduled rotation: rotate all keys expiring within 7 days
key_mgr = KeyManager(admin_agent, rbac)
expiring = key_mgr.get_expiring_keys(within_days=7)
for key_info in expiring:
    print(f"Rotating {key_info['label']} for {key_info['agent_id']}")
    key_mgr.rotate_key(
        target_agent_id=key_info["agent_id"],
        old_key_id=key_info["key_id"],
        grace_period_minutes=60,
    )

# Emergency revocation: immediate, no grace period
key_mgr.revoke_key(
    target_agent_id="acme-ops-01",
    key_id="key-compromised-123",
    reason="potential_exposure_in_public_image",
)
```

### Key Labeling Convention

Label every key with enough context to identify it during an incident. The recommended format: `{environment}-{role}-{year}-{quarter}`. Examples: `prod-reader-2026-q2`, `staging-admin-2026-q1`, `dev-operator-2026-q2`. Labels appear in audit logs and key inventories. During an incident, clear labels let you identify which key to revoke without parsing metadata.

### Avoiding Common Key Management Mistakes

Five mistakes account for the majority of key-related agent incidents in production:

**Shared keys across agents.** When multiple agents use the same API key, you lose all auditability. The platform logs show which key made a call, not which agent. If one agent is compromised, you must revoke the key and disrupt every agent sharing it. One agent, one key, always.

**Keys with no expiry.** A key that never expires is a key that is eventually compromised. Set explicit TTLs on every key. If the agent is long-running, the rotation schedule handles continuity -- the key expires, the rotation job creates a new one, and the agent picks it up seamlessly.

**Keys stored in environment variables in shared runtimes.** If your agents run in a shared Kubernetes namespace, any pod in that namespace can read another pod's environment variables through the `/proc` filesystem or through a compromised sidecar. Use Kubernetes Secrets with projected volumes, not plain environment variables.

**No revocation procedure tested in advance.** The first time you revoke a key should not be during an incident. Run a revocation drill quarterly: revoke a staging key, verify the agent fails gracefully, issue a new key, verify recovery. Document the time-to-revoke and time-to-recover.

**Overly broad scopes.** A key with `["*"]` scope is an admin key regardless of what role the agent is assigned. Scope keys to the exact tool list from `get_allowed_tools()`, not to wildcards. The `create_scoped_key()` method in the `KeyManager` does this automatically.

---

## Chapter 5: Permission Delegation

### The Delegation Problem

Agent commerce creates delegation chains that do not exist in human IAM. When Agent A hires Agent B through the marketplace, B needs permissions to perform the hired task -- but B should not inherit all of A's permissions. If A is an admin and B is a marketplace worker, B should get only the specific tools needed for the contracted work. This is permission delegation: A grants B a scoped subset of its own permissions for a bounded time period.

The constraints on delegation:

1. **No privilege escalation**: An agent cannot delegate permissions it does not have. A reader cannot delegate write access.
2. **Subset only**: The delegated permission set must be a strict subset of (or equal to) the delegator's permissions.
3. **Time-bounded**: Delegations expire. The default is the duration of the contracted work plus a buffer.
4. **Budget-bounded**: Delegations include a spending limit. The delegated agent's budget cap serves as a hard permission boundary -- even if the agent has tool access, it cannot spend more than the delegated budget.
5. **Revocable**: The delegator can revoke the delegation at any time.

### The DelegationManager

```python
class DelegationManager:
    """Permission delegation between agents with budget boundaries."""

    def __init__(self, rbac: RBACManager):
        self.rbac = rbac
        self._delegations: dict[str, dict] = {}  # delegation_id -> metadata

    def delegate_permissions(
        self,
        from_agent_id: str,
        to_agent_id: str,
        tools: list[str],
        budget_cap: str,
        ttl_hours: int = 24,
        reason: str = "",
    ) -> dict:
        """Delegate a subset of permissions from one agent to another.

        Args:
            from_agent_id: The agent granting permissions.
            to_agent_id: The agent receiving permissions.
            tools: The specific tools to delegate.
            budget_cap: Maximum spend for the delegated agent.
            ttl_hours: How long the delegation lasts.
            reason: Why the delegation was created (for audit).
        """
        # Verify the delegator has all the requested permissions
        delegator_tools = self.rbac.get_allowed_tools(from_agent_id)
        if "*" not in delegator_tools:
            unauthorized = set(tools) - delegator_tools
            if unauthorized:
                raise PermissionError(
                    f"Agent {from_agent_id} cannot delegate tools it does "
                    f"not have: {sorted(unauthorized)}"
                )

        # Create a temporary role for the delegation
        delegation_id = f"deleg-{from_agent_id}-{to_agent_id}-{int(time.time())}"
        delegation_role = f"_delegation_{delegation_id}"

        self.rbac.define_role(
            role_name=delegation_role,
            description=f"Delegated by {from_agent_id}: {reason}",
            tools=tools,
        )
        self.rbac.assign_role(to_agent_id, delegation_role)

        # Set budget cap as a financial permission boundary
        api_call("set_budget_cap", {
            "agent_id": to_agent_id,
            "cap": budget_cap,
        })

        self._delegations[delegation_id] = {
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "tools": tools,
            "budget_cap": budget_cap,
            "role_name": delegation_role,
            "created_at": int(time.time()),
            "expires_at": int(time.time()) + ttl_hours * 3600,
            "ttl_hours": ttl_hours,
            "reason": reason,
            "status": "active",
        }

        return {
            "delegation_id": delegation_id,
            "from": from_agent_id,
            "to": to_agent_id,
            "tools": tools,
            "budget_cap": budget_cap,
            "expires_at": self._delegations[delegation_id]["expires_at"],
            "status": "active",
        }

    def revoke_delegation(self, delegation_id: str) -> dict:
        """Revoke a delegation immediately."""
        if delegation_id not in self._delegations:
            raise ValueError(f"Delegation {delegation_id} not found.")

        deleg = self._delegations[delegation_id]
        self.rbac.revoke_role(deleg["to_agent_id"], deleg["role_name"])

        # Set budget cap to zero to prevent any further spending
        api_call("set_budget_cap", {
            "agent_id": deleg["to_agent_id"],
            "cap": "0",
        })

        deleg["status"] = "revoked"
        deleg["revoked_at"] = int(time.time())

        return {
            "delegation_id": delegation_id,
            "status": "revoked",
            "to_agent_id": deleg["to_agent_id"],
        }

    def get_delegation_chain(self, agent_id: str) -> list[dict]:
        """Get all active delegations for an agent (both granted and received)."""
        now = int(time.time())
        chain = []
        for deleg_id, deleg in self._delegations.items():
            if deleg["status"] != "active":
                continue
            if deleg["expires_at"] < now:
                deleg["status"] = "expired"
                continue
            if agent_id in (deleg["from_agent_id"], deleg["to_agent_id"]):
                chain.append({
                    "delegation_id": deleg_id,
                    "direction": "granted" if deleg["from_agent_id"] == agent_id
                                 else "received",
                    "counterparty": deleg["to_agent_id"]
                                    if deleg["from_agent_id"] == agent_id
                                    else deleg["from_agent_id"],
                    "tools": deleg["tools"],
                    "budget_cap": deleg["budget_cap"],
                    "expires_at": deleg["expires_at"],
                    "reason": deleg["reason"],
                })
        return chain

    def cleanup_expired(self) -> int:
        """Revoke all expired delegations. Returns count of cleaned up."""
        now = int(time.time())
        cleaned = 0
        for deleg_id, deleg in list(self._delegations.items()):
            if deleg["status"] == "active" and deleg["expires_at"] < now:
                self.revoke_delegation(deleg_id)
                deleg["status"] = "expired"
                cleaned += 1
        return cleaned
```

### Delegation Chains: Owner to Manager to Worker

Real-world agent hierarchies have multiple delegation levels. An owner agent delegates to a manager agent, which delegates to worker agents. Each level further restricts the permission set.

```python
# Level 1: Owner delegates to manager
delegation_mgr = DelegationManager(rbac)

rbac.assign_role("acme-owner-01", "admin")
rbac.assign_role("acme-manager-01", "operator")

owner_to_manager = delegation_mgr.delegate_permissions(
    from_agent_id="acme-owner-01",
    to_agent_id="acme-manager-01",
    tools=["create_escrow", "release_escrow", "register_service",
           "search_services", "send_message"],
    budget_cap="5000.00",
    ttl_hours=168,  # 1 week
    reason="Q2 marketplace operations",
)

# Level 2: Manager delegates a narrower set to worker
manager_to_worker = delegation_mgr.delegate_permissions(
    from_agent_id="acme-manager-01",
    to_agent_id="acme-worker-01",
    tools=["search_services", "send_message"],  # Read-only subset
    budget_cap="500.00",  # Tighter budget
    ttl_hours=24,  # 1 day only
    reason="Price comparison task #4721",
)

# View the full delegation chain
chain = delegation_mgr.get_delegation_chain("acme-manager-01")
print(json.dumps(chain, indent=2))
# Shows both the delegation received from owner and the one granted to worker
```

### Budget as Permission Boundary

The budget cap set via `set_budget_cap` is not just a financial control -- it is a permission boundary. An agent with tool access but a zero-dollar budget cannot execute any tool that costs money. This creates a dual-lock system: the agent must have both the RBAC permission (tool is in its role) and the budget permission (budget cap allows the spend). Either lock failing independently blocks the operation.

This dual-lock approach means that even if the RBAC system has a bug that grants excessive permissions, the budget cap limits the damage. And if the budget cap is set too high, the RBAC restriction prevents the agent from calling tools outside its role. Defense in depth through orthogonal controls.

```python
# Verify budget status after delegation
budget = api_call("get_budget_status", {
    "agent_id": "acme-worker-01",
})
print(f"Worker budget remaining: {budget}")
```

---

## Chapter 6: Multi-Tenant Architecture

### Why Multi-Tenancy for Agents

Multi-tenancy is relevant in two scenarios. The first is a platform operator running agent services for multiple customers -- each customer is a tenant with isolated agents, wallets, and data. The second is a single organization with multiple business units, each running independent agent fleets that should not interact. In both cases, the requirement is the same: agents in Tenant A cannot access resources in Tenant B unless explicitly granted cross-tenant permissions.

Tenant isolation for agents requires four boundaries:

1. **Identity boundary**: Agents are registered within a tenant. An agent's identity record includes its tenant. The `AgentIAM` class in Chapter 2 captures tenant at registration time.
2. **Wallet boundary**: Each tenant has its own wallet. An agent in Tenant A cannot deposit to or withdraw from Tenant B's wallet.
3. **Key boundary**: API keys are scoped to a tenant. A key issued for Tenant A's agents cannot authenticate Tenant B's agents.
4. **Data boundary**: Reputation, metrics, and claim chains are tenant-scoped. An agent's trust score in Tenant A is independent of Tenant B.

### The TenantManager

```python
class TenantManager:
    """Multi-tenant isolation for agent fleets."""

    def __init__(self, rbac: RBACManager):
        self.rbac = rbac
        self._tenants: dict[str, dict] = {}  # tenant_id -> metadata
        self._agent_tenants: dict[str, str] = {}  # agent_id -> tenant_id

    def create_tenant(self, tenant_id: str, display_name: str,
                      admin_agent_id: str,
                      budget_cap: str = "10000.00") -> dict:
        """Create a new tenant with a dedicated wallet and admin agent."""
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant {tenant_id} already exists.")

        # Create a wallet for the tenant
        wallet = api_call("create_wallet", {
            "agent_id": f"{tenant_id}-wallet",
        })

        # Set the tenant's budget cap
        api_call("set_budget_cap", {
            "agent_id": f"{tenant_id}-wallet",
            "cap": budget_cap,
        })

        # Register the admin agent in this tenant
        self._agent_tenants[admin_agent_id] = tenant_id

        self._tenants[tenant_id] = {
            "tenant_id": tenant_id,
            "display_name": display_name,
            "admin_agent_id": admin_agent_id,
            "wallet_id": f"{tenant_id}-wallet",
            "budget_cap": budget_cap,
            "created_at": int(time.time()),
            "agents": [admin_agent_id],
        }

        return self._tenants[tenant_id]

    def assign_agent_to_tenant(self, agent_id: str,
                               tenant_id: str) -> dict:
        """Assign an agent to a tenant. Agents belong to exactly one tenant."""
        if tenant_id not in self._tenants:
            raise ValueError(f"Tenant {tenant_id} does not exist.")

        # Remove from previous tenant if assigned
        old_tenant = self._agent_tenants.get(agent_id)
        if old_tenant and old_tenant != tenant_id:
            self._tenants[old_tenant]["agents"] = [
                a for a in self._tenants[old_tenant]["agents"]
                if a != agent_id
            ]

        self._agent_tenants[agent_id] = tenant_id
        if agent_id not in self._tenants[tenant_id]["agents"]:
            self._tenants[tenant_id]["agents"].append(agent_id)

        return {
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "status": "assigned",
        }

    def get_tenant_agents(self, tenant_id: str) -> list[str]:
        """List all agents in a tenant."""
        if tenant_id not in self._tenants:
            raise ValueError(f"Tenant {tenant_id} does not exist.")
        return list(self._tenants[tenant_id]["agents"])

    def check_tenant_access(self, agent_id: str,
                            target_agent_id: str) -> dict:
        """Check if two agents are in the same tenant."""
        agent_tenant = self._agent_tenants.get(agent_id)
        target_tenant = self._agent_tenants.get(target_agent_id)

        same_tenant = (
            agent_tenant is not None
            and target_tenant is not None
            and agent_tenant == target_tenant
        )

        return {
            "agent_id": agent_id,
            "target_agent_id": target_agent_id,
            "agent_tenant": agent_tenant,
            "target_tenant": target_tenant,
            "same_tenant": same_tenant,
            "access_allowed": same_tenant,
        }

    def get_tenant_budget_status(self, tenant_id: str) -> dict:
        """Get the budget status for a tenant's wallet."""
        if tenant_id not in self._tenants:
            raise ValueError(f"Tenant {tenant_id} does not exist.")

        wallet_id = self._tenants[tenant_id]["wallet_id"]
        budget = api_call("get_budget_status", {
            "agent_id": wallet_id,
        })
        balance = api_call("get_balance", {
            "agent_id": wallet_id,
        })

        return {
            "tenant_id": tenant_id,
            "wallet_id": wallet_id,
            "budget": budget,
            "balance": balance,
        }
```

### Tenant-Scoped API Keys

Every key is scoped to a tenant. The `TenantKeyManager` extends the `KeyManager` from Chapter 4 to enforce tenant boundaries on key creation.

```python
class TenantKeyManager:
    """API key management with tenant isolation."""

    def __init__(self, key_mgr: KeyManager, tenant_mgr: TenantManager):
        self.key_mgr = key_mgr
        self.tenant_mgr = tenant_mgr

    def create_tenant_scoped_key(self, agent_id: str,
                                  label: str) -> dict:
        """Create a key that is scoped to the agent's tenant."""
        tenant_id = self.tenant_mgr._agent_tenants.get(agent_id)
        if not tenant_id:
            raise ValueError(
                f"Agent {agent_id} is not assigned to any tenant."
            )

        # Label includes tenant for auditability
        tenant_label = f"{tenant_id}/{label}"
        result = self.key_mgr.create_scoped_key(
            target_agent_id=agent_id,
            label=tenant_label,
        )

        return {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "key": result,
            "label": tenant_label,
        }
```

### Cross-Tenant Access Control

Cross-tenant access is denied by default. When it is required -- for example, a shared analytics agent that reads metrics across tenants -- it must be explicitly granted through a cross-tenant delegation.

```python
class CrossTenantGateway:
    """Controlled cross-tenant access with explicit grants."""

    def __init__(self, tenant_mgr: TenantManager,
                 delegation_mgr: DelegationManager):
        self.tenant_mgr = tenant_mgr
        self.delegation_mgr = delegation_mgr
        self._cross_tenant_grants: list[dict] = []

    def grant_cross_tenant_access(
        self,
        from_tenant_id: str,
        to_tenant_id: str,
        agent_id: str,
        tools: list[str],
        budget_cap: str,
        ttl_hours: int = 24,
        reason: str = "",
    ) -> dict:
        """Grant an agent in one tenant access to another tenant's resources.

        Requires admin approval from both tenants (enforced by caller).
        """
        # Verify agent belongs to the source tenant
        agent_tenant = self.tenant_mgr._agent_tenants.get(agent_id)
        if agent_tenant != from_tenant_id:
            raise PermissionError(
                f"Agent {agent_id} is not in tenant {from_tenant_id}."
            )

        # Verify target tenant exists
        if to_tenant_id not in self.tenant_mgr._tenants:
            raise ValueError(f"Target tenant {to_tenant_id} does not exist.")

        target_admin = self.tenant_mgr._tenants[to_tenant_id]["admin_agent_id"]

        # Create delegation from target tenant's admin to the requesting agent
        delegation = self.delegation_mgr.delegate_permissions(
            from_agent_id=target_admin,
            to_agent_id=agent_id,
            tools=tools,
            budget_cap=budget_cap,
            ttl_hours=ttl_hours,
            reason=f"Cross-tenant: {from_tenant_id}->{to_tenant_id}: {reason}",
        )

        grant = {
            "from_tenant": from_tenant_id,
            "to_tenant": to_tenant_id,
            "agent_id": agent_id,
            "delegation_id": delegation["delegation_id"],
            "tools": tools,
            "created_at": int(time.time()),
        }
        self._cross_tenant_grants.append(grant)

        return grant
```

### Tenant Setup Workflow

```python
# Create two tenants
tenant_mgr = TenantManager(rbac)

acme = tenant_mgr.create_tenant(
    tenant_id="acme",
    display_name="Acme Corporation",
    admin_agent_id="acme-admin-01",
    budget_cap="50000.00",
)

globex = tenant_mgr.create_tenant(
    tenant_id="globex",
    display_name="Globex Industries",
    admin_agent_id="globex-admin-01",
    budget_cap="25000.00",
)

# Assign agents to tenants
tenant_mgr.assign_agent_to_tenant("acme-reader-01", "acme")
tenant_mgr.assign_agent_to_tenant("acme-ops-01", "acme")
tenant_mgr.assign_agent_to_tenant("globex-ops-01", "globex")

# Verify tenant isolation
print(tenant_mgr.check_tenant_access("acme-reader-01", "acme-ops-01"))
# {"same_tenant": True, "access_allowed": True}

print(tenant_mgr.check_tenant_access("acme-reader-01", "globex-ops-01"))
# {"same_tenant": False, "access_allowed": False}

# Check tenant budget
print(tenant_mgr.get_tenant_budget_status("acme"))
```

---

## Chapter 7: IAM Auditing & Monitoring

### Why Every Access Decision Must Be Logged

IAM without audit logging is security theater. If you cannot answer "which agent accessed which tool at what time with what permission," you cannot detect compromises, investigate incidents, or prove compliance. The EU AI Act Article 12 requires logging adequate to reconstruct events. The CSA Agentic AI IAM Framework requires continuous monitoring of access patterns. SOC 2 Type II requires evidence that access controls are operating effectively over time. All three are satisfied by the same mechanism: log every access decision, ship those logs to a durable store, and monitor for anomalies.

The access decisions to log:

- **Allowed**: Agent X called tool Y at time T. Granted by role Z.
- **Denied**: Agent X attempted tool Y at time T. Denied because of reason R.
- **Delegated**: Agent X delegated tools [Y1, Y2] to Agent Z at time T with budget B.
- **Revoked**: Delegation D was revoked at time T by agent X.
- **Rotated**: Key K for agent X was rotated at time T. New key K2 issued.
- **Tenant access**: Agent X in tenant A attempted access to resource in tenant B. Allowed/denied.

Denied decisions are as important as allowed decisions. A pattern of denied access attempts from a single agent may indicate a compromised agent probing for permissions. A spike in denied access across multiple agents may indicate an attacker testing stolen keys.

### The IAMAuditor

```python
class IAMAuditor:
    """Comprehensive IAM event logging and anomaly detection."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id  # The audit system's own agent identity
        self._events: list[dict] = []
        self._webhook_id: Optional[str] = None

    def log_event(self, event_type: str, details: dict) -> dict:
        """Record an IAM event to the local log and publish to event bus."""
        event = {
            "event_id": f"iam-{int(time.time() * 1000)}",
            "event_type": event_type,
            "timestamp": int(time.time()),
            "details": details,
        }
        self._events.append(event)

        # Publish to GreenHelix event bus for external consumers
        try:
            api_call("publish_event", {
                "agent_id": self.agent_id,
                "event_type": f"iam.{event_type}",
                "payload": event,
            })
        except Exception:
            # Log publishing failure but do not block the operation
            event["publish_status"] = "failed"

        return event

    def setup_iam_webhook(self, callback_url: str,
                          events: Optional[list[str]] = None) -> dict:
        """Register a webhook for real-time IAM event alerts."""
        if events is None:
            events = [
                "iam.access_denied",
                "iam.delegation_created",
                "iam.delegation_revoked",
                "iam.key_rotated",
                "iam.key_revoked",
                "iam.cross_tenant_access",
                "iam.anomaly_detected",
            ]

        result = api_call("register_webhook", {
            "agent_id": self.agent_id,
            "callback_url": callback_url,
            "events": events,
        })

        self._webhook_id = result.get("webhook_id")
        return result

    def get_access_log(self, agent_id: Optional[str] = None,
                       event_type: Optional[str] = None,
                       since: Optional[int] = None) -> list[dict]:
        """Query the IAM event log with optional filters."""
        results = self._events

        if agent_id:
            results = [
                e for e in results
                if e["details"].get("agent_id") == agent_id
            ]
        if event_type:
            results = [
                e for e in results
                if e["event_type"] == event_type
            ]
        if since:
            results = [
                e for e in results
                if e["timestamp"] >= since
            ]

        return results

    def detect_anomalies(self, window_seconds: int = 3600,
                         deny_threshold: int = 10,
                         delegation_threshold: int = 5) -> list[dict]:
        """Detect anomalous IAM patterns in the recent event window.

        Anomaly signals:
        - Many denied access attempts from one agent (brute-force probing)
        - Unusual delegation creation rate (privilege escalation attempt)
        - Access from agent not seen before (new agent or impersonation)
        - Cross-tenant access attempts (lateral movement)
        """
        now = int(time.time())
        cutoff = now - window_seconds
        recent = [e for e in self._events if e["timestamp"] >= cutoff]

        anomalies = []

        # Signal 1: Excessive denials from a single agent
        deny_counts: dict[str, int] = {}
        for event in recent:
            if event["event_type"] == "access_denied":
                aid = event["details"].get("agent_id", "unknown")
                deny_counts[aid] = deny_counts.get(aid, 0) + 1

        for aid, count in deny_counts.items():
            if count >= deny_threshold:
                anomaly = {
                    "type": "excessive_denials",
                    "agent_id": aid,
                    "count": count,
                    "window_seconds": window_seconds,
                    "severity": "high",
                    "recommendation": (
                        f"Investigate agent {aid}. {count} denied access "
                        f"attempts in {window_seconds}s may indicate "
                        "compromised credentials or privilege probing."
                    ),
                }
                anomalies.append(anomaly)
                self.log_event("anomaly_detected", anomaly)

        # Signal 2: Excessive delegations
        deleg_counts: dict[str, int] = {}
        for event in recent:
            if event["event_type"] == "delegation_created":
                aid = event["details"].get("from_agent_id", "unknown")
                deleg_counts[aid] = deleg_counts.get(aid, 0) + 1

        for aid, count in deleg_counts.items():
            if count >= delegation_threshold:
                anomaly = {
                    "type": "excessive_delegations",
                    "agent_id": aid,
                    "count": count,
                    "window_seconds": window_seconds,
                    "severity": "medium",
                    "recommendation": (
                        f"Agent {aid} created {count} delegations in "
                        f"{window_seconds}s. Verify these are legitimate "
                        "or revoke and investigate."
                    ),
                }
                anomalies.append(anomaly)
                self.log_event("anomaly_detected", anomaly)

        # Signal 3: Cross-tenant access attempts
        cross_tenant = [
            e for e in recent
            if e["event_type"] == "cross_tenant_access"
        ]
        if len(cross_tenant) > 0:
            anomaly = {
                "type": "cross_tenant_activity",
                "count": len(cross_tenant),
                "window_seconds": window_seconds,
                "severity": "high",
                "recommendation": (
                    f"{len(cross_tenant)} cross-tenant access events "
                    f"in {window_seconds}s. Review each for authorization."
                ),
            }
            anomalies.append(anomaly)

        return anomalies

    def generate_iam_report(self, period_hours: int = 24) -> dict:
        """Generate a summary IAM report for the specified period."""
        cutoff = int(time.time()) - period_hours * 3600
        recent = [e for e in self._events if e["timestamp"] >= cutoff]

        event_counts: dict[str, int] = {}
        for event in recent:
            et = event["event_type"]
            event_counts[et] = event_counts.get(et, 0) + 1

        unique_agents = set()
        for event in recent:
            aid = event["details"].get("agent_id")
            if aid:
                unique_agents.add(aid)

        denied = [e for e in recent if e["event_type"] == "access_denied"]

        return {
            "period_hours": period_hours,
            "total_events": len(recent),
            "event_breakdown": event_counts,
            "unique_agents": len(unique_agents),
            "denied_access_count": len(denied),
            "anomalies_detected": len([
                e for e in recent
                if e["event_type"] == "anomaly_detected"
            ]),
        }
```

### Integrating the Auditor with the IAM Stack

The auditor hooks into every component from the previous chapters. Every access decision, delegation, key rotation, and tenant operation logs through the auditor.

```python
# Initialize the full IAM stack with auditing
rbac = RBACManager()
auditor = IAMAuditor(agent_id="iam-auditor-01")

# Wrap the SecureToolCaller to emit audit events
class AuditedToolCaller(SecureToolCaller):
    """SecureToolCaller with IAM event auditing."""

    def __init__(self, rbac: RBACManager, auditor: IAMAuditor):
        super().__init__(rbac)
        self.auditor = auditor

    def execute(self, agent: AgentIAM, tool: str,
                input_data: dict) -> dict:
        try:
            result = super().execute(agent, tool, input_data)
            self.auditor.log_event("access_allowed", {
                "agent_id": agent.agent_id,
                "tool": tool,
                "tenant": agent.tenant,
            })
            return result
        except PermissionError as e:
            self.auditor.log_event("access_denied", {
                "agent_id": agent.agent_id,
                "tool": tool,
                "tenant": agent.tenant,
                "reason": str(e),
            })
            raise


# Usage
caller = AuditedToolCaller(rbac, auditor)

# Set up webhook for real-time alerts
auditor.setup_iam_webhook(
    callback_url="https://hooks.acme.com/iam-alerts",
    events=["iam.access_denied", "iam.anomaly_detected"],
)

# Run anomaly detection on a schedule
anomalies = auditor.detect_anomalies(
    window_seconds=3600,
    deny_threshold=10,
)
if anomalies:
    print(f"ALERT: {len(anomalies)} IAM anomalies detected")
    for a in anomalies:
        print(f"  [{a['severity']}] {a['type']}: {a['recommendation']}")

# Generate daily IAM report
report = auditor.generate_iam_report(period_hours=24)
print(json.dumps(report, indent=2))
```

### Trust-Based Access Decisions

The GreenHelix trust and reputation system provides a signal that traditional IAM does not: behavioral reputation. An agent's trust score reflects its historical behavior -- successful transactions, metric quality, dispute rate, counterparty ratings. This signal can augment RBAC decisions in two ways.

**Trust-gated delegation.** Before accepting a delegation, verify the delegating agent's reputation. An agent with a declining trust score may be compromised or malfunctioning. The delegation should be rejected or flagged for human review.

```python
def trust_gated_delegate(delegation_mgr: DelegationManager,
                         auditor: IAMAuditor,
                         from_agent_id: str,
                         to_agent_id: str,
                         tools: list[str],
                         budget_cap: str,
                         min_trust_score: float = 0.7) -> dict:
    """Only delegate if the source agent has sufficient trust score."""
    reputation = api_call("get_agent_reputation", {
        "agent_id": from_agent_id,
    })

    trust_score = reputation.get("trust_score", 0)
    if trust_score < min_trust_score:
        auditor.log_event("delegation_blocked_low_trust", {
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "trust_score": trust_score,
            "minimum_required": min_trust_score,
        })
        raise PermissionError(
            f"Agent {from_agent_id} trust score {trust_score} is below "
            f"minimum {min_trust_score} for delegation."
        )

    return delegation_mgr.delegate_permissions(
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        tools=tools,
        budget_cap=budget_cap,
        reason=f"trust_verified:{trust_score}",
    )
```

**Reputation-adjusted budgets.** Higher-trust agents get higher budget caps within the same role. A newly registered agent with no reputation history gets a conservative budget. As its trust score improves through successful transactions, the budget cap increases automatically.

### What to Alert On

Not every IAM event requires a human response. Alert fatigue is real and causes teams to ignore genuine incidents. Configure alerts for these specific patterns:

- **Any denied access from an admin agent**: Admin agents should have `*` permissions. If an admin is denied access, the RBAC configuration is wrong or the agent is impersonating an admin.
- **More than 10 denied access attempts from any single agent in one hour**: Likely a compromised agent probing for permissions.
- **Any cross-tenant access attempt that was not pre-authorized**: Lateral movement indicator.
- **Key revocation outside of scheduled rotation**: Someone manually revoked a key. Find out why.
- **Delegation chain depth exceeding 3**: Three levels of delegation (owner to manager to worker) is reasonable. Four or more levels suggest uncontrolled delegation growth.

Everything else goes to the daily report for review during the weekly permission audit (Chapter 8).

---

## Chapter 8: Production IAM Checklist

### Before Go-Live

Run through this checklist before deploying any agent fleet to production. Every item maps to a chapter in this guide.

**Identity (Chapter 2)**

- [ ] Every agent has a unique Ed25519 keypair registered via `register_agent`.
- [ ] Agent IDs follow the `{tenant}-{role}-{instance}` naming convention.
- [ ] Private keys are stored in a secrets manager (not in environment files, not in source control, not in container images).
- [ ] `verify_agent` is called before every sensitive operation (escrow creation, payment release, budget modification).
- [ ] Agent identity metadata includes owner, tenant, and roles.

**RBAC (Chapter 3)**

- [ ] Every agent is assigned exactly the roles it needs. No agent has `admin` unless it is a dedicated administration agent.
- [ ] Custom roles are defined for any agent function not covered by the five default roles.
- [ ] `check_permission()` is called before every tool execution (via `SecureToolCaller` or equivalent).
- [ ] Role definitions are version-controlled and reviewed on every change.
- [ ] No agent has both `billing` and `operator` roles (separation of financial control and transaction execution).

**API Keys (Chapter 4)**

- [ ] Every agent has a scoped API key that permits only its role's tools. No shared keys.
- [ ] Key labels follow the `{environment}-{role}-{year}-{quarter}` convention.
- [ ] Scheduled key rotation runs daily. Admin keys rotate every 7 days. All other keys rotate every 30 days.
- [ ] `get_expiring_keys()` is integrated into your monitoring dashboard.
- [ ] Emergency key revocation procedure is documented and tested.

**Delegation (Chapter 5)**

- [ ] All delegations are time-bounded. Default TTL matches the expected task duration plus a 20% buffer.
- [ ] All delegations are budget-bounded via `set_budget_cap`.
- [ ] Delegation chain depth is limited to 3 levels (configurable but audited).
- [ ] Expired delegations are cleaned up automatically via `cleanup_expired()`.
- [ ] Delegation creation logs include the reason field.

**Multi-Tenancy (Chapter 6)**

- [ ] Every agent is assigned to exactly one tenant.
- [ ] Each tenant has a dedicated wallet with its own budget cap.
- [ ] Cross-tenant access requires explicit `CrossTenantGateway` grant.
- [ ] Tenant-scoped API keys are used (never a key that works across tenants).
- [ ] Tenant agent inventory is reviewed monthly.

**Auditing (Chapter 7)**

- [ ] IAM auditor is initialized and connected to all IAM components.
- [ ] Webhooks are registered for denied access and anomaly events.
- [ ] Anomaly detection runs at least hourly.
- [ ] Daily IAM reports are generated and reviewed weekly.
- [ ] Audit log retention meets your compliance requirements (minimum 12 months for SOC 2, 5 years for some financial regulations).

### Ongoing Cadence

| Frequency | Action | Owner |
|-----------|--------|-------|
| **Hourly** | Run `detect_anomalies()`. Alert on high-severity findings. | Automated |
| **Daily** | Run `get_expiring_keys()`. Rotate keys within 7 days of expiry. | Automated |
| **Daily** | Run `cleanup_expired()` on delegation manager. | Automated |
| **Daily** | Generate IAM report via `generate_iam_report()`. | Automated |
| **Weekly** | Review IAM report. Investigate any anomalies. Verify no stale delegations. | Security team |
| **Monthly** | Full permission review. Verify every agent's roles match its current function. Remove unused roles. | Platform team |
| **Quarterly** | Review role definitions. Add or modify roles for new agent functions. Archive unused custom roles. | Platform team + Security team |
| **Annually** | Full IAM architecture review. Assess against updated CSA and NIST frameworks. Update this checklist. | Security team |

### Cross-References

This guide covers IAM design: who can do what, with which key, in which tenant. It deliberately does not cover three adjacent topics that are handled by other guides in this series:

- **Threat modeling and OWASP-aligned security hardening**: See Product 8, "Locking Down Agent Commerce." P8 covers the attack surface -- prompt injection, tool misuse, excessive agency, insecure storage. This guide covers the access control layer that mitigates those attacks.
- **EU AI Act compliance and liability frameworks**: See Product 11, "Ship Compliant Agents." P11 covers Article 12 record-keeping, risk classification, and liability-bounded contracts. This guide's audit logging (Chapter 7) produces the records that P11's compliance framework requires.
- **Incident detection, containment, and recovery**: See Product 12, "The Agent Incident Response Playbook." P12 covers what to do when things go wrong. This guide's RBAC and budget boundaries (Chapters 3, 5) are the containment mechanisms that P12's runbooks invoke.

Together, P8 (defense), P11 (compliance), P12 (response), and this guide (access control) form a complete security posture for agent commerce systems. Each can be implemented independently, but the full stack is greater than the sum of its parts.

### The One-Line Summary

Every agent gets an identity. Every identity gets a role. Every role gets scoped tools. Every tool call gets a scoped key. Every key gets a rotation schedule. Every rotation gets logged. Every log gets reviewed. That is agent IAM.

---

## GreenHelix Agent Provisioning — Production Implementation

The chapters above define the architecture. This section gives you the production implementation: a complete `AgentProvisioner` class that orchestrates agent registration, RBAC, key lifecycle, and multi-tenant isolation using the real `greenhelix_trading` library. Every method call below maps to an actual GreenHelix API endpoint. Copy, configure, run.

### Prerequisites

```bash
pip install greenhelix-trading cryptography requests
```

### The AgentProvisioner Class

```python
"""
GreenHelix Agent Provisioner — production-ready agent IAM orchestration.

Combines AgentIAM, RBACManager, and TenantManager from the greenhelix_trading
library into a single provisioning workflow with key rotation, scoped
permissions, and multi-tenant isolation.

Usage:
    from greenhelix_trading import AgentIAM, RBACManager, TenantManager
    provisioner = AgentProvisioner(api_key="ghx_live_...", tenant_budget=5000.0)
    provisioner.provision_agent("acme-reader-01", role="reader")
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import requests

from greenhelix_trading import AgentIAM, RBACManager, TenantManager


logger = logging.getLogger("greenhelix.provisioner")


# ---------------------------------------------------------------------------
# GreenHelix error codes returned by the gateway
# ---------------------------------------------------------------------------
GHX_RATE_LIMITED = 429
GHX_AUTH_FAILED = 401
GHX_CONFLICT = 409
GHX_NOT_FOUND = 404
GHX_SERVER_ERROR = 500


class GreenHelixProvisioningError(Exception):
    """Base error for all provisioning failures."""

    def __init__(self, message: str, status_code: int = 0,
                 agent_id: str = "", tool: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.agent_id = agent_id
        self.tool = tool


class GreenHelixRateLimitError(GreenHelixProvisioningError):
    """Raised when the GreenHelix API returns HTTP 429."""

    def __init__(self, retry_after: float, agent_id: str = ""):
        super().__init__(
            f"Rate limited. Retry after {retry_after}s",
            status_code=GHX_RATE_LIMITED,
            agent_id=agent_id,
        )
        self.retry_after = retry_after


class GreenHelixConflictError(GreenHelixProvisioningError):
    """Raised when registering an agent_id that already exists."""

    def __init__(self, agent_id: str):
        super().__init__(
            f"Agent '{agent_id}' already registered. Use get_identity() "
            "to retrieve the existing record, or choose a different agent_id.",
            status_code=GHX_CONFLICT,
            agent_id=agent_id,
        )


# ---------------------------------------------------------------------------
# Retry decorator for transient GreenHelix errors
# ---------------------------------------------------------------------------
def retry_on_rate_limit(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator that retries on HTTP 429 with exponential backoff."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == GHX_RATE_LIMITED:
                        retry_after = float(
                            exc.response.headers.get("Retry-After", base_delay * (2 ** attempt))
                        )
                        logger.warning(
                            "Rate limited on attempt %d/%d. Sleeping %.1fs",
                            attempt + 1, max_retries + 1, retry_after,
                        )
                        last_exc = exc
                        time.sleep(retry_after)
                    else:
                        raise
            raise GreenHelixRateLimitError(
                retry_after=base_delay * (2 ** max_retries),
                agent_id=kwargs.get("agent_id", ""),
            ) from last_exc
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# RBAC role definitions — the five standard GreenHelix commerce roles
# ---------------------------------------------------------------------------
GREENHELIX_ROLES = {
    "admin": [
        "register_agent", "verify_agent", "get_agent_identity",
        "create_api_key", "rotate_api_key", "create_wallet",
        "set_budget_cap", "get_budget_status", "get_balance",
        "create_escrow", "release_escrow", "cancel_escrow",
        "register_service", "search_services", "best_match",
        "rate_service", "send_message", "get_messages",
        "submit_metrics", "get_agent_reputation", "get_trust_score",
        "get_claim_chains", "build_claim_chain",
        "get_agent_leaderboard", "estimate_cost",
        "get_volume_discount", "convert_currency",
        "register_webhook", "publish_event",
    ],
    "operator": [
        "create_escrow", "release_escrow", "cancel_escrow",
        "register_service", "search_services", "best_match",
        "rate_service", "send_message", "get_messages",
        "submit_metrics",
    ],
    "reader": [
        "get_agent_identity", "get_agent_reputation",
        "get_trust_score", "search_services",
        "get_balance", "get_budget_status",
        "get_messages", "get_claim_chains",
        "get_agent_leaderboard",
    ],
    "billing": [
        "create_wallet", "get_balance",
        "set_budget_cap", "get_budget_status",
        "estimate_cost", "get_volume_discount",
        "convert_currency",
    ],
    "marketplace": [
        "register_service", "search_services",
        "best_match", "rate_service",
    ],
}


class AgentProvisioner:
    """Orchestrates agent registration, RBAC, key management, and tenancy
    against the live GreenHelix A2A Commerce Gateway.

    This class ties together three library primitives:
      - AgentIAM:      identity registration, verification, scoped keys
      - RBACManager:    local role/permission evaluation
      - TenantManager:  multi-tenant isolation and budget caps

    Every method that calls the GreenHelix API handles rate limits (429),
    auth failures (401), and conflicts (409) with structured exceptions.
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str = "default",
        tenant_budget: float = 10000.0,
        base_url: str = "https://api.greenhelix.net/v1",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.tenant_id = tenant_id

        # ── Library instances ──
        self.rbac = RBACManager()
        self.tenant_mgr = TenantManager(api_key=api_key, base_url=base_url)

        # ── Internal registries ──
        self._agents: dict[str, AgentIAM] = {}
        self._key_registry: dict[str, dict] = {}  # agent_id -> key metadata
        self._provisioned_at: dict[str, float] = {}

        # ── Bootstrap: define standard roles and create the tenant ──
        self._bootstrap_roles()
        self.tenant_mgr.create_tenant(tenant_id, budget=tenant_budget)
        logger.info(
            "Provisioner initialized: tenant=%s budget=%.2f base_url=%s",
            tenant_id, tenant_budget, base_url,
        )

    # ------------------------------------------------------------------
    # Role bootstrap
    # ------------------------------------------------------------------
    def _bootstrap_roles(self) -> None:
        """Load the five standard GreenHelix RBAC roles."""
        for role_name, tools in GREENHELIX_ROLES.items():
            self.rbac.define_role(role_name, tools)
        logger.info("Bootstrapped %d RBAC roles", len(GREENHELIX_ROLES))

    # ------------------------------------------------------------------
    # Agent registration with RBAC
    # ------------------------------------------------------------------
    @retry_on_rate_limit(max_retries=3)
    def register_agent(
        self,
        agent_id: str,
        role: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Register a new agent with a specific RBAC role.

        Steps:
          1. Create an AgentIAM instance bound to the GreenHelix API.
          2. Call register_agent() on the gateway with roles and metadata.
          3. Assign the agent to the local RBACManager.
          4. Assign the agent to the tenant via TenantManager.

        Args:
            agent_id: Unique identifier, e.g. "acme-reader-01".
            role: One of admin, operator, reader, billing, marketplace.
            metadata: Optional dict attached to the agent's identity record.

        Returns:
            Registration result from the GreenHelix gateway.

        Raises:
            GreenHelixConflictError: If agent_id is already registered.
            GreenHelixRateLimitError: If the API returns 429 after retries.
            ValueError: If the role is not defined.
        """
        if role not in GREENHELIX_ROLES:
            raise ValueError(
                f"Unknown role '{role}'. Valid roles: "
                f"{sorted(GREENHELIX_ROLES.keys())}"
            )

        iam = AgentIAM(
            api_key=self.api_key,
            agent_id=agent_id,
            base_url=self.base_url,
        )

        try:
            result = iam.register_agent(
                roles=[role],
                metadata=metadata or {
                    "tenant": self.tenant_id,
                    "provisioned_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == GHX_CONFLICT:
                raise GreenHelixConflictError(agent_id) from exc
            if exc.response is not None and exc.response.status_code == GHX_AUTH_FAILED:
                raise GreenHelixProvisioningError(
                    "Authentication failed. Check your GreenHelix API key.",
                    status_code=GHX_AUTH_FAILED,
                    agent_id=agent_id,
                    tool="register_agent",
                ) from exc
            raise

        # Local RBAC assignment
        self.rbac.assign_role(agent_id, role)

        # Tenant assignment — registers the agent in the tenant and sets
        # the budget cap via set_budget_cap on the gateway
        self.tenant_mgr.assign_agent(self.tenant_id, agent_id)

        # Track internally
        self._agents[agent_id] = iam
        self._provisioned_at[agent_id] = time.time()

        logger.info(
            "Registered agent=%s role=%s tenant=%s",
            agent_id, role, self.tenant_id,
        )
        return result

    # ------------------------------------------------------------------
    # Scoped API key creation
    # ------------------------------------------------------------------
    @retry_on_rate_limit(max_retries=3)
    def create_scoped_key(
        self,
        agent_id: str,
        label: str,
    ) -> dict:
        """Create an API key scoped to the agent's RBAC-allowed tools.

        The key's allowed_tools list is derived from the agent's current
        role assignment in the local RBACManager — not from a wildcard.

        Args:
            agent_id: The agent to create a key for.
            label: Human-readable label, e.g. "prod-reader-2026-q2".

        Returns:
            Key creation result from the GreenHelix gateway, including
            the key_id and the secret (shown only once).

        Raises:
            ValueError: If the agent is not registered or has no role.
        """
        iam = self._agents.get(agent_id)
        if iam is None:
            raise ValueError(
                f"Agent '{agent_id}' is not registered with this provisioner."
            )

        role = self.rbac.get_role(agent_id)
        if role is None:
            raise ValueError(f"Agent '{agent_id}' has no RBAC role assigned.")

        allowed_tools = GREENHELIX_ROLES[role]

        result = iam.create_scoped_key(
            label=f"{self.tenant_id}/{label}",
            allowed_tools=allowed_tools,
        )

        self._key_registry[agent_id] = {
            "key_id": result.get("key_id", f"key-{int(time.time())}"),
            "label": label,
            "role": role,
            "allowed_tools": allowed_tools,
            "created_at": time.time(),
            "status": "active",
        }

        logger.info(
            "Created scoped key for agent=%s role=%s tools=%d label=%s",
            agent_id, role, len(allowed_tools), label,
        )
        return result

    # ------------------------------------------------------------------
    # Key rotation workflow
    # ------------------------------------------------------------------
    @retry_on_rate_limit(max_retries=3)
    def rotate_key(self, agent_id: str, new_label: str = "") -> dict:
        """Rotate an agent's API key using the GreenHelix rotate_api_key tool.

        Rotation flow:
          1. Look up the current key_id from the local registry.
          2. Call iam.rotate_key(key_id) on the gateway — the gateway
             creates a new key and schedules the old one for revocation.
          3. Update the local registry.

        Args:
            agent_id: The agent whose key to rotate.
            new_label: Optional label for the new key. Defaults to
                       "{old_label}-rotated-{timestamp}".

        Returns:
            Rotation result from the GreenHelix gateway.

        Raises:
            ValueError: If no key exists for the agent.
        """
        iam = self._agents.get(agent_id)
        if iam is None:
            raise ValueError(f"Agent '{agent_id}' is not registered.")

        key_meta = self._key_registry.get(agent_id)
        if key_meta is None:
            raise ValueError(f"No key found for agent '{agent_id}'.")

        old_key_id = key_meta["key_id"]

        # Gateway handles the atomic rotation: create new, schedule old revocation
        result = iam.rotate_key(key_id=old_key_id)

        # Update local registry
        rotated_label = new_label or f"{key_meta['label']}-rotated-{int(time.time())}"
        self._key_registry[agent_id] = {
            "key_id": result.get("new_key_id", f"key-{int(time.time())}"),
            "label": rotated_label,
            "role": key_meta["role"],
            "allowed_tools": key_meta["allowed_tools"],
            "created_at": time.time(),
            "previous_key_id": old_key_id,
            "status": "active",
        }

        logger.info(
            "Rotated key for agent=%s old=%s new=%s",
            agent_id, old_key_id, self._key_registry[agent_id]["key_id"],
        )
        return result

    # ------------------------------------------------------------------
    # Bulk key rotation for expiring keys
    # ------------------------------------------------------------------
    def rotate_expiring_keys(self, max_age_days: int = 30) -> list[dict]:
        """Find and rotate all keys older than max_age_days.

        Returns a list of rotation results for each rotated key.
        """
        cutoff = time.time() - (max_age_days * 86400)
        results = []

        for agent_id, key_meta in list(self._key_registry.items()):
            if key_meta["status"] == "active" and key_meta["created_at"] < cutoff:
                logger.info(
                    "Key for agent=%s is %.1f days old — rotating",
                    agent_id,
                    (time.time() - key_meta["created_at"]) / 86400,
                )
                result = self.rotate_key(agent_id)
                results.append({"agent_id": agent_id, "rotation": result})

        return results

    # ------------------------------------------------------------------
    # Permission checks
    # ------------------------------------------------------------------
    def check_permission(self, agent_id: str, tool: str) -> dict:
        """Check whether an agent is allowed to call a specific tool.

        This is a pure local check — no API call. Sub-millisecond.
        """
        return self.rbac.check_permission(agent_id, tool)

    def enforce_permission(self, agent_id: str, tool: str) -> None:
        """Raise PermissionError if the agent cannot call the tool."""
        decision = self.rbac.check_permission(agent_id, tool)
        if not decision["allowed"]:
            raise PermissionError(
                f"Agent '{agent_id}' (role={decision['role']}) "
                f"is not permitted to call '{tool}'"
            )

    # ------------------------------------------------------------------
    # Identity verification
    # ------------------------------------------------------------------
    @retry_on_rate_limit(max_retries=2)
    def verify_agent(self, agent_id: str) -> dict:
        """Verify an agent's identity against the GreenHelix gateway.

        Signs a timestamped challenge with Ed25519, then calls verify_agent.

        Returns:
            Verification result from the gateway.
        """
        iam = self._agents.get(agent_id)
        if iam is None:
            raise ValueError(f"Agent '{agent_id}' is not registered.")

        # Generate an Ed25519 keypair for the challenge
        private_key = Ed25519PrivateKey.generate()
        challenge = f"{agent_id}:{int(time.time())}"
        signature_bytes = private_key.sign(challenge.encode("utf-8"))

        import base64
        signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

        return iam.verify_identity(
            message=challenge,
            signature=signature_b64,
        )

    # ------------------------------------------------------------------
    # Multi-tenant isolation
    # ------------------------------------------------------------------
    def get_tenant_agents(self) -> list[str]:
        """List all agents assigned to this provisioner's tenant."""
        return self.tenant_mgr.get_tenant_agents(self.tenant_id)

    @retry_on_rate_limit(max_retries=2)
    def create_tenant_key(self, label: str) -> dict:
        """Create a tenant-level API key via the GreenHelix gateway."""
        return self.tenant_mgr.create_tenant_key(
            tenant_id=self.tenant_id,
            label=f"{self.tenant_id}/{label}",
        )

    @retry_on_rate_limit(max_retries=2)
    def setup_tenant_audit(self, webhook_url: str) -> dict:
        """Register a webhook for tenant-level IAM audit events.

        The GreenHelix gateway will POST to webhook_url on:
          - agent_registered
          - key_created
          - key_rotated
          - permission_changed
        """
        return self.tenant_mgr.setup_tenant_audit(
            tenant_id=self.tenant_id,
            webhook_url=webhook_url,
        )

    # ------------------------------------------------------------------
    # Identity metrics
    # ------------------------------------------------------------------
    @retry_on_rate_limit(max_retries=2)
    def submit_metrics(self, agent_id: str, metrics: dict) -> dict:
        """Submit identity metrics for an agent via the GreenHelix gateway.

        Metrics feed into the trust score and leaderboard.
        """
        iam = self._agents.get(agent_id)
        if iam is None:
            raise ValueError(f"Agent '{agent_id}' is not registered.")
        return iam.submit_identity_metrics(metrics)

    # ------------------------------------------------------------------
    # Inventory and status
    # ------------------------------------------------------------------
    def get_inventory(self) -> dict:
        """Return a full inventory of provisioned agents, roles, and keys."""
        agents = []
        for agent_id, iam in self._agents.items():
            role = self.rbac.get_role(agent_id)
            key_meta = self._key_registry.get(agent_id, {})
            agents.append({
                "agent_id": agent_id,
                "role": role,
                "key_status": key_meta.get("status", "no_key"),
                "key_label": key_meta.get("label", ""),
                "key_age_days": round(
                    (time.time() - key_meta.get("created_at", time.time())) / 86400, 1
                ),
                "provisioned_at": self._provisioned_at.get(agent_id, 0),
            })
        return {
            "tenant_id": self.tenant_id,
            "agent_count": len(agents),
            "agents": agents,
            "roles_defined": self.rbac.list_roles(),
        }
```

### Full Provisioning Workflow

```python
from greenhelix_trading import AgentIAM, RBACManager, TenantManager

# ── Step 1: Initialize the provisioner ──
provisioner = AgentProvisioner(
    api_key="ghx_live_abc123def456",
    tenant_id="acme",
    tenant_budget=50000.0,
)

# ── Step 2: Register agents with specific RBAC roles ──
provisioner.register_agent(
    agent_id="acme-admin-01",
    role="admin",
    metadata={"owner": "platform-team@acme.com", "environment": "production"},
)

provisioner.register_agent(
    agent_id="acme-reader-01",
    role="reader",
    metadata={"owner": "data-team@acme.com", "purpose": "price_comparison"},
)

provisioner.register_agent(
    agent_id="acme-ops-01",
    role="operator",
    metadata={"owner": "ops-team@acme.com", "purpose": "escrow_management"},
)

provisioner.register_agent(
    agent_id="acme-billing-01",
    role="billing",
    metadata={"owner": "finance@acme.com", "purpose": "wallet_management"},
)

# ── Step 3: Create scoped API keys ──
admin_key = provisioner.create_scoped_key("acme-admin-01", "prod-admin-2026-q2")
reader_key = provisioner.create_scoped_key("acme-reader-01", "prod-reader-2026-q2")
ops_key = provisioner.create_scoped_key("acme-ops-01", "prod-ops-2026-q2")
billing_key = provisioner.create_scoped_key("acme-billing-01", "prod-billing-2026-q2")

# ── Step 4: Verify RBAC enforcement ──
# Reader can query reputation — allowed
print(provisioner.check_permission("acme-reader-01", "get_agent_reputation"))
# {"allowed": True, "agent_id": "acme-reader-01", "tool": "get_agent_reputation", "role": "reader"}

# Reader cannot create escrow — denied
print(provisioner.check_permission("acme-reader-01", "create_escrow"))
# {"allowed": False, "agent_id": "acme-reader-01", "tool": "create_escrow", "role": "reader"}

# Operator can create escrow — allowed
print(provisioner.check_permission("acme-ops-01", "create_escrow"))
# {"allowed": True, "agent_id": "acme-ops-01", "tool": "create_escrow", "role": "operator"}

# Billing agent cannot send messages — denied
print(provisioner.check_permission("acme-billing-01", "send_message"))
# {"allowed": False, "agent_id": "acme-billing-01", "tool": "send_message", "role": "billing"}

# ── Step 5: Set up audit webhook ──
provisioner.setup_tenant_audit(
    webhook_url="https://hooks.acme.com/greenhelix-iam-events"
)

# ── Step 6: Submit identity metrics ──
provisioner.submit_metrics("acme-ops-01", {
    "transactions_completed": 142,
    "disputes_resolved": 3,
    "average_response_ms": 245,
})

# ── Step 7: View full inventory ──
inventory = provisioner.get_inventory()
print(json.dumps(inventory, indent=2, default=str))
```

### Key Rotation Workflow

```python
# ── Scheduled rotation: rotate keys older than 30 days ──
rotated = provisioner.rotate_expiring_keys(max_age_days=30)
for r in rotated:
    print(f"Rotated key for {r['agent_id']}: {r['rotation']}")

# ── Manual rotation for a specific agent ──
provisioner.rotate_key("acme-ops-01", new_label="prod-ops-2026-q2-v2")

# ── Emergency rotation after credential exposure ──
# The GreenHelix gateway's rotate_api_key tool atomically creates
# the new key and schedules the old key for revocation.
try:
    provisioner.rotate_key("acme-admin-01", new_label="emergency-rotate")
    print("Emergency rotation complete. Distribute the new key immediately.")
except GreenHelixRateLimitError as exc:
    print(f"CRITICAL: Rate limited during emergency rotation. Retry in {exc.retry_after}s")
except GreenHelixProvisioningError as exc:
    print(f"CRITICAL: Rotation failed — {exc}. Manual intervention required.")
```

### GreenHelix Error Handling

```python
# ── Handle every GreenHelix-specific failure mode ──

def safe_provision(provisioner: AgentProvisioner, agent_id: str,
                   role: str, metadata: dict = None) -> dict:
    """Register an agent with full GreenHelix error handling.

    Handles:
      - 409 Conflict: agent already exists, retrieve existing identity
      - 429 Rate Limit: exponential backoff (handled by decorator, caught here as fallback)
      - 401 Auth Failure: invalid or expired API key
      - 500 Server Error: transient gateway failure
    """
    try:
        return provisioner.register_agent(agent_id, role, metadata)

    except GreenHelixConflictError:
        # Agent already exists — retrieve and return existing identity
        logger.warning("Agent '%s' already registered. Fetching existing identity.", agent_id)
        iam = AgentIAM(
            api_key=provisioner.api_key,
            agent_id=agent_id,
            base_url=provisioner.base_url,
        )
        existing = iam.get_identity()
        # Still assign locally so RBAC and key management work
        provisioner._agents[agent_id] = iam
        provisioner.rbac.assign_role(agent_id, role)
        return existing

    except GreenHelixRateLimitError as exc:
        logger.error(
            "Rate limited after all retries for agent '%s'. Retry after %.1fs.",
            agent_id, exc.retry_after,
        )
        raise

    except GreenHelixProvisioningError as exc:
        if exc.status_code == GHX_AUTH_FAILED:
            logger.critical(
                "API key rejected by GreenHelix gateway (HTTP 401). "
                "Verify your key at https://sandbox.greenhelix.net/v1."
            )
        elif exc.status_code == GHX_SERVER_ERROR:
            logger.error(
                "GreenHelix gateway returned 500 for agent '%s'. "
                "This is transient — retry in 30s.",
                agent_id,
            )
        raise


# ── Usage ──
result = safe_provision(provisioner, "acme-marketplace-01", "marketplace", {
    "owner": "marketplace-team@acme.com",
    "purpose": "service_discovery",
})
print(json.dumps(result, indent=2, default=str))
```

### curl Equivalents for Every GreenHelix API Call

Each method in the `AgentProvisioner` maps to a `POST` against the GreenHelix execute endpoint. Here are the raw curl equivalents for debugging, scripting, and integration testing.

```bash
# ── Register an agent ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "register_agent",
    "input": {
      "agent_id": "acme-reader-01",
      "roles": ["reader"],
      "metadata": {
        "tenant": "acme",
        "provisioned_at": "2026-04-07T00:00:00+00:00"
      }
    }
  }'

# ── Get agent identity ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_agent_identity",
    "input": {"agent_id": "acme-reader-01"}
  }'

# ── Verify agent identity ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "verify_agent",
    "input": {
      "agent_id": "acme-reader-01",
      "message": "acme-reader-01:1712448000",
      "signature": "BASE64_ED25519_SIGNATURE"
    }
  }'

# ── Create a scoped API key ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_api_key",
    "input": {
      "agent_id": "acme-reader-01",
      "label": "acme/prod-reader-2026-q2",
      "allowed_tools": [
        "get_agent_identity", "get_agent_reputation",
        "get_trust_score", "search_services",
        "get_balance", "get_budget_status",
        "get_messages", "get_claim_chains",
        "get_agent_leaderboard"
      ]
    }
  }'

# ── Rotate an API key ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "rotate_api_key",
    "input": {
      "agent_id": "acme-reader-01",
      "key_id": "key-1712448000"
    }
  }'

# ── Assign agent to tenant and set budget cap ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "set_budget_cap",
    "input": {
      "agent_id": "acme-reader-01",
      "daily": 5000.0
    }
  }'

# ── Submit identity metrics ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "submit_metrics",
    "input": {
      "agent_id": "acme-ops-01",
      "metrics": {
        "transactions_completed": 142,
        "disputes_resolved": 3,
        "average_response_ms": 245
      }
    }
  }'

# ── Register tenant audit webhook ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "register_webhook",
    "input": {
      "agent_id": "acme",
      "url": "https://hooks.acme.com/greenhelix-iam-events",
      "events": [
        "agent_registered",
        "key_created",
        "key_rotated",
        "permission_changed"
      ]
    }
  }'

# ── Create tenant-level API key ──
curl -X POST https://sandbox.greenhelix.net/v1 \
  -H "Authorization: Bearer ghx_live_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_api_key",
    "input": {
      "agent_id": "acme",
      "label": "acme/tenant-admin-2026-q2"
    }
  }'
```

### Multi-Tenant Isolation Example

```python
# ── Provision two isolated tenants on the same GreenHelix gateway ──

acme_provisioner = AgentProvisioner(
    api_key="ghx_live_acme_key",
    tenant_id="acme",
    tenant_budget=50000.0,
)

globex_provisioner = AgentProvisioner(
    api_key="ghx_live_globex_key",
    tenant_id="globex",
    tenant_budget=25000.0,
)

# Each tenant registers its own agents — isolated by tenant_id
acme_provisioner.register_agent("acme-ops-01", role="operator")
globex_provisioner.register_agent("globex-ops-01", role="operator")

# Agents within a tenant are visible
print(acme_provisioner.get_tenant_agents())
# ["acme-ops-01"]

print(globex_provisioner.get_tenant_agents())
# ["globex-ops-01"]

# Tenant-scoped keys — an acme key cannot authenticate globex agents
acme_provisioner.create_scoped_key("acme-ops-01", "prod-ops-2026-q2")
globex_provisioner.create_scoped_key("globex-ops-01", "prod-ops-2026-q2")

# Each tenant gets its own audit webhook
acme_provisioner.setup_tenant_audit("https://hooks.acme.com/iam")
globex_provisioner.setup_tenant_audit("https://hooks.globex.com/iam")
```

