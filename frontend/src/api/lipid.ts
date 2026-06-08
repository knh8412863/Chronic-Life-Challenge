import { apiRequest } from "./client";

export type LipidRecord = {
  id: number;
  record_id?: number;
  total_cholesterol?: number | null;
  ldl_cholesterol?: number | null;
  hdl_cholesterol?: number | null;
  ldl: number | null;
  hdl: number | null;
  triglycerides?: number | null;
  waist_circumference?: number | null;
  waist_cm?: number | null;
  height?: number | null;
  weight?: number | null;
  bmi?: number | null;
  record_date: string;
  memo?: string | null;
  created_at: string;
  updated_at?: string;
};

export type CreateLipidBody = {
  total_cholesterol?: number;
  ldl_cholesterol?: number;
  hdl_cholesterol?: number;
  ldl?: number;
  hdl?: number;
  triglycerides?: number;
  waist_circumference?: number;
  waist_cm?: number;
  height?: number;
  weight?: number;
  record_date: string;
  memo?: string;
};

function toApiLipidBody(body: CreateLipidBody) {
  return {
    record_date: body.record_date,
    total_cholesterol: body.total_cholesterol,
    ldl_cholesterol: body.ldl_cholesterol ?? body.ldl,
    hdl_cholesterol: body.hdl_cholesterol ?? body.hdl,
    triglycerides: body.triglycerides,
    waist_circumference: body.waist_circumference ?? body.waist_cm,
    height: body.height,
    weight: body.weight,
    memo: body.memo,
  };
}

export async function createLipidRecord(body: CreateLipidBody, token?: string) {
  return apiRequest<{ data: LipidRecord }>("/health/lipid-obesity-records", {
    method: "POST",
    body: JSON.stringify(toApiLipidBody(body)),
    token,
  });
}
