// ClawNexus Skill — OpenClaw Skill entry point
// Queries clawnexus daemon HTTP API at localhost:17890

const API_URL = process.env.CLAWNEXUS_API ?? "http://localhost:17890";

interface SkillRequest {
  action: string;
  params?: Record<string, string>;
}

interface SkillResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}

async function callDaemon(method: string, path: string, body?: unknown): Promise<{ ok: boolean; data: unknown }> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch {
    return { ok: false, data: { error: "Cannot connect to ClawNexus daemon" } };
  }
}

export async function handleSkillRequest(request: SkillRequest): Promise<SkillResponse> {
  switch (request.action) {
    case "list": {
      const { ok, data } = await callDaemon("GET", "/instances");
      return ok
        ? { success: true, data }
        : { success: false, error: (data as { error?: string }).error };
    }

    case "info": {
      const name = request.params?.name;
      if (!name) return { success: false, error: "Missing instance name" };
      const { ok, data } = await callDaemon("GET", `/instances/${encodeURIComponent(name)}`);
      return ok
        ? { success: true, data }
        : { success: false, error: "Instance not found" };
    }

    case "scan": {
      const { ok, data } = await callDaemon("POST", "/scan");
      return ok
        ? { success: true, data }
        : { success: false, error: (data as { error?: string }).error };
    }

    case "alias": {
      const id = request.params?.id;
      const alias = request.params?.alias;
      if (!id || !alias) return { success: false, error: "Missing id or alias" };
      const { ok, data } = await callDaemon("PUT", `/instances/${encodeURIComponent(id)}/alias`, { alias });
      return ok
        ? { success: true, data }
        : { success: false, error: (data as { error?: string }).error };
    }

    case "connect": {
      const name = request.params?.name;
      if (!name) return { success: false, error: "Missing instance name" };
      const { ok, data } = await callDaemon("GET", `/instances/${encodeURIComponent(name)}`);
      if (!ok) return { success: false, error: "Instance not found" };
      const inst = data as { address: string; gateway_port: number; tls: boolean };
      const protocol = inst.tls ? "wss" : "ws";
      return { success: true, data: { url: `${protocol}://${inst.address}:${inst.gateway_port}` } };
    }

    case "health": {
      const { ok, data } = await callDaemon("GET", "/health");
      return ok
        ? { success: true, data }
        : { success: false, error: "Daemon not available" };
    }

    case "resolve": {
      const name = request.params?.name;
      if (!name) return { success: false, error: "Missing .claw name" };
      const { ok, data } = await callDaemon("GET", `/resolve/${encodeURIComponent(name)}`);
      return ok
        ? { success: true, data }
        : { success: false, error: "Name not found" };
    }

    default:
      return { success: false, error: `Unknown action: ${request.action}` };
  }
}
