export class ApiRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiRequestError";
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...init, credentials: "include" });
  } catch {
    throw new Error("NEXUS could not reach the local service. Check that the backend is running.");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload.detail;
    const message = typeof detail === "string"
      ? detail
      : detail?.message ?? payload.error?.message ?? "The request could not be completed.";
    throw new ApiRequestError(message, response.status);
  }

  return response;
}