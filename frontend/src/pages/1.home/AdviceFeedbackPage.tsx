import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { createAdviceFeedback, getTodayAdvice, type DailyAdvice } from "../../api/advices";
import { getStoredAccessToken } from "../../api/auth";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type AdviceFeedbackPageProps = {
  onNavigate: (route: AppRoute) => void;
};

type FeedbackType = "HELPFUL" | "NOT_HELPFUL";

const feedbackOptions: Array<{ value: FeedbackType; label: string; helper: string }> = [
  { value: "HELPFUL", label: "도움이 됐어요", helper: "오늘 조언이 생활 실천에 도움이 되었어요." },
  { value: "NOT_HELPFUL", label: "도움이 안 됐어요", helper: "내용이 맞지 않거나 실천하기 어려웠어요." },
];

export function AdviceFeedbackPage({ onNavigate }: AdviceFeedbackPageProps) {
  const [advice, setAdvice] = useState<DailyAdvice | null>(null);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackType | null>(null);
  const [comment, setComment] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }

    getTodayAdvice(token)
      .then((response) => {
        setAdvice(response.data);
        setMessage("");
      })
      .catch(() => setMessage("오늘의 조언을 먼저 생성한 뒤 피드백을 남겨주세요."))
      .finally(() => setIsLoading(false));
  }, [onNavigate]);

  async function handleSubmit() {
    if (!advice || !selectedFeedback) {
      setMessage("피드백 항목을 선택해 주세요.");
      return;
    }

    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }

    setIsSubmitting(true);
    setMessage("");
    try {
      await createAdviceFeedback(
        advice.advice_id,
        {
          feedback_type: selectedFeedback,
          comment: comment.trim() || null,
        },
        token,
      );
      setMessage("조언 피드백이 제출되었습니다.");
      setTimeout(() => onNavigate("/advices/today"), 700);
    } catch {
      setMessage("피드백 제출에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) return <LoadingState message="오늘의 조언을 불러오는 중입니다." />;

  return (
    <div className="page-stack">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">오늘의 조언</p>
          <h1>조언 피드백</h1>
        </div>
        <button type="button" className="small-button" onClick={() => onNavigate("/advices/today")}>
          오늘의 조언으로
        </button>
      </section>

      {message && !advice && <ErrorState title={message} />}

      {advice && (
        <section className="dashboard-card advice-feedback-card">
          <div className="advice-feedback-summary">
            <span className="advice-feedback-ai">AI</span>
            <div>
              <h2>{advice.title}</h2>
              <p>{advice.advice_date} 생성 · {advice.source_type === "LLM" ? "AI 생성" : "기본 규칙"}</p>
            </div>
          </div>
          <div className="advice-text-box">{advice.advice_text}</div>

          <div className="advice-feedback-section">
            <h2>이 조언이 도움이 되었나요?</h2>
            <div className="feedback-choice-grid">
              {feedbackOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={selectedFeedback === option.value ? "is-selected" : ""}
                  onClick={() => setSelectedFeedback(option.value)}
                >
                  <strong>{option.label}</strong>
                  <span>{option.helper}</span>
                </button>
              ))}
            </div>
          </div>

          <label className="advice-feedback-comment">
            추가 의견 (선택)
            <textarea
              maxLength={500}
              placeholder="조언이 좋았던 점이나 아쉬웠던 점을 적어주세요."
              value={comment}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <div className="feedback-helper-row">
            <span>{comment.length}/500</span>
            {selectedFeedback && <strong>{feedbackOptions.find((option) => option.value === selectedFeedback)?.label}</strong>}
          </div>

          {message && (
            <div className="warning-banner compact">
              <strong>!</strong>
              <span>{message}</span>
            </div>
          )}

          <button className="green-button" disabled={!selectedFeedback || isSubmitting} type="button" onClick={handleSubmit}>
            {isSubmitting ? "제출 중..." : "피드백 제출"}
          </button>
        </section>
      )}
    </div>
  );
}
