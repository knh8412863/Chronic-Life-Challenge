import { apiRequest } from "./client";

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

function toHealthProfile(user: UserMeResponse): HealthProfile {
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
    family_history: [],
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
  const response = await apiRequest<UserMeResponse>("/users/me", { token });
  return { data: toHealthProfile(response) };
}

export async function updateHealthProfile(body: UpdateHealthProfileBody, token?: string) {
  const response = await apiRequest<UserMeResponse>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(toUserUpdateBody(body)),
    token,
  });
  return { data: toHealthProfile(response) };
}
