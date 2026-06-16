import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { generateTodayAdvice, getTodayAdvice, type DailyAdvice } from "../../api/advices";
import { getStoredAccessToken } from "../../api/auth";
import { ApiError } from "../../api/client";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type AdviceTodayPageProps = {
  onNavigate: (route: AppRoute) => void;
};

type DailyAdviceDraft = Partial<DailyAdvice>;

type AdviceApiResponse = {
  data?: DailyAdviceDraft | null;
};

function hasData(value: unknown): value is AdviceApiResponse {
  return typeof value === "object" && value !== null && "data" in value;
}

function normalizeDailyAdvice(response: AdviceApiResponse | DailyAdviceDraft | null | undefined): DailyAdvice | null {
  const raw = hasData(response) ? response.data : response;
  if (!raw || typeof raw !== "object") return null;

  const remainingCount = Number(raw.remaining_regeneration_count);

  return {
    advice_id: raw.advice_id ?? 0,
    advice_date: raw.advice_date ?? new Date().toISOString().slice(0, 10),
    title: raw.title || "오늘의 AI 건강 조언",
    advice_text: raw.advice_text || "오늘의 조언을 새로 받아보세요.",
    provider: raw.provider ?? "SYSTEM",
    model_name: raw.model_name ?? "",
    trigger_type: raw.trigger_type ?? "AUTO",
    generated: raw.generated ?? false,
    created_at: raw.created_at || new Date().toISOString(),
    source_type: raw.source_type ?? "RULE_BASED",
    remaining_regeneration_count: Number.isFinite(remainingCount) ? remainingCount : 0,
  };
}

function formatCreatedAt(value?: string | null) {
  if (!value) return "생성 시간 확인 중";
  return `${value.slice(0, 16).replace("T", " ")} 생성`;
}

export function AdviceTodayPage({ onNavigate }: AdviceTodayPageProps) {
  const [advice, setAdvice] = useState<DailyAdvice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [isLimitExceeded, setIsLimitExceeded] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }

    getTodayAdvice(token)
      .then((response) => {
        const nextAdvice = normalizeDailyAdvice(response);
        setAdvice(nextAdvice);
        setMessage("");
        setIsLimitExceeded((nextAdvice?.remaining_regeneration_count ?? 0) <= 0);
      })
      .catch(() => setMessage("오늘의 조언을 불러오지 못했습니다. 새로 받아보세요."))
      .finally(() => setIsLoading(false));
  }, [onNavigate]);

  async function handleGenerate() {
    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }

    setIsGenerating(true);
    setMessage("");
    try {
      const response = await generateTodayAdvice(token);
      const nextAdvice = normalizeDailyAdvice(response);
      setAdvice(nextAdvice);
      setIsLimitExceeded((nextAdvice?.remaining_regeneration_count ?? 0) <= 0);
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        setIsLimitExceeded(true);
        return;
      }
      setMessage("조언을 새로 받지 못했습니다. 건강 기록 입력 여부와 서버 연결을 확인해 주세요.");
    } finally {
      setIsGenerating(false);
    }
  }

  if (isLoading) return <LoadingState message="오늘의 조언을 불러오는 중입니다." />;

  const remainingCount = advice?.remaining_regeneration_count ?? 0;
  const generateDisabled = isGenerating || isLimitExceeded || remainingCount <= 0;

  return (
    <div className="page-stack">
      <section className="section-header-row">
        <h1>오늘의 조언</h1>
        <div className="button-row">
          <div
            className="advice-regenerate-tooltip-wrap"
            data-tooltip={`조언은 하루 최대 2회 생성 가능합니다.\n오늘 ${remainingCount}회 생성 가능합니다.`}
          >
            <button className="green-button" type="button" onClick={handleGenerate} disabled={generateDisabled}>
              {isGenerating ? "생성 중..." : "조언 새로 받기"}
            </button>
          </div>
          <button className="small-button" type="button" onClick={() => onNavigate("/advices/history")}>
            조언 이력
          </button>
        </div>
      </section>
      {(isLimitExceeded || remainingCount <= 0) && (
        <p className="advice-limit-message">
          조언은 하루에 2번만 받을 수 있습니다.
          <br />
          내일 다시 시도해주세요.
        </p>
      )}
      <section className="dashboard-card advice-detail-card">
        <div className="advice-title-row">
          <span>AI</span>
          <div>
            <h2>{advice?.title ?? "오늘의 AI 건강 조언"}</h2>
            <p>{advice ? formatCreatedAt(advice.created_at) : "생성된 조언 없음"}</p>
          </div>
        </div>
        <div className="advice-text-box">
          {advice?.advice_text ?? "오늘의 조언을 새로 받아보세요."}
        </div>
        <p>⚠ 본 조언은 참고용이며 의료 진단을 대체하지 않습니다.</p>
      </section>
      {message && <ErrorState title={message} />}
      <section className="dashboard-card feedback-week-card">
        <h2>최근 7일 조언 피드백 현황</h2>
        <div className="feedback-week-grid">
          {["월", "화", "수", "목", "금", "토", "일"].map((day, index) => (
            <div className={index < 3 ? "good" : index < 5 ? "bad" : ""} key={day}>
              <span>{day}</span>
              <strong>{index < 3 ? "👍" : index < 5 ? "👎" : ""}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
