import { apiRequest } from "./client";
import { getLatestHealthSurveyInput, type HealthSurveyRecord } from "./predictions";

export type FamilyHistoryItem = {
  condition: string;
  relation: string;
};

export type HealthProfile = {
  name: string;
  email: string;
  birth_date: string;
  birthday?: string;
  gender: string;
  managed_diseases: string[];
  height_cm: number | null;
  weight_kg: number | null;
  height?: number | null;
  weight?: number | null;
  bmi: number | null;
  family_history: FamilyHistoryItem[];
  smoking: string;
  alcohol: string;
  profile_image_url?: string | null;
};

export type UpdateHealthProfileBody = {
  name?: string;
  height_cm?: number | null;
  weight_kg?: number | null;
  smoking?: string;
  alcohol?: string;
};

type UserMeResponse = {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  birthday: string;
  gender: string;
  profile_image_url: string | null;
  height: number | null;
  weight: number | null;
  bmi: number | null;
  managed_diseases: string[];
};

type MaybeData<T> = T | { data: T };

function unwrapData<T>(response: MaybeData<T>): T {
  if (response && typeof response === "object" && "data" in response) {
    return response.data;
  }
  return response;
}

function buildFamilyHistory(input?: HealthSurveyRecord | null): FamilyHistoryItem[] {
  if (!input) return [];

  const items: FamilyHistoryItem[] = [];
  if (input.fh_diabetes_father) items.push({ condition: "DIABETES", relation: "FATHER" });
  if (input.fh_diabetes_mother) items.push({ condition: "DIABETES", relation: "MOTHER" });
  if (input.fh_diabetes_sibling) items.push({ condition: "DIABETES", relation: "SIBLING" });
  if (input.fh_hypertension_father) items.push({ condition: "HYPERTENSION", relation: "FATHER" });
  if (input.fh_hypertension_mother) items.push({ condition: "HYPERTENSION", relation: "MOTHER" });
  if (input.fh_hypertension_sibling) items.push({ condition: "HYPERTENSION", relation: "SIBLING" });
  if (input.family_history_ckd) items.push({ condition: "CKD", relation: "" });
  return items;
}

function toHealthProfile(user: UserMeResponse, latestSurvey?: HealthSurveyRecord | null): HealthProfile {
  return {
    name: user.name,
    email: user.email,
    birth_date: user.birthday,
    birthday: user.birthday,
    gender: user.gender,
    managed_diseases: user.managed_diseases,
    height_cm: user.height,
    weight_kg: user.weight,
    height: user.height,
    weight: user.weight,
    bmi: user.bmi,
    family_history: buildFamilyHistory(latestSurvey),
    smoking: "미입력",
    alcohol: "미입력",
    profile_image_url: user.profile_image_url,
  };
}

function toUserUpdateBody(body: UpdateHealthProfileBody) {
  return {
    name: body.name,
    height: body.height_cm,
    weight: body.weight_kg,
  };
}

export async function getHealthProfile(token?: string) {
  const [user, latestSurvey] = await Promise.all([
    apiRequest<MaybeData<UserMeResponse>>("/users/me", { token }).then(unwrapData),
    getLatestHealthSurveyInput(token)
      .then((response) => response.data)
      .catch(() => null),
  ]);
  return { data: toHealthProfile(user, latestSurvey) };
}

export async function updateHealthProfile(body: UpdateHealthProfileBody, token?: string) {
  const response = await apiRequest<MaybeData<UserMeResponse>>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(toUserUpdateBody(body)),
    token,
  }).then(unwrapData);
  return { data: toHealthProfile(response) };
}
