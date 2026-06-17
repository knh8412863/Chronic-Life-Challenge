import { apiRequest } from "./client";
import {
  createHealthSurveyInput,
  getLatestHealthSurveyInput,
  type HealthSurveyPayload,
  type HealthSurveyRecord,
} from "./predictions";

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
  diagnosed_diseases: string[];
  medications: string[];
  last_checkup_period: string | null;
  smoking: string;
  alcohol: string;
  alcohol_amount: number | null;
  sedentary_hours: number | null;
  exercise_frequency: number | null;
  walking_days: number | null;
  sleep_hours: number | null;
  stress_level: number | null;
  diet_score: number | null;
  profile_image_url?: string | null;
};

export type UpdateHealthProfileBody = {
  name?: string;
  height_cm?: number | null;
  weight_kg?: number | null;
  managed_diseases?: string[];
  diagnosed_diseases?: string[];
  medications?: string[];
  last_checkup_period?: string | null;
  fh_diabetes_father?: boolean;
  fh_diabetes_mother?: boolean;
  fh_diabetes_sibling?: boolean;
  fh_hypertension_father?: boolean;
  fh_hypertension_mother?: boolean;
  fh_hypertension_sibling?: boolean;
  family_history_ckd?: boolean;
  smoking?: string;
  alcohol?: string;
  alcohol_amount?: number | null;
  sedentary_hours?: number | null;
  exercise_frequency?: number | null;
  walking_days?: number | null;
  sleep_hours?: number | null;
  stress_level?: number | null;
  diet_score?: number | null;
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

function smokingCode(value?: string): 0 | 1 | 2 {
  if (value === "현재 흡연" || value === "예") return 2;
  if (value === "과거 흡연") return 1;
  return 0;
}

function alcoholLabel(frequency?: number | null, amount?: number | null) {
  const frequencyLabel =
    frequency === 0 ? "음주 안함" : frequency === 1 ? "월 1회 미만" : frequency === 3 ? "주 1회 이상" : "미입력";
  if (!amount || frequency === 0 || frequency == null) return frequencyLabel;
  return `${frequencyLabel}, 소주 기준 ${amount}잔`;
}

function alcoholFrequencyCode(value?: string): 0 | 1 | 3 {
  if (!value || value === "음주 안함" || value === "안 마심") return 0;
  if (value.includes("주 3회") || value.includes("주 1회 이상")) return 3;
  return 1;
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
    diagnosed_diseases: latestSurvey?.diagnosed_diseases ?? [],
    medications: latestSurvey?.medications ?? [],
    last_checkup_period: latestSurvey?.last_checkup_period ?? null,
    smoking: smokingLabel(latestSurvey?.smoking_status),
    alcohol: alcoholLabel(latestSurvey?.alcohol_frequency, latestSurvey?.alcohol_amount),
    alcohol_amount: latestSurvey?.alcohol_amount ?? null,
    sedentary_hours: latestSurvey?.sedentary_hours ?? null,
    exercise_frequency: latestSurvey?.exercise_frequency ?? null,
    walking_days: latestSurvey?.walking_days ?? null,
    sleep_hours: latestSurvey?.sleep_hours ?? null,
    stress_level: latestSurvey?.stress_level ?? null,
    diet_score: latestSurvey?.diet_score ?? null,
    profile_image_url: user.profile_image_url,
  };
}

function toUserUpdateBody(body: UpdateHealthProfileBody) {
  return {
    name: body.name,
    height: body.height_cm,
    weight: body.weight_kg,
    managed_diseases: body.managed_diseases,
  };
}

function hasSurveyUpdate(body: UpdateHealthProfileBody) {
  return [
    "height_cm",
    "weight_kg",
    "diagnosed_diseases",
    "medications",
    "last_checkup_period",
    "fh_diabetes_father",
    "fh_diabetes_mother",
    "fh_diabetes_sibling",
    "fh_hypertension_father",
    "fh_hypertension_mother",
    "fh_hypertension_sibling",
    "family_history_ckd",
    "smoking",
    "alcohol",
    "alcohol_amount",
    "sedentary_hours",
    "exercise_frequency",
    "walking_days",
    "sleep_hours",
    "stress_level",
    "diet_score",
  ].some((key) => key in body);
}

function buildSurveyPayload(user: UserMeResponse, latest: HealthSurveyRecord | null, body: UpdateHealthProfileBody): HealthSurveyPayload {
  const height = body.height_cm ?? latest?.height ?? user.height;
  const weight = body.weight_kg ?? latest?.weight ?? user.weight;
  if (!height || !weight) {
    throw new Error("height_weight_required");
  }

  const alcoholFrequency = alcoholFrequencyCode(body.alcohol ?? alcoholLabel(latest?.alcohol_frequency, latest?.alcohol_amount));
  const alcoholAmount = alcoholFrequency === 0 ? null : body.alcohol_amount ?? latest?.alcohol_amount ?? 1;

  return {
    input_mode: "DEEP",
    birth_date: user.birthday,
    height,
    weight,
    waist_circumference: latest?.waist_circumference ?? null,
    diagnosed_diseases: body.diagnosed_diseases ?? latest?.diagnosed_diseases ?? [],
    medications: body.medications ?? latest?.medications ?? [],
    last_checkup_period: body.last_checkup_period ?? latest?.last_checkup_period ?? null,
    sbp: latest?.sbp ?? null,
    dbp: latest?.dbp ?? null,
    glucose_fasting: latest?.glucose_fasting ?? null,
    fh_diabetes_father: body.fh_diabetes_father ?? latest?.fh_diabetes_father ?? false,
    fh_diabetes_mother: body.fh_diabetes_mother ?? latest?.fh_diabetes_mother ?? false,
    fh_diabetes_sibling: body.fh_diabetes_sibling ?? latest?.fh_diabetes_sibling ?? false,
    fh_hypertension_father: body.fh_hypertension_father ?? latest?.fh_hypertension_father ?? false,
    fh_hypertension_mother: body.fh_hypertension_mother ?? latest?.fh_hypertension_mother ?? false,
    fh_hypertension_sibling: body.fh_hypertension_sibling ?? latest?.fh_hypertension_sibling ?? false,
    family_history_ckd: body.family_history_ckd ?? latest?.family_history_ckd ?? false,
    smoking_status: smokingCode(body.smoking ?? smokingLabel(latest?.smoking_status)),
    alcohol_frequency: alcoholFrequency,
    alcohol_amount: alcoholAmount,
    walking_days: body.walking_days ?? latest?.walking_days ?? null,
    sedentary_hours: body.sedentary_hours ?? latest?.sedentary_hours ?? null,
    exercise_frequency: body.exercise_frequency ?? latest?.exercise_frequency ?? 0,
    physical_activity_min: latest?.physical_activity_min ?? null,
    sleep_hours: body.sleep_hours ?? latest?.sleep_hours ?? null,
    stress_level: body.stress_level ?? latest?.stress_level ?? null,
    diet_score: body.diet_score ?? latest?.diet_score ?? null,
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
  const user = await apiRequest<MaybeData<UserMeResponse>>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(toUserUpdateBody(body)),
    token,
  }).then(unwrapData);

  let latestSurvey = await getLatestHealthSurveyInput(token)
    .then((response) => response.data)
    .catch(() => null);

  if (hasSurveyUpdate(body)) {
    const payload = buildSurveyPayload(user, latestSurvey, body);
    await createHealthSurveyInput(payload, token);
    latestSurvey = await getLatestHealthSurveyInput(token)
      .then((response) => response.data)
      .catch(() => null);
  }

  return { data: toHealthProfile(user, latestSurvey) };
}
