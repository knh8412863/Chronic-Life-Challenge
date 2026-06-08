import { apiRequest } from "./client";

export type ChronicDiseaseGoal = {
  target_systolic_bp: number | null;
  target_diastolic_bp: number | null;
  target_fasting_glucose: number | null;
  target_postprandial_glucose: number | null;
  target_hba1c: number | null;
  target_ldl_cholesterol: number | null;
  target_hdl_cholesterol: number | null;
  target_triglycerides: number | null;
  target_bmi: number | null;
  target_weight_kg: number | null;
  target_egfr: number | null;
  updated_at: string;
};

export type LifestyleGoal = {
  target_steps: number | null;
  target_water_ml: number | null;
  target_exercise_minutes: number | null;
  target_sleep_hours: number | null;
  target_diet_score: number | null;
  updated_at: string;
};

export type HealthGoals = {
  chronic_disease_goal: ChronicDiseaseGoal;
  lifestyle_goal: LifestyleGoal;
};

export type UpdateHealthGoalsBody = {
  chronic_disease_goal?: Partial<Omit<ChronicDiseaseGoal, "updated_at">>;
  lifestyle_goal?: Partial<Omit<LifestyleGoal, "updated_at">>;
};

export async function getHealthGoals(token?: string) {
  return apiRequest<{ data: HealthGoals }>("/health/goals", { token });
}

export async function updateHealthGoals(body: UpdateHealthGoalsBody, token?: string) {
  return apiRequest<{ data: HealthGoals }>("/health/goals", {
    method: "PATCH",
    body: JSON.stringify(body),
    token,
  });
}
