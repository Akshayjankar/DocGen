import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getApiBase } from "@/lib/api";

describe("getApiBase", () => {
  const originalBackendUrl = process.env.BACKEND_URL;
  const originalPublicApiUrl = process.env.NEXT_PUBLIC_API_URL;

  beforeEach(() => {
    delete process.env.BACKEND_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  afterEach(() => {
    if (originalBackendUrl !== undefined) {
      process.env.BACKEND_URL = originalBackendUrl;
    } else {
      delete process.env.BACKEND_URL;
    }
    if (originalPublicApiUrl !== undefined) {
      process.env.NEXT_PUBLIC_API_URL = originalPublicApiUrl;
    } else {
      delete process.env.NEXT_PUBLIC_API_URL;
    }
  });

  it("returns BACKEND_URL on the server when provided by service binding", () => {
    process.env.BACKEND_URL = "http://backend-internal.vercel.app/";
    expect(getApiBase()).toBe("http://backend-internal.vercel.app");
  });

  it("returns NEXT_PUBLIC_API_URL on the server when BACKEND_URL is not set", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://custom-api.example.com/";
    expect(getApiBase()).toBe("https://custom-api.example.com");
  });

  it("falls back to http://localhost:8000 on the server when no env vars are set", () => {
    expect(getApiBase()).toBe("http://localhost:8000");
  });
});
