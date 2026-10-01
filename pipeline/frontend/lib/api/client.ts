const CONFIGURED_API = process.env.NEXT_PUBLIC_API_BASE_URL;

/** Same-origin "/api" by default: next.config.ts forwards it to the backend,
 * so the page works from any device that can reach this server. A
 * configured URL pointing at localhost is honoured only on the laptop
 * itself — from a phone, "localhost" is the phone. */
function apiBase(): string {
  if (typeof window === "undefined") return CONFIGURED_API ?? "http://127.0.0.1:8001/api";
  if (!CONFIGURED_API) return "/api";
  const pointsAtLocalhost = /\/\/(localhost|127\.0\.0\.1)[:/]/.test(CONFIGURED_API);
  const pageIsLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  return pointsAtLocalhost && !pageIsLocal ? "/api" : CONFIGURED_API;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API ${status} ${statusText}: ${JSON.stringify(body)}`);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  formData?: FormData;
  searchParams?: Record<string, string | number | boolean | undefined>;
}

function buildUrl(path: string, searchParams?: RequestOptions["searchParams"]): string {
  const origin = typeof window === "undefined" ? "http://127.0.0.1:3001" : window.location.origin;
  const url = new URL(`${apiBase()}${path}`, origin);
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/** Thin fetch wrapper shared by every domain client below. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, searchParams } = options;

  const response = await fetch(buildUrl(path, searchParams), {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorBody);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
