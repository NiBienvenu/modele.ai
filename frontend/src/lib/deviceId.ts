// Identifier of this browser. No account: the backend keeps the
// conversations of each device id. Created once, then reused.

import { readStored, writeStored } from "./storage";

const KEY = "device-id";

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  // Fallback for old browsers / non-HTTPS pages
  return "dev-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

let cached: string | null = null;

export function getDeviceId(): string {
  if (cached) return cached;
  cached = readStored(KEY) ?? createId();
  writeStored(KEY, cached);
  return cached;
}
