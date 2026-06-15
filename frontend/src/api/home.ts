import { apiRequest } from "./client";

export type HomeSummary = {
  today_score: {
    score: number | null;
    status: "GOOD" | "CAUTION" | "HIGH" | "NEEDS_INPUT";
    message: string;
    calculation_basis: string[];
  };
  recent_prediction: {
    result_id: number;
    overall_risk_level: string;
    at_risk_diseases: string[];
    created_at: string;
  } | null;
  today_advice: {
    advice_id: number | null;
    title: string;
    content: string;
    is_placeholder: boolean;
  };
  challenge_summary: {
    active_count: number;
    completion_rate: number;
    message: string;
  };
  health_metric_summary: {
    dyslipidemia: MetricAssessment;
    obesity: MetricAssessment;
  };
  vital_summary: {
    blood_pressure_label: string;
    blood_pressure_status: "NORMAL" | "CAUTION" | "HIGH" | "NEEDS_INPUT";
    blood_pressure_value: string | null;
    glucose_label: string;
    glucose_status: "NORMAL" | "CAUTION" | "HIGH" | "NEEDS_INPUT";
    glucose_value: string | null;
    has_today_health_record: boolean;
  };
  quick_record_status: {
    has_health_survey: boolean;
    has_lipid_obesity_record: boolean;
    has_renal_record: boolean;
  };
  unread_notification_count: number;
};

export type MetricAssessment = {
  status: string;
  reasons: string[];
  missing_fields: string[];
};

export async function getHomeSummary(token?: string) {
  return apiRequest<{ data: HomeSummary }>("/home/summary", { token });
}
