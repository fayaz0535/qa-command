/** Wraps a fetch-driven action with a client-side timeout (aborts the request) and a
 * generation counter so a response that arrives after the caller has already moved on
 * (timed out, or a newer call started) is safely ignored instead of clobbering state. */

export function createAbortTimeout(ms: number): { signal: AbortSignal; clear: () => void } {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, clear: () => clearTimeout(timer) };
}

export function isAbortError(e: unknown): boolean {
  return typeof e === "object" && e !== null && (e as { name?: string }).name === "AbortError";
}

export function describeError(e: unknown, timeoutMessage: string): string {
  if (isAbortError(e)) return timeoutMessage;
  if (e instanceof Error) return e.message;
  return "Something went wrong";
}
