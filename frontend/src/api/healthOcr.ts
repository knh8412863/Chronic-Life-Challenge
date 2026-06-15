import { apiRequest } from "./client";

export type HealthCheckupOcrData = {
  file_name: string;
  content_type: string;
  extracted_text: string;
  vitals: {
    sbp: number | null;
    dbp: number | null;
    glucose_fasting: number | null;
    glucose_postprandial: number | null;
  };
  lipid: {
    total_cholesterol: number | null;
    ldl_cholesterol: number | null;
    hdl_cholesterol: number | null;
    triglycerides: number | null;
    waist_circumference: number | null;
    height: number | null;
    weight: number | null;
  };
  renal: {
    creatinine: number | null;
    egfr: number | null;
    bun: number | null;
    urine_protein_pos: boolean | null;
  };
  activity: {
    steps: number | null;
    exercise_minutes: number | null;
    water_ml: number | null;
    sleep_hours: number | null;
  };
  matched_fields: string[];
};

export async function analyzeHealthCheckupFile(file: File, token?: string) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<{ data: HealthCheckupOcrData }>("/health/checkup-ocr", {
    method: "POST",
    body: formData,
    token,
  });
}
