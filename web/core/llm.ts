// Gemini adapter. Every call declares a fallback, so the whole system runs with
// no API key and survives a dead network during a live demo.

const ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models";
const MODEL = process.env.GEMINI_MODEL ?? "gemini-2.5-flash";

export function llmAvailable(): boolean {
  return Boolean(process.env.GEMINI_API_KEY);
}

interface JsonCallOptions<T> {
  system: string;
  prompt: string;
  /** Returned verbatim when no key is configured or the call fails. */
  fallback: T;
  temperature?: number;
}

export interface LlmResult<T> {
  data: T;
  live: boolean;
  note: string;
}

export async function llmJson<T>(opts: JsonCallOptions<T>): Promise<LlmResult<T>> {
  const key = process.env.GEMINI_API_KEY;
  if (!key) {
    return { data: opts.fallback, live: false, note: "offline fallback (no GEMINI_API_KEY)" };
  }

  try {
    const res = await fetch(`${ENDPOINT}/${MODEL}:generateContent?key=${key}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: opts.system }] },
        contents: [{ role: "user", parts: [{ text: opts.prompt }] }],
        generationConfig: {
          temperature: opts.temperature ?? 0.4,
          responseMimeType: "application/json",
        },
      }),
      signal: AbortSignal.timeout(20_000),
    });

    if (!res.ok) {
      return { data: opts.fallback, live: false, note: `fallback (Gemini HTTP ${res.status})` };
    }

    const body = await res.json();
    const text = body?.candidates?.[0]?.content?.parts?.[0]?.text;
    if (typeof text !== "string") {
      return { data: opts.fallback, live: false, note: "fallback (empty Gemini response)" };
    }

    return { data: JSON.parse(text) as T, live: true, note: `gemini:${MODEL}` };
  } catch (err) {
    const reason = err instanceof Error ? err.message : "unknown error";
    return { data: opts.fallback, live: false, note: `fallback (${reason})` };
  }
}
