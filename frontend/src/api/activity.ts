import { apiRequest } from "./client";
import { localDateString } from "../utils/date";

export type DailyActivity = {
  id?: number;
  activity_log_id?: number;
  activity_date: string;
  record_date?: string;
  steps?: number | null;
  exercise_minutes?: number | null;
  alcohol_frequency?: number | null;
  alcohol_amount?: number | null;
  walking_days?: number | null;
  sedentary_hours?: number | null;
  sleep_hours?: number | null;
  water_ml?: number | null;
  stress_level?: number | null;
  diet_score?: number | null;
  memo?: string | null;
  exists?: boolean;
};

export type SaveActivityBody = {
  steps?: number;
  exercise_minutes?: number;
  sleep_hours?: number;
  water_ml?: number;
  stress_level?: number;
  diet_score?: number;
  alcohol_frequency?: number;
  alcohol_amount?: number;
  walking_days?: number;
  sedentary_hours?: number;
  memo?: string;
};

function todayStr() {
  return localDateString();
}

type ActivityLogResponse = {
  activity_log_id: number;
  record_date: string;
  steps: number | null;
  exercise_minutes: number | null;
  water_ml: number | null;
  alcohol_frequency: number | null;
  alcohol_amount: number | null;
  walking_days: number | null;
  sedentary_hours: number | null;
  sleep_hours: number | null;
  stress_level: number | null;
  diet_score: number | null;
  memo: string | null;
};

function toDailyActivity(log?: ActivityLogResponse): DailyActivity {
  if (!log) {
    return { activity_date: todayStr(), exists: false };
  }
  return {
    id: log.activity_log_id,
    activity_log_id: log.activity_log_id,
    activity_date: log.record_date,
    record_date: log.record_date,
    steps: log.steps,
    exercise_minutes: log.exercise_minutes,
    water_ml: log.water_ml,
    alcohol_frequency: log.alcohol_frequency,
    alcohol_amount: log.alcohol_amount,
    walking_days: log.walking_days,
    sedentary_hours: log.sedentary_hours,
    sleep_hours: log.sleep_hours,
    stress_level: log.stress_level,
    diet_score: log.diet_score,
    memo: log.memo,
    exists: true,
  };
}

function toApiActivityBody(body: SaveActivityBody) {
  return {
    record_date: todayStr(),
    steps: body.steps,
    exercise_minutes: body.exercise_minutes,
    water_ml: body.water_ml,
    alcohol_frequency: body.alcohol_frequency,
    alcohol_amount: body.alcohol_amount,
    walking_days: body.walking_days,
    sedentary_hours: body.sedentary_hours,
    sleep_hours: body.sleep_hours,
    stress_level: body.stress_level,
    diet_score: body.diet_score,
    memo: body.memo,
  };
}

export async function getTodayActivity(token?: string) {
  const today = todayStr();
  const response = await apiRequest<{ data: { items: ActivityLogResponse[] } }>(
    `/health/activity-logs?from=${today}&to=${today}&limit=1`,
    { token },
  );
  return { data: toDailyActivity(response.data.items[0]) };
}

export async function getActivityLogs(query: { from?: string; to?: string; limit?: number } = {}, token?: string) {
  const params = new URLSearchParams();
  if (query.from) params.set("from", query.from);
  if (query.to) params.set("to", query.to);
  if (query.limit) params.set("limit", String(query.limit));
  const qs = params.toString();
  const response = await apiRequest<{ data: { items: ActivityLogResponse[] } }>(
    `/health/activity-logs${qs ? `?${qs}` : ""}`,
    { token },
  );
  return { data: response.data.items.map(toDailyActivity) };
}

export async function saveActivity(body: SaveActivityBody, token?: string) {
  return apiRequest<{ data: DailyActivity }>("/health/activity-logs", {
    method: "POST",
    body: JSON.stringify(toApiActivityBody(body)),
    token,
  });
}
