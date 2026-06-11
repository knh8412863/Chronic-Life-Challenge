import { apiRequest } from "./client";

export type DailyAdvice = {
  advice_id: number;
  advice_date: string;
  title: string;
  advice_text: string;
  provider: string;
  model_name: string;
  trigger_type: "AUTO" | "MANUAL";
  generated: boolean;
  created_at: string;
  source_type: "RULE_BASED" | "LLM";
  remaining_regeneration_count: number;
};

export type AdviceHistorySort = "LATEST" | "OLDEST";

export type AdviceHistoryItem = {
  advice_id: number;
  advice_date: string;
  title: string;
  advice_text: string;
  trigger_type: "AUTO" | "MANUAL";
  source_type: "RULE_BASED" | "LLM";
  feedback_type: "HELPFUL" | "NOT_HELPFUL" | null;
  created_at: string;
};

export type AdviceFeedbackPayload = {
  feedback_type: "HELPFUL" | "NOT_HELPFUL";
  comment?: string | null;
};

export type AdviceFeedbackResponse = {
  feedback_id: number;
  advice_id: number;
  feedback_type: "HELPFUL" | "NOT_HELPFUL";
  created_at: string;
};

export function getTodayAdvice(token?: string) {
  return apiRequest<{ data: DailyAdvice }>("/daily-advices/today", { token });
}

export function getAdviceHistory(sort: AdviceHistorySort = "LATEST", token?: string) {
  return apiRequest<{ data: AdviceHistoryItem[] }>(`/daily-advices/history?sort=${sort}`, { token });
}

export function generateTodayAdvice(token?: string) {
  return apiRequest<{ data: DailyAdvice }>("/daily-advices/generate", {
    method: "POST",
    body: JSON.stringify({ trigger_type: "MANUAL" }),
    token,
  });
}

export function createAdviceFeedback(adviceId: number, payload: AdviceFeedbackPayload, token?: string) {
  return apiRequest<{ data: AdviceFeedbackResponse }>(`/daily-advices/${adviceId}/feedbacks`, {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}
