import { v4 as uuid } from "uuid";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  console.warn(
    "NEXT_PUBLIC_API_BASE_URL is not defined. API calls will fail until it is set."
  );
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  { idempotent }: { idempotent?: boolean } = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (idempotent && !headers.has("Idempotency-Key")) {
    headers.set("Idempotency-Key", uuid());
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const text = await response.text();
  const data = text ? (JSON.parse(text) as T) : (undefined as T);

  if (!response.ok) {
    const detail = (data as Record<string, unknown> | undefined)?.detail ?? response.statusText;
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail)
    );
  }

  return {
    data,
    status: response.status,
  };
}
