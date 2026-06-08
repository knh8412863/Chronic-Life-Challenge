import { apiRequest } from "./client";

export type KidneyRecord = {
  id: number;
  record_id?: number;
  creatinine: number | null;
  bun?: number | null;
  egfr?: number | null;
  urine_protein_pos: boolean | null;
  record_date?: string;
  measured_date: string;
  memo?: string | null;
  created_at: string;
  updated_at?: string;
};

export type CreateKidneyBody = {
  creatinine?: number;
  bun?: number;
  egfr?: number;
  urine_protein_pos?: boolean;
  record_date?: string;
  measured_date: string;
  memo?: string;
};

function toApiKidneyBody(body: CreateKidneyBody) {
  return {
    record_date: body.record_date ?? body.measured_date,
    creatinine: body.creatinine,
    bun: body.bun,
    egfr: body.egfr,
    urine_protein_pos: body.urine_protein_pos,
    memo: body.memo,
  };
}

export async function createKidneyRecord(body: CreateKidneyBody, token?: string) {
  return apiRequest<{ data: KidneyRecord }>("/health/renal-records", {
    method: "POST",
    body: JSON.stringify(toApiKidneyBody(body)),
    token,
  });
}
