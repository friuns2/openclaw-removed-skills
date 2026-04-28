> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# reset

# `openclaw reset`

Reset local config/state (keeps the CLI installed).

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw backup create
openclaw reset
openclaw reset --dry-run
openclaw reset --scope config+creds+sessions --yes --non-interactive
```

Run `openclaw backup create` first if you want a restorable snapshot before removing local state.


Built with [Mintlify](https://mintlify.com).