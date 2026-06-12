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

function smokingLabel(value?: number | null) {
  if (value === 0) return "비흡연";
  if (value === 1) return "과거 흡연";
  if (value === 2) return "현재 흡연";
  return "미입력";
}

function alcoholLabel(frequency?: number | null, amount?: number | null) {
  const frequencyLabel =
    frequency === 0 ? "음주 안함" : frequency === 1 ? "월 1회 미만" : frequency === 3 ? "주 1회 이상" : "미입력";
  if (!amount || frequency === 0 || frequency == null) return frequencyLabel;
  return `${frequencyLabel}, 소주 기준 ${amount}잔`;
}

function toHealthProfile(user: UserMeResponse, latestSurvey?: HealthSurveyRecord | null): HealthProfile {
  const height = latestSurvey?.height ?? user.height;
  const weight = latestSurvey?.weight ?? user.weight;
  const bmi = latestSurvey?.bmi ?? user.bmi;
  return {
    name: user.name,
    email: user.email,
    birth_date: user.birthday,
    birthday: user.birthday,
    gender: user.gender,
    managed_diseases: user.managed_diseases,
    height_cm: height,
    weight_kg: weight,
    height,
    weight,
    bmi,
    family_history: buildFamilyHistory(latestSurvey),
    smoking: smokingLabel(latestSurvey?.smoking_status),
    alcohol: alcoholLabel(latestSurvey?.alcohol_frequency, latestSurvey?.alcohol_amount),
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
