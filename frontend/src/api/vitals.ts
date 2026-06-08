import { apiRequest } from "./client";

export type MeasureCategory = "BP" | "BG";
export type MeasureType =
  | "BP_MORNING"
  | "BP_LUNCH"
  | "BP_EVENING"
  | "GLUCOSE_FASTING"
  | "GLUCOSE_POSTPRANDIAL";

export const MEASURE_TYPE_LABELS: Record<MeasureType, string> = {
  BP_MORNING: "혈압 (아침)",
  BP_LUNCH: "혈압 (점심)",
  BP_EVENING: "혈압 (저녁)",
  GLUCOSE_FASTING: "공복혈당",
  GLUCOSE_POSTPRANDIAL: "식후혈당",
};

export const MEASURE_TIME_LABELS: Record<string, string> = {
  MORNING: "아침",
  LUNCH: "점심",
  EVENING: "저녁",
};

export function isBpType(t: string): boolean {
  return t.startsWith("BP_");
}

export type VitalRecord = {
  id: number;
  record_id?: number;
  record_date?: string;
  measure_type: MeasureType;
  measured_at: string;
  systolic?: number | null;
  diastolic?: number | null;
  glucose_value?: number | null;
  sbp?: number | null;
  dbp?: number | null;
  glucose?: number | null;
  is_critical: boolean;
  status_label?: "NORMAL" | "CRITICAL";
  memo?: string | null;
  created_at: string;
  updated_at?: string;
};

export type VitalDetail = VitalRecord & {
  avg_systolic_7d?: number | null;
  avg_diastolic_7d?: number | null;
  avg_glucose_7d?: number | null;
  recent_records?: VitalRecord[];
};

export type VitalsListSummary = {
  avg_systolic: number | null;
  avg_diastolic: number | null;
  avg_glucose: number | null;
  avg_sbp?: number | null;
  avg_dbp?: number | null;
  critical_count: number;
};

export type VitalsListData = {
  summary: VitalsListSummary;
  total: number;
  items: VitalRecord[];
};

export type VitalsQuery = {
  period?: "7D" | "30D" | "90D";
  type?: "ALL" | "BP" | "BG";
  from?: string;
  to?: string;
  measure_type?: MeasureType;
  limit?: number;
};

export type CreateVitalBody = {
  measure_type: MeasureType;
  measured_at: string;
  systolic?: number;
  diastolic?: number;
  glucose_value?: number;
  sbp?: number;
  dbp?: number;
  glucose?: number;
  memo?: string;
};

export type UpdateVitalBody = Partial<CreateVitalBody>;

type ApiVitalRecord = Omit<VitalRecord, "id" | "systolic" | "diastolic" | "glucose_value"> & {
  record_id: number;
  sbp: number | null;
  dbp: number | null;
  glucose: number | null;
};

type ApiVitalsListData = {
  summary: {
    avg_sbp: number | null;
    avg_dbp: number | null;
    avg_glucose: number | null;
    critical_count: number;
  };
  total: number;
  items: ApiVitalRecord[];
};

type ApiVitalDetailData = {
  record: ApiVitalRecord;
  trend: {
    avg_sbp: number | null;
    avg_dbp: number | null;
    avg_glucose: number | null;
    recent_7_days: ApiVitalRecord[];
  };
};

function toVitalRecord(record: ApiVitalRecord): VitalRecord {
  return {
    ...record,
    id: record.record_id,
    systolic: record.sbp,
    diastolic: record.dbp,
    glucose_value: record.glucose,
  };
}

function toApiVitalBody(body: CreateVitalBody | UpdateVitalBody) {
  return {
    measured_at: body.measured_at,
    measure_type: body.measure_type,
    sbp: body.sbp ?? body.systolic,
    dbp: body.dbp ?? body.diastolic,
    glucose: body.glucose ?? body.glucose_value,
    memo: body.memo,
  };
}

export async function getVitals(query: VitalsQuery = {}, token?: string) {
  const params = new URLSearchParams();
  if (query.from) params.set("from", query.from);
  if (query.to) params.set("to", query.to);
  if (query.measure_type) params.set("measure_type", query.measure_type);
  if (query.limit) params.set("limit", String(query.limit));
  const qs = params.toString();
  const response = await apiRequest<{ data: ApiVitalsListData }>(`/health/vitals${qs ? `?${qs}` : ""}`, { token });
  return {
    data: {
      ...response.data,
      summary: {
        ...response.data.summary,
        avg_systolic: response.data.summary.avg_sbp,
        avg_diastolic: response.data.summary.avg_dbp,
      },
      items: response.data.items.map(toVitalRecord),
    },
  };
}

export async function getVitalDetail(id: number, token?: string) {
  const response = await apiRequest<{ data: ApiVitalDetailData }>(`/health/vitals/${id}`, { token });
  const record = toVitalRecord(response.data.record);
  return {
    data: {
      ...record,
      avg_systolic_7d: response.data.trend.avg_sbp,
      avg_diastolic_7d: response.data.trend.avg_dbp,
      avg_glucose_7d: response.data.trend.avg_glucose,
      recent_records: response.data.trend.recent_7_days.map(toVitalRecord),
    },
  };
}

export async function createVital(body: CreateVitalBody, token?: string) {
  return apiRequest<{ data: VitalRecord }>("/health/vitals", {
    method: "POST",
    body: JSON.stringify(toApiVitalBody(body)),
    token,
  });
}

export async function updateVital(id: number, body: UpdateVitalBody, token?: string) {
  return apiRequest<{ data: VitalRecord }>(`/health/vitals/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toApiVitalBody(body)),
    token,
  });
}

export async function deleteVital(id: number, token?: string) {
  return apiRequest<void>(`/health/vitals/${id}`, { method: "DELETE", token });
}
