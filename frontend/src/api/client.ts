const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

type RequestOptions = RequestInit & {
  token?: string;
};

export const AUTH_REQUIRED_EVENT = "all4health:auth-required";
export const AUTH_REQUIRED_MESSAGE = "권한이 없습니다.\n회원가입 또는 로그인 후 다시 진행해주세요.";

export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(status: number, detail?: unknown) {
    const message =
      typeof detail === "string"
        ? detail
        : `API request failed: ${status}`;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function extractErrorDetail(body: unknown): unknown {
  if (!isRecord(body)) return body;

  const error = body.error;
  if (isRecord(error) && typeof error.message === "string") {
    return error.message;
  }

  return body.detail ?? body.message ?? body.error ?? body;
}

function isGenericAuthFailure(detail: unknown): boolean {
  if (typeof detail !== "string") return false;

  const normalized = detail.toLowerCase();
  const pageSpecificMessages = ["비밀번호", "google", "이메일", "password"];
  if (pageSpecificMessages.some((keyword) => normalized.includes(keyword.toLowerCase()))) {
    return false;
  }

  return [
    "authenticate failed",
    "not authenticated",
    "access token",
    "refresh token",
    "token has expired",
    "token is invalid",
    "unauthorized",
  ].some((keyword) => normalized.includes(keyword));
}

function dispatchAuthRequired() {
  window.dispatchEvent(
    new CustomEvent(AUTH_REQUIRED_EVENT, {
      detail: { message: AUTH_REQUIRED_MESSAGE },
    }),
  );
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: options.credentials ?? "include",
    headers,
  });

  if (!response.ok) {
    let detail: unknown;
    try {
      const body = await response.json();
      detail = extractErrorDetail(body);
    } catch {
      detail = response.statusText;
    }

    if (response.status === 401 && isGenericAuthFailure(detail)) {
      dispatchAuthRequired();
      throw new ApiError(response.status, AUTH_REQUIRED_MESSAGE);
    }

    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
