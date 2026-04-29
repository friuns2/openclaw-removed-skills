> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Getting Started

# Getting Started

Goal: go from zero to a first working chat with minimal setup.

<Info>
  Fastest chat: open the Control UI (no channel setup needed). Run `openclaw dashboard`
  and chat in the browser, or open `http://127.0.0.1:18789/` on the
  <Tooltip headline="Gateway host" tip="The machine running the OpenClaw gateway service.">gateway host</Tooltip>.
  Docs: [Dashboard](/web/dashboard) and [Control UI](/web/control-ui).
</Info>

## Prereqs

* Node 24 recommended (Node 22 LTS, currently `22.16+`, still supported for compatibility)

<Tip>
  Check your Node version with `node --version` if you are unsure.
</Tip>

## Quick setup (CLI)

<Steps>
  <Step title="Install OpenClaw (recommended)">
    <Tabs>
      <Tab title="macOS/Linux">
        ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
        curl -fsSL https://openclaw.ai/install.sh | bash
        ```

        <img src="https://mintcdn.com/clawdhub/U8jr7qEbUc9OU9YR/assets/install-script.svg?fit=max&auto=format&n=U8jr7qEbUc9OU9YR&q=85&s=50706f81e3210a610262f14facb11f65" alt="Install Script Process" className="rounded-lg" width="1370" height="581" data-path="assets/install-script.svg" />
      </Tab>

      <Tab title="Windows (PowerShell)">
        ```powershell  theme={"theme":{"light":"min-light","dark":"min-dark"}}
        iwr -useb https://openclaw.ai/install.ps1 | iex
        ```
      </Tab>
    </Tabs>

    <Note>
      Other install methods and requirements: [Install](/install).
    </Note>
  </Step>

  <Step title="Run onboarding">
    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw onboard --install-daemon
    ```

    Onboarding configures auth, gateway settings, and optional channels.
    See [Onboarding (CLI)](/start/wizard) for details.
  </Step>

  <Step title="Check the Gateway">
    If you installed the service, it should already be running:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw gateway status
    ```
  </Step>

  <Step title="Open the Control UI">
    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw dashboard
    ```
  </Step>
</Steps>

<Check>
  If the Control UI loads, your Gateway is ready for use.
</Check>

## Optional checks and extras

<AccordionGroup>
  <Accordion title="Run the Gateway in the foreground">
    Useful for quick tests or troubleshooting.

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw gateway --port 18789
    ```
  </Accordion>

  <Accordion title="Send a test message">
    Requires a configured channel.

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw message send --target +15555550123 --message "Hello from OpenClaw"
    ```
  </Accordion>
</AccordionGroup>

## Useful environment variables

If you run OpenClaw as a service account or want custom config/state locations:

* `OPENCLAW_HOME` sets the home directory used for internal path resolution.
* `OPENCLAW_STATE_DIR` overrides the state directory.
* `OPENCLAW_CONFIG_PATH` overrides the config file path.

Full environment variable reference: [Environment vars](/help/environment).

## Go deeper

<Columns>
  <Card title="Onboarding (CLI)" href="/start/wizard">
    Full CLI onboarding reference and advanced options.
  </Card>

  <Card title="macOS app onboarding" href="/start/onboarding">
    First run flow for the macOS app.
  </Card>
</Columns>

## What you will have

* A running Gateway
* Auth configured
* Control UI access or a connected channel

## Next steps

* DM safety and approvals: [Pairing](/channels/pairing)
* Connect more channels: [Channels](/channels)
* Advanced workflows and from source: [Setup](/start/setup)


Built with [Mintlify](https://mintlify.com).