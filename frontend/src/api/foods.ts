import { apiRequest } from "./client";

export type MealType = "BREAKFAST" | "LUNCH" | "DINNER" | "SNACK";

export type MealLog = {
  meal_log_id: number;
  food_analysis_result_id: number | null;
  meal_date: string;
  meal_type: MealType;
  food_name: string;
  amount: string | null;
  calories: number | null;
  carbs_g: number | null;
  protein_g: number | null;
  fat_g: number | null;
  sodium_mg: number | null;
  sugar_g: number | null;
  fiber_g: number | null;
  memo: string | null;
  created_at: string;
  updated_at: string;
};

export type MealDailySummary = {
  meal_date: string;
  meal_count: number;
  total_calories: number;
  total_sodium_mg: number;
  total_sugar_g: number;
  total_fiber_g: number;
};

export type MealLogList = {
  daily_summary: MealDailySummary[];
  total: number;
  items: MealLog[];
};

export type MealLogBody = {
  food_analysis_result_id?: number | null;
  meal_date?: string;
  meal_type?: MealType;
  food_name?: string;
  amount?: string | null;
  calories?: number | null;
  carbs_g?: number | null;
  protein_g?: number | null;
  fat_g?: number | null;
  sodium_mg?: number | null;
  sugar_g?: number | null;
  fiber_g?: number | null;
  memo?: string | null;
};

export type FoodAnalysisBody = {
  meal_date?: string;
  meal_type?: MealType;
  food_name: string;
  amount?: string | null;
  calories?: number | null;
  carbs_g?: number | null;
  protein_g?: number | null;
  fat_g?: number | null;
  sodium_mg?: number | null;
  sugar_g?: number | null;
  fiber_g?: number | null;
};

export type FoodNutrition = {
  calories: number | null;
  carbs_g: number | null;
  protein_g: number | null;
  fat_g: number | null;
  sodium_mg: number | null;
  sugar_g: number | null;
  fiber_g: number | null;
};

export type FoodAnalysisResult = {
  food_analysis_result_id: number;
  task_uuid: string;
  status: "SUCCESS" | "FAILED";
  meal_date: string | null;
  meal_type: MealType | null;
  food_name: string;
  amount: string | null;
  nutrition: FoodNutrition;
  health_score: number;
  risk_flags: string[];
  advice_text: string;
  created_at: string;
};

export type MealNutritionSummary = {
  meal_count: number;
  total_calories: number;
  total_sodium_mg: number;
  total_sugar_g: number;
  total_fiber_g: number;
  total_protein_g: number;
};

export type LatestFoodAnalysisAdvice = {
  food_analysis_result_id: number;
  task_uuid: string;
  food_name: string;
  health_score: number;
  risk_flags: string[];
  advice_text: string;
  created_at: string;
};

export type FoodTodayMealSummary = {
  summary_date: string;
  nutrition_summary: MealNutritionSummary;
  latest_analysis_advice: LatestFoodAnalysisAdvice | null;
};

export type FoodDailyMealSummary = {
  meal_date: string;
  nutrition_summary: MealNutritionSummary;
};

export type FoodPeriodMealSummary = {
  period_start: string;
  period_end: string;
  daily_summaries: FoodDailyMealSummary[];
};

export type FoodNutritionOcrData = {
  file_name: string;
  content_type: string;
  extracted_text: string;
  food_name: string | null;
  amount: string | null;
  serving_basis: "TOTAL" | "PER_100G" | "PER_AMOUNT_G" | "PER_SERVING" | "UNKNOWN";
  total_amount_g: number | null;
  basis_amount_g: number | null;
  serving_amount_g: number | null;
  nutrition: FoodNutrition;
  matched_fields: string[];
};

export type MealLogQuery = {
  from?: string;
  to?: string;
  meal_type?: MealType;
  limit?: number;
};

function toQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) search.set(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export async function getMealLogs(query: MealLogQuery = {}, token?: string) {
  return apiRequest<{ data: MealLogList }>(`/health/meals${toQuery(query)}`, { token });
}

export async function createMealLog(body: MealLogBody, token?: string) {
  return apiRequest<{ data: { meal_log_id: number; meal_date: string; created_at: string } }>("/health/meals", {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function updateMealLog(mealLogId: number, body: MealLogBody, token?: string) {
  return apiRequest<{ data: MealLog }>(`/health/meals/${mealLogId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    token,
  });
}

export async function deleteMealLog(mealLogId: number, token?: string) {
  return apiRequest<void>(`/health/meals/${mealLogId}`, {
    method: "DELETE",
    token,
  });
}

export async function createFoodAnalysis(body: FoodAnalysisBody, token?: string) {
  return apiRequest<{ data: FoodAnalysisResult }>("/food/analyze", {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function analyzeFoodNutritionLabel(file: File, token?: string) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<{ data: FoodNutritionOcrData }>("/food/nutrition-ocr", {
    method: "POST",
    body: formData,
    token,
  });
}

export async function getFoodAnalysis(taskUuid: string, token?: string) {
  return apiRequest<{ data: FoodAnalysisResult }>(`/food/analyze/${taskUuid}`, { token });
}

export async function getTodayMealSummary(token?: string) {
  return apiRequest<{ data: FoodTodayMealSummary }>("/food/meals/summary/today", { token });
}

export async function getPeriodMealSummary(from?: string, to?: string, token?: string) {
  return apiRequest<{ data: FoodPeriodMealSummary }>(`/food/meals/summary${toQuery({ from, to })}`, { token });
}
