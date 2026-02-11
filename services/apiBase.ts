const LOCAL_DEV_API_BASE = 'http://localhost:8000/api/v1';
const CLOUD_RUN_FRONTEND_HOST = 'morpheus-frontend-78704783250.us-central1.run.app';
const CLOUD_RUN_BACKEND_API_BASE = 'https://morpheus-backend-78704783250.us-central1.run.app/api/v1';
const LOCALHOST_API_PATTERN = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i;

const normalizeApiBase = (value: string): string => {
  const trimmed = value.trim();
  return trimmed.replace(/\/+$/, '');
};

const hasValue = (value: unknown): value is string => {
  return typeof value === 'string' && value.trim().length > 0;
};

const getEnvApiBase = (): string | null => {
  if (typeof import.meta === 'undefined') return null;
  if (!hasValue(import.meta.env?.VITE_API_BASE_URL)) return null;
  return normalizeApiBase(String(import.meta.env.VITE_API_BASE_URL));
};

const getRuntimeDefaultApiBase = (): string => {
  const envBase = getEnvApiBase();
  if (envBase) return envBase;

  if (typeof window !== 'undefined') {
    const { host, hostname } = window.location;

    if (host.includes(CLOUD_RUN_FRONTEND_HOST)) {
      return CLOUD_RUN_BACKEND_API_BASE;
    }

    // In non-local browser contexts, prefer same-origin API via reverse proxy.
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return '/api/v1';
    }
  }

  return LOCAL_DEV_API_BASE;
};

export const resolveApiBase = (): string => {
  return getRuntimeDefaultApiBase();
};

export const resolveStoredOrDefaultApiBase = (storedValue: string | null): string => {
  if (!hasValue(storedValue)) {
    return getRuntimeDefaultApiBase();
  }

  const normalizedStored = normalizeApiBase(storedValue);

  if (typeof window !== 'undefined') {
    const isBrowserLocalHost =
      window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    // Avoid stale localhost URL persisting in localStorage on deployed hosts.
    if (!isBrowserLocalHost && LOCALHOST_API_PATTERN.test(normalizedStored)) {
      return getRuntimeDefaultApiBase();
    }
  }

  return normalizedStored;
};
