import { apiRequest } from "./client";

export type HealthSurveyPayload = {
  input_mode: "BASIC" | "DEEP";
  birth_date: string;
  height: number;
  weight: number;
  waist_circumference?: number | null;
  diagnosed_diseases: string[];
  medications: string[];
  last_checkup_period?: string | null;
  sbp?: number | null;
  dbp?: number | null;
  glucose_fasting?: number | null;
  fh_diabetes_father: boolean;
  fh_diabetes_mother: boolean;
  fh_diabetes_sibling: boolean;
  fh_hypertension_father: boolean;
  fh_hypertension_mother: boolean;
  fh_hypertension_sibling: boolean;
  family_history_ckd: boolean;
  smoking_status: 0 | 1 | 2;
  alcohol_frequency: 0 | 1 | 3;
  alcohol_amount?: number | null;
  walking_days?: number | null;
  sedentary_hours?: number | null;
  exercise_frequency: number;
  physical_activity_min?: number | null;
  sleep_hours?: number | null;
  stress_level?: number | null;
  diet_score?: number | null;
};

export type HealthSurveyResponse = {
  health_input_id: number;
  bmi: number;
  input_mode: "BASIC" | "DEEP";
  profile_age_snapshot: number;
  profile_gender_snapshot: string;
  created_at: string;
};

export type HealthSurveyRecord = HealthSurveyResponse & {
  age: number;
  gender: string;
  height: number;
  weight: number;
  waist_circumference?: number | null;
  sbp?: number | null;
  dbp?: number | null;
  glucose_fasting?: number | null;
  diagnosed_diseases: string[];
  medications: string[];
  last_checkup_period?: string | null;
  fh_diabetes_father?: boolean;
  fh_diabetes_mother?: boolean;
  fh_diabetes_sibling?: boolean;
  fh_hypertension_father?: boolean;
  fh_hypertension_mother?: boolean;
  fh_hypertension_sibling?: boolean;
  family_history_ckd?: boolean;
  smoking_status?: 0 | 1 | 2;
  alcohol_frequency?: 0 | 1 | 3;
  alcohol_amount?: number | null;
  walking_days?: number | null;
  sedentary_hours?: number | null;
  exercise_frequency?: number;
  physical_activity_min?: number | null;
  sleep_hours?: number | null;
  stress_level?: number | null;
  diet_score?: number | null;
};

export type PredictionTaskCreatePayload = {
  health_input_id?: number;
  prediction_mode: "SCREENING";
};

export type PredictionTask = {
  task_uuid: string;
  status: string;
  prediction_mode: string;
};

export type PredictionTaskStatus = PredictionTask & {
  progress_percent: number;
  current_step: string;
  result_id: number | null;
  error_message: string | null;
};

export type DiseaseRisk = {
  probability: number;
  risk_score: number;
  threshold: number;
  is_at_risk: boolean;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | string;
  message: string;
  risk_factors: string[];
};

export type PredictionResult = {
  result_id: number;
  prediction_mode: string;
  created_at: string;
  disease_risks: Record<string, DiseaseRisk>;
  input_completeness: {
    used_default_values: boolean;
    missing_fields: string[];
    message: string;
  };
  disclaimer: string;
};

export type PredictionResultListItem = {
  result_id: number;
  prediction_mode: string;
  created_at: string;
  overall_risk_level: "LOW" | "MEDIUM" | "HIGH" | string;
  highest_risk_disease: string | null;
  highest_risk_probability: number | null;
  highest_risk_score: number | null;
  disease_risks: Record<string, DiseaseRisk>;
  input_completeness: PredictionResult["input_completeness"];
  feedback_submitted: boolean;
};

export type PredictionResultList = {
  total: number;
  items: PredictionResultListItem[];
};

export type PredictionFeedbackPayload = {
  feedback_type: "CORRECT" | "INCORRECT" | "UNSURE";
  actual_diagnosis?: Record<string, boolean> | null;
  comment?: string | null;
};

export type PredictionFeedbackResponse = {
  feedback_id: number;
  prediction_result_id: number;
  feedback_type: "CORRECT" | "INCORRECT" | "UNSURE";
  created_at: string;
};

export function createHealthSurveyInput(payload: HealthSurveyPayload, token?: string) {
  return apiRequest<{ data: HealthSurveyResponse }>("/prediction-inputs", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function getLatestHealthSurveyInput(token?: string) {
  return apiRequest<{ data: HealthSurveyRecord }>("/prediction-inputs/latest", {
    token,
  });
}

export function createPredictionTask(payload: PredictionTaskCreatePayload, token?: string) {
  return apiRequest<{ data: PredictionTask }>("/prediction-tasks", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function getPredictionTaskStatus(taskUuid: string, token?: string) {
  return apiRequest<{ data: PredictionTaskStatus }>(`/prediction-tasks/${taskUuid}/status`, {
    token,
  });
}

export function getPredictionResult(resultId: number, token?: string) {
  return apiRequest<{ data: PredictionResult }>(`/prediction-results/${resultId}`, {
    token,
  });
}

export function getPredictionResults(limit = 20, token?: string) {
  return apiRequest<{ data: PredictionResultList }>(`/prediction-results?limit=${limit}`, {
    token,
  });
}

export function createPredictionFeedback(resultId: number, payload: PredictionFeedbackPayload, token?: string) {
  return apiRequest<{ data: PredictionFeedbackResponse }>(`/prediction-results/${resultId}/feedbacks`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}
