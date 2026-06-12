import { apiRequest } from "./client";

const ACCESS_TOKEN_KEY = "access_token";
const LEGACY_ACCESS_TOKEN_KEY = "accessToken";
const MYPAGE_VERIFIED_AT_KEY = "mypage_verified_at";

export type LoginPayload = {
  email: string;
  password: string;
  remember_me?: boolean;
};

export type LoginResponse = {
  access_token: string;
};

export type GoogleLoginPayload = {
  id_token: string;
  remember_me?: boolean;
};

export type GoogleSignUpPayload = {
  id_token: string;
  name: string;
  gender: "MALE" | "FEMALE";
  birth_date: string;
  phone_number: string;
  managed_diseases?: string[];
  consent_terms_version?: string;
  consent_privacy_agreed?: boolean;
  consent_health_data?: boolean;
  consent_marketing?: boolean;
  remember_me?: boolean;
};

export type SignUpPayload = {
  email: string;
  password: string;
  name: string;
  gender: "MALE" | "FEMALE";
  birth_date: string;
  phone_number: string;
  managed_diseases?: string[];
  consent_terms_version?: string;
  consent_privacy_agreed?: boolean;
  consent_health_data?: boolean;
  consent_marketing?: boolean;
};

export function getStoredAccessToken() {
  return (
    sessionStorage.getItem(ACCESS_TOKEN_KEY) ??
    localStorage.getItem(ACCESS_TOKEN_KEY) ??
    localStorage.getItem(LEGACY_ACCESS_TOKEN_KEY) ??
    undefined
  );
}

export function storeAccessToken(accessToken: string, persist = false) {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);

  const storage = persist ? localStorage : sessionStorage;
  storage.setItem(ACCESS_TOKEN_KEY, accessToken);
}

export function clearStoredAccessToken() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(MYPAGE_VERIFIED_AT_KEY);
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
}

export function login(payload: LoginPayload) {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function googleLogin(payload: GoogleLoginPayload) {
  return apiRequest<LoginResponse>("/auth/google-login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function googleSignup(payload: GoogleSignUpPayload) {
  return apiRequest<LoginResponse>("/auth/google-registrations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function signup(payload: SignUpPayload) {
  return apiRequest<{ detail: string }>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function checkSignupAvailability(payload: Pick<SignUpPayload, "email" | "phone_number">) {
  return apiRequest<void>("/auth/signup-availability", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logout() {
  const token = getStoredAccessToken();
  try {
    await apiRequest<void>("/auth/sessions/current", { method: "DELETE", token });
  } finally {
    clearStoredAccessToken();
  }
}

export function refreshAccessToken() {
  return apiRequest<LoginResponse>("/auth/token/refresh");
}

export function requestPasswordReset(email: string) {
  return apiRequest<void>("/auth/password-reset-requests", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, newPassword: string, newPasswordConfirm: string) {
  return apiRequest<void>("/auth/password-resets", {
    method: "POST",
    body: JSON.stringify({
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    }),
  });
}

export function requestEmailVerification() {
  const token = getStoredAccessToken();
  return apiRequest<void>("/auth/email-verification-requests", {
    method: "POST",
    token,
  });
}

export function verifyEmail(token: string) {
  return apiRequest<{ data: { verified: boolean } }>(
    `/auth/email-verifications?token=${encodeURIComponent(token)}`,
  );
}
