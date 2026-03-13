import { appConfig } from "@/shared/config/app-config";

export interface ApiError {
  detail: string;
  code?: string;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${appConfig.apiBaseUrl}${path}`;
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error: ApiError = await response
      .json()
      .catch((): ApiError => ({ detail: response.statusText })) as ApiError;
    // eslint-disable-next-line @typescript-eslint/only-throw-error
    throw error;
  }
  return response.json() as Promise<T>;
}
