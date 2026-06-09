import { apiRequest } from "./client";

export type Gender = "MALE" | "FEMALE";
export type ConsentType = "TOS" | "PRIVACY" | "HEALTH_DATA" | "MARKETING" | "LOCATION";
export type WithdrawalReason = "NOT_USEFUL" | "PRIVACY_CONCERN" | "HARD_TO_USE" | "FOUND_ALTERNATIVE" | "OTHER";

type MaybeData<T> = T | { data: T };

function unwrapData<T>(response: MaybeData<T>): T {
  if (response && typeof response === "object" && "data" in response) {
    return response.data;
  }
  return response;
}

export type UserInfo = {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  birthday: string;
  gender: Gender;
  profile_image_url: string | null;
  height: number | null;
  weight: number | null;
  bmi: number | null;
  managed_diseases: string[];
  joined_days: number;
  membership_grade: string;
  points: number;
  level: number;
  created_at: string;
};

export type UserUpdatePayload = {
  name?: string;
  phone_number?: string;
  height?: number;
  weight?: number;
  profile_image_url?: string | null;
  managed_diseases?: string[];
};

export type UserConsent = {
  consent_type: ConsentType;
  title: string;
  is_required: boolean;
  is_agreed: boolean;
  agreed_at: string | null;
  withdrawn_at: string | null;
  policy_version: string;
};

export type PolicyChange = {
  policy_type: ConsentType;
  title: string;
  policy_version: string;
  changed_at: string | null;
};

export type ConsentList = {
  items: UserConsent[];
  recent_policy_changes: PolicyChange[];
};

export type PolicyDocument = {
  policy_type: ConsentType;
  title: string;
  policy_version: string;
  changed_at: string | null;
  content: string;
};

export type WithdrawalPayload = {
  password: string;
  withdrawal_reason: WithdrawalReason;
  withdrawal_comment?: string | null;
  confirm_agreed: boolean;
};

export async function getCurrentUser(token?: string) {
  const response = await apiRequest<MaybeData<UserInfo>>("/users/me", { token });
  return unwrapData(response);
}

export async function updateCurrentUser(payload: UserUpdatePayload, token?: string) {
  const response = await apiRequest<MaybeData<UserInfo>>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
  return unwrapData(response);
}

export async function withdrawCurrentUser(payload: WithdrawalPayload, token?: string) {
  return apiRequest<void>("/users/me", {
    method: "DELETE",
    body: JSON.stringify(payload),
    token,
  });
}

export async function getUserConsents(token?: string) {
  const response = await apiRequest<MaybeData<ConsentList>>("/users/me/consents", { token });
  return unwrapData(response);
}

export async function updateUserConsent(consentType: ConsentType, isAgreed: boolean, policyVersion: string, token?: string) {
  const response = await apiRequest<MaybeData<UserConsent>>(`/users/me/consents/${consentType}`, {
    method: "PATCH",
    body: JSON.stringify({ is_agreed: isAgreed, policy_version: policyVersion }),
    token,
  });
  return unwrapData(response);
}

export async function getPolicyDocument(policyType: ConsentType, version?: string, token?: string) {
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  const response = await apiRequest<MaybeData<PolicyDocument>>(`/policy-documents/${policyType}${query}`, { token });
  return unwrapData(response);
}
