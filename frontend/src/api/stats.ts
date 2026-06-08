import { apiRequest } from "./client";

export type ScorePoint = {
  date: string;
  total_score: number;
  grade: string;
};

export type ScoreHistory = {
  period: string;
  points: ScorePoint[];
};

type HealthStatisticsResponse = {
  period_start: string;
  period_end: string;
  vital_summary: {
    avg_sbp: number | null;
    avg_dbp: number | null;
    avg_glucose: number | null;
    critical_count: number;
  };
  activity_summary: {
    avg_sleep_hours: number | null;
    avg_stress_level: number | null;
    avg_diet_score: number | null;
  };
  exercise_summary: {
    total_duration_minutes: number;
    total_calories_burned: number;
    logged_count: number;
  };
};

function daysAgoStr(days: number) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export async function getScoreHistory(period = "30D", token?: string) {
  const days = period === "7D" ? 6 : period === "90D" ? 89 : 29;
  const from = daysAgoStr(days);
  const to = new Date().toISOString().slice(0, 10);
  const response = await apiRequest<{ data: HealthStatisticsResponse }>(
    `/health/statistics?from=${from}&to=${to}`,
    { token },
  );
  const score =
    (response.data.vital_summary.critical_count === 0 ? 35 : 20)
    + Math.min(35, Math.round(response.data.exercise_summary.total_duration_minutes / 10))
    + Math.min(30, Math.round((response.data.activity_summary.avg_diet_score ?? 0) * 3));
  return {
    data: {
      period,
      points: [
        {
          date: response.data.period_end,
          total_score: Math.min(100, score),
          grade: score >= 80 ? "GOOD" : score >= 60 ? "CAUTION" : "LOW",
        },
      ],
    },
  };
}
