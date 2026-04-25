import { describe, it, expect, beforeEach, vi } from "vitest";
import { handleSkillRequest } from "../src/index.js";

describe("Skill handleSkillRequest", () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
  });

  function mockOk(data: unknown) {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => data,
    });
  }

  function mockError(data: unknown) {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => data,
    });
  }

  describe("action: list", () => {
    it("returns instances on success", async () => {
      mockOk({ count: 1, instances: [{ agent_id: "a1" }] });
      const result = await handleSkillRequest({ action: "list" });
      expect(result.success).toBe(true);
      expect((result.data as any).count).toBe(1);
    });

    it("returns error on failure", async () => {
      mockError({ error: "Failed" });
      const result = await handleSkillRequest({ action: "list" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Failed");
    });
  });

  describe("action: info", () => {
    it("returns instance info", async () => {
      mockOk({ agent_id: "a1", display_name: "Test" });
      const result = await handleSkillRequest({ action: "info", params: { name: "a1" } });
      expect(result.success).toBe(true);
    });

    it("requires name param", async () => {
      const result = await handleSkillRequest({ action: "info" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Missing instance name");
    });

    it("returns error when not found", async () => {
      mockError({ error: "Not found" });
      const result = await handleSkillRequest({ action: "info", params: { name: "unknown" } });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Instance not found");
    });
  });

  describe("action: scan", () => {
    it("returns scan results", async () => {
      mockOk({ discovered: 2, instances: [] });
      const result = await handleSkillRequest({ action: "scan" });
      expect(result.success).toBe(true);
    });

    it("returns error on failure", async () => {
      mockError({ error: "Scan failed" });
      const result = await handleSkillRequest({ action: "scan" });
      expect(result.success).toBe(false);
    });
  });

  describe("action: alias", () => {
    it("sets alias successfully", async () => {
      mockOk({ status: "ok", agent_id: "a1", alias: "home" });
      const result = await handleSkillRequest({ action: "alias", params: { id: "a1", alias: "home" } });
      expect(result.success).toBe(true);
    });

    it("requires id and alias params", async () => {
      const result = await handleSkillRequest({ action: "alias", params: { id: "a1" } });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Missing id or alias");
    });

    it("requires params object", async () => {
      const result = await handleSkillRequest({ action: "alias" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Missing id or alias");
    });
  });

  describe("action: connect", () => {
    it("returns ws URL for instance", async () => {
      mockOk({ agent_id: "a1", address: "192.168.1.10", gateway_port: 18789, tls: false });
      const result = await handleSkillRequest({ action: "connect", params: { name: "a1" } });
      expect(result.success).toBe(true);
      expect((result.data as any).url).toBe("ws://192.168.1.10:18789");
    });

    it("returns wss URL for TLS instance", async () => {
      mockOk({ agent_id: "a1", address: "192.168.1.10", gateway_port: 18789, tls: true });
      const result = await handleSkillRequest({ action: "connect", params: { name: "a1" } });
      expect((result.data as any).url).toBe("wss://192.168.1.10:18789");
    });

    it("requires name param", async () => {
      const result = await handleSkillRequest({ action: "connect" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Missing instance name");
    });

    it("returns error when instance not found", async () => {
      mockError({ error: "Not found" });
      const result = await handleSkillRequest({ action: "connect", params: { name: "unknown" } });
      expect(result.success).toBe(false);
    });
  });

  describe("action: health", () => {
    it("returns daemon health", async () => {
      mockOk({ status: "ok", service: "clawnexus-daemon" });
      const result = await handleSkillRequest({ action: "health" });
      expect(result.success).toBe(true);
    });

    it("returns error when daemon unavailable", async () => {
      mockError({ error: "Down" });
      const result = await handleSkillRequest({ action: "health" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Daemon not available");
    });
  });

  describe("unknown action", () => {
    it("returns error for unknown action", async () => {
      const result = await handleSkillRequest({ action: "unknown-action" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Unknown action: unknown-action");
    });
  });

  describe("network failure", () => {
    it("handles fetch rejection", async () => {
      mockFetch.mockRejectedValueOnce(new Error("ECONNREFUSED"));
      const result = await handleSkillRequest({ action: "list" });
      expect(result.success).toBe(false);
      expect(result.error).toBe("Cannot connect to ClawNexus daemon");
    });
  });
});
