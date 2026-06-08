import { apiRequest } from "./client";

export type ExerciseTypeCode = "RUNNING" | "WALKING" | "CYCLING" | "SWIMMING" | "ETC";

export const EXERCISE_TYPE_LABELS: Record<ExerciseTypeCode, string> = {
  RUNNING: "달리기",
  WALKING: "걷기",
  CYCLING: "자전거",
  SWIMMING: "수영",
  ETC: "기타",
};

export const EXERCISE_TYPE_ICONS: Record<ExerciseTypeCode, string> = {
  RUNNING: "🏃",
  WALKING: "🚶",
  CYCLING: "🚴",
  SWIMMING: "🏊",
  ETC: "✏️",
};

export const EXERCISE_TYPES: ExerciseTypeCode[] = [
  "RUNNING",
  "WALKING",
  "CYCLING",
  "SWIMMING",
  "ETC",
];

export type ExerciseLog = {
  id: number;
  exercise_log_id?: number;
  exercise_type: ExerciseTypeCode;
  duration_minutes: number;
  calories_burned?: number | null;
  memo?: string | null;
  exercise_date: string;
  created_at: string;
  updated_at?: string;
};

export type ExerciseSummary = {
  total_duration_minutes: number;
  total_calories_burned: number;
  logged_days: number;
  logged_count: number;
};

export type ExerciseListData = {
  summary: ExerciseSummary;
  total: number;
  items: ExerciseLog[];
};

export type ExerciseQuery = {
  from?: string;
  to?: string;
  period?: "TODAY" | "7D" | "1M" | "3M";
  exercise_type?: ExerciseTypeCode;
  limit?: number;
};

export type CreateExerciseBody = {
  exercise_type: ExerciseTypeCode;
  duration_minutes: number;
  calories_burned?: number;
  memo?: string;
  exercise_date: string;
};

export type UpdateExerciseBody = Partial<CreateExerciseBody>;

type ApiExerciseLog = Omit<ExerciseLog, "id"> & {
  exercise_log_id: number;
};

function toExerciseLog(log: ApiExerciseLog): ExerciseLog {
  return {
    ...log,
    id: log.exercise_log_id,
  };
}

export async function getExerciseLogs(query: ExerciseQuery = {}, token?: string) {
  const params = new URLSearchParams();
  if (query.from) params.set("from", query.from);
  if (query.to) params.set("to", query.to);
  if (query.exercise_type) params.set("exercise_type", query.exercise_type);
  if (query.limit) params.set("limit", String(query.limit));
  const qs = params.toString();
  const response = await apiRequest<{ data: Omit<ExerciseListData, "items"> & { items: ApiExerciseLog[] } }>(`/health/exercise-logs${qs ? `?${qs}` : ""}`, {
    token,
  });
  return {
    data: {
      ...response.data,
      summary: {
        ...response.data.summary,
        logged_days: response.data.summary.logged_count,
      },
      items: response.data.items.map(toExerciseLog),
    },
  };
}

export async function createExerciseLog(body: CreateExerciseBody, token?: string) {
  return apiRequest<{ data: ExerciseLog }>("/health/exercise-logs", {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function updateExerciseLog(id: number, body: UpdateExerciseBody, token?: string) {
  return apiRequest<{ data: ExerciseLog }>(`/health/exercise-logs/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    token,
  });
}

export async function deleteExerciseLog(id: number, token?: string) {
  return apiRequest<void>(`/health/exercise-logs/${id}`, { method: "DELETE", token });
}
