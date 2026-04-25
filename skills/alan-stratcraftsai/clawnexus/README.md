# clawnexus-skill

ClawNexus Skill for OpenClaw — query and manage AI instances from within an OpenClaw conversation.

## Installation

```bash
npm install clawnexus-skill
```

## Prerequisites

The `clawnexus` daemon must be running:

```bash
npm install -g clawnexus
clawnexus start
```

## Requirements

Requires `clawnexus >= 0.2.0`.

## Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `list` | List all known instances | — |
| `info` | Get details for a specific instance | `name` |
| `scan` | Scan the local network for instances | — |
| `alias` | Set a friendly alias for an instance | `id`, `alias` |
| `connect` | Get WebSocket URL for an instance | `name` |
| `health` | Check daemon status | — |
| `resolve` | Resolve a `.claw` name to an instance (Registry, v0.2+) | `name` |

> `id` and `name` parameters accept any identifier in the resolve chain: alias, auto\_name, display\_name, agent\_id, IP address, or `address:port`.

## Usage

```typescript
import { handleSkillRequest } from "clawnexus-skill";

// List all instances
const result = await handleSkillRequest({ action: "list" });
// { success: true, data: { count: 2, instances: [...] } }

// Get instance info
const info = await handleSkillRequest({
  action: "info",
  params: { name: "home" },
});

// Scan the network
const scan = await handleSkillRequest({ action: "scan" });

// Set an alias (id accepts alias, auto_name, address, or address:port)
const alias = await handleSkillRequest({
  action: "alias",
  params: { id: "olivia", alias: "home" },
});

// Get connection URL
const conn = await handleSkillRequest({
  action: "connect",
  params: { name: "home" },
});
// { success: true, data: { url: "ws://192.168.1.10:18789" } }

// Resolve a .claw name (requires Registry, clawnexus >= 0.2.0)
const resolved = await handleSkillRequest({
  action: "resolve",
  params: { name: "myagent.id.claw" },
});
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `CLAWNEXUS_API` | Daemon API URL | `http://localhost:17890` |

## License

MIT
