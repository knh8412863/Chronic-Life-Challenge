import { apiRequest } from "./client";

export type ReportStatus = "AVAILABLE" | "EMPTY" | "FAILED";
export type CurrentReportStatus = "AVAILABLE" | "EMPTY" | "GENERATABLE";
export type ReportItemStatus = "NORMAL" | "CAUTION" | "HIGH" | "UNAVAILABLE";
export type ReportTrendStatus = "IMPROVED" | "UNCHANGED" | "WORSENED" | "UNAVAILABLE";
export type ReportChallengeStatus = "ACHIEVED" | "IN_PROGRESS" | "UNAVAILABLE";

export type WeeklyReportSourceSummary = {
  health_survey_count: number;
  lipid_obesity_record_count: number;
  renal_record_count: number;
  vital_record_count: number;
  activity_log_count: number;
  exercise_log_count: number;
  meal_log_count: number;
  prediction_count: number;
  at_risk_prediction_count: number;
  challenge_checkin_count: number;
};

export type WeeklyReportSummaryCard = {
  label: string;
  value: string;
  status: ReportItemStatus;
  description: string;
};

export type WeeklyReportMetricSummary = {
  metric: string;
  label: string;
  value: string;
  unit: string | null;
  status: ReportItemStatus;
  description: string;
};

export type WeeklyReportTrendSummary = {
  status: ReportTrendStatus;
  message: string;
  previous_week_report_id: number | null;
};

export type WeeklyReportChallengeSummary = {
  checkin_count: number;
  completion_rate: number;
  status: ReportChallengeStatus;
  message: string;
};

export type WeeklyReport = {
  report_id: number;
  week_start_date: string;
  week_end_date: string;
  status: ReportStatus;
  source_summary: WeeklyReportSourceSummary;
  summary_cards: WeeklyReportSummaryCard[];
  metric_summaries: WeeklyReportMetricSummary[];
  trend_summary: WeeklyReportTrendSummary;
  challenge_summary: WeeklyReportChallengeSummary;
  report_text: string;
  provider: string;
  model_name: string;
  generated: boolean;
  created_at: string;
  source_type: "RULE_BASED" | "LLM";
};

export type CurrentWeeklyReport = {
  status: CurrentReportStatus;
  week_start_date: string;
  week_end_date: string;
  report: WeeklyReport | null;
  empty_message: string | null;
};

export type WeeklyReportListItem = {
  report_id: number;
  week_start_date: string;
  week_end_date: string;
  summary_text: string;
  overall_status: ReportItemStatus;
  created_at: string;
};

export type WeeklyReportExportFormat = "JSON" | "CSV" | "PDF";

export type WeeklyReportExport = {
  report_id: number;
  file_name: string;
  content_type: string;
  content: string;
  content_encoding: "TEXT" | "BASE64";
  emailed: boolean;
};

export async function getCurrentWeeklyReport(token?: string) {
  return apiRequest<{ data: CurrentWeeklyReport }>("/weekly-reports/current", { token });
}

export async function generateWeeklyReport(forceRegenerate = false, token?: string) {
  return apiRequest<{ data: WeeklyReport }>("/weekly-reports/generate", {
    method: "POST",
    body: JSON.stringify({ force_regenerate: forceRegenerate }),
    token,
  });
}

export async function getWeeklyReports(limit = 20, token?: string) {
  return apiRequest<{ data: WeeklyReportListItem[] }>(`/weekly-reports?limit=${limit}`, { token });
}

export async function getWeeklyReport(reportId: number, token?: string) {
  return apiRequest<{ data: WeeklyReport }>(`/weekly-reports/${reportId}`, { token });
}

export async function exportWeeklyReport(
  reportId: number,
  exportFormat: WeeklyReportExportFormat,
  token?: string,
  sendEmail = false,
) {
  return apiRequest<{ data: WeeklyReportExport }>(
    `/weekly-reports/${reportId}/exports?export_format=${exportFormat}&send_email=${sendEmail}`,
    { token },
  );
}
