import { afterEach, describe, expect, it, vi } from "vitest";
import { getDashboardOverview, login } from "./api";

const storage = new Map<string, string>();

afterEach(() => {
  vi.restoreAllMocks();
  storage.clear();
});

describe("ResumeIQ API client", () => {
  it("stores a login token and loads the current user", async () => {
    vi.stubGlobal("localStorage", { getItem: (key: string) => storage.get(key) ?? null, setItem: (key: string, value: string) => storage.set(key, value), removeItem: (key: string) => storage.delete(key) });
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "test-token" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "user-1", email: "jordan@example.com", full_name: "Jordan Doe", created_at: "2026-01-01T00:00:00Z" }), { status: 200 })));

    const user = await login("jordan@example.com", "correct-horse-battery");

    expect(user.email).toBe("jordan@example.com");
    expect(storage.get("resumeiq.access_token")).toBe("test-token");
  });

  it("surfaces dashboard API failures without inventing metrics", async () => {
    vi.stubGlobal("localStorage", { getItem: () => "test-token", setItem: () => undefined, removeItem: () => undefined });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Dashboard unavailable" }), { status: 503 })));

    await expect(getDashboardOverview()).rejects.toThrow("Dashboard unavailable");
  });
});