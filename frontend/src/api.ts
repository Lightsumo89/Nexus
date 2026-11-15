export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

interface Options {
  method?: string;
  body?: unknown;
  form?: FormData;
}

export async function api<T>(path: string, opts: Options = {}): Promise<T> {
  const hasBody = opts.body !== undefined || opts.form !== undefined;
  const res = await fetch("/api" + path, {
    method: opts.method ?? (hasBody ? "POST" : "GET"),
    credentials: "include",
    headers: opts.body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: opts.form ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail.map((d: { msg: string }) => d.msg).join(", ");
    } catch {
      message = res.statusText;
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export const fmtWhen = (iso: string) =>
  new Date(iso).toLocaleString([], { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

export const WEEKDAYS = ["Sundays", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays"];
