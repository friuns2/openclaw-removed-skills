# Examples

## Provider setup note

This skill works with any OpenClaw text provider. A common setup is:

- `openai-codex/gpt-5.4` for the main agent model
- `google/gemini-3.1-flash-image-preview` for image generation

Image generation is optional. Threads image publishing still requires a final reachable `media_url`.

Run commands from:

```bash
cd /opt/threads-service-ts/threads-service
```

## Publish now

User intent:

`Post this to Threads from main-brand right now`

Command:

```bash
threadsctl publish text --account main-brand --text "..." --confirmed
```

## Create a draft first

User intent:

`Prepare a Threads draft for review`

Command:

```bash
threadsctl draft create --account main-brand --type text --text "..." --created-by "OpenClaw"
```

## Publish an image

User intent:

`Post this image with a caption`

Command:

```bash
threadsctl publish image --account main-brand --file "/root/.openclaw/media/tool-image-generation/image-1---real-file.jpg" --text "..." --alt-text "..." --confirmed
```

## Generate an image, then post it

User intent:

`Create an image for this post and then publish it to Threads`

Recommended flow:

1. Use the configured image generation provider to create the asset.
2. If OpenClaw saved the result to `/root/.openclaw/media/...`, publish it with `--file`.
3. Use `--media-url` only for already hosted public images.

Preferred command for local OpenClaw output:

```bash
threadsctl publish image --account main-brand --file "/root/.openclaw/media/tool-image-generation/generated-image.jpg" --text "..." --alt-text "..." --confirmed
```

Hosted-image fallback:

```bash
threadsctl publish image --account main-brand --media-url "https://example.com/generated-image.jpg" --text "..." --alt-text "..." --confirmed
```

## Connect another Threads account

User intent:

`Connect a second Threads account called client-two`

Command:

```bash
threadsctl auth connect-url --label client-two
```

Then return the generated URL to the user and instruct them to complete OAuth in the browser.

## Inspect accounts

User intent:

`Show me connected Threads accounts`

Command:

```bash
threadsctl accounts list
```

## Inspect recent published posts

User intent:

`Show published posts for main-brand`

Command:

```bash
threadsctl published list --account main-brand
```
