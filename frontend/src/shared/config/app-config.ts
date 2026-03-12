const DEFAULT_APP_TITLE = "DLE-SaaS";
const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

function normalizeUrl(value: string) {
  return value.replace(/\/+$/, "");
}

function readEnvString(value: unknown, fallback: string) {
  if (typeof value !== "string") {
    return fallback;
  }

  const trimmed = value.trim();
  return trimmed || fallback;
}

const apiBaseUrl = normalizeUrl(readEnvString(import.meta.env.VITE_API_BASE_URL, DEFAULT_API_BASE_URL));

export const appConfig = {
  apiBaseUrl,
  apiDocsUrl: `${apiBaseUrl}/schema/docs/`,
  title: readEnvString(import.meta.env.VITE_APP_TITLE, DEFAULT_APP_TITLE)
};
