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

export type UpdateKidneyBody = Partial<CreateKidneyBody>;

function toApiKidneyBody(body: CreateKidneyBody | UpdateKidneyBody) {
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

type ApiKidneyRecord = Omit<KidneyRecord, "id"> & {
  record_id: number;
};

function toKidneyRecord(record: ApiKidneyRecord): KidneyRecord {
  return {
    ...record,
    id: record.record_id,
    measured_date: record.measured_date ?? record.record_date ?? "",
  };
}

export async function getKidneyRecords(query: { limit?: number } = {}, token?: string) {
  const params = new URLSearchParams();
  if (query.limit) params.set("limit", String(query.limit));
  const qs = params.toString();
  const response = await apiRequest<{ data: ApiKidneyRecord[] }>(`/health/renal-records${qs ? `?${qs}` : ""}`, { token });
  return { data: response.data.map(toKidneyRecord) };
}

export async function updateKidneyRecord(id: number, body: UpdateKidneyBody, token?: string) {
  return apiRequest<{ data: KidneyRecord }>(`/health/renal-records/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toApiKidneyBody(body)),
    token,
  });
}

export async function deleteKidneyRecord(id: number, token?: string) {
  return apiRequest<void>(`/health/renal-records/${id}`, { method: "DELETE", token });
}
