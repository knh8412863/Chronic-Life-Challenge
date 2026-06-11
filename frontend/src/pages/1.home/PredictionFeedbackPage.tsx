import { useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { createPredictionFeedback } from "../../api/predictions";

type PredictionFeedbackPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const feedbackOptions = [
  { label: "정확함", value: "CORRECT" },
  { label: "불확실", value: "UNSURE" },
  { label: "부정확", value: "INCORRECT" },
] as const;

const diagnosisOptions = [
  { label: "당뇨병", value: "diabetes" },
  { label: "고혈압", value: "hypertension" },
  { label: "만성신장질환", value: "kidney" },
] as const;

export function PredictionFeedbackPage({ onNavigate }: PredictionFeedbackPageProps) {
  const resultId = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const value = params.get("result_id") ?? sessionStorage.getItem("predictionResultId");
    return value ? Number(value) : null;
  }, []);
  const [selectedFeedback, setSelectedFeedback] = useState<(typeof feedbackOptions)[number]["value"] | null>(null);
  const [actualDiagnosis, setActualDiagnosis] = useState<Record<string, boolean>>({});
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const toggleDiagnosis = (value: string) => {
    setActualDiagnosis((prev) => ({ ...prev, [value]: !prev[value] }));
  };

  const handleSubmit = async () => {
    if (!selectedFeedback || !resultId) {
      setMessage("예측 결과와 정확도 평가를 확인해 주세요.");
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
      await createPredictionFeedback(
        resultId,
        {
          feedback_type: selectedFeedback,
          actual_diagnosis: Object.keys(actualDiagnosis).length > 0 ? actualDiagnosis : null,
          comment: comment.trim() || null,
        },
        token,
      );
      window.history.pushState({}, "", `/prediction/result?result_id=${resultId}`);
      onNavigate("/prediction/result");
    } catch {
      setMessage("피드백 제출에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      <h1>예측 피드백</h1>
      <section className="dashboard-card feedback-form">
        <h2>예측 결과가 도움이 되셨나요?</h2>
        <p>예측 결과 ID: {resultId ?? "확인 필요"} · 3대 만성질환</p>
        <hr />
        <h2>정확도 평가</h2>
        <div className="feedback-choice-grid">
          {feedbackOptions.map((option) => (
            <button
              className={selectedFeedback === option.value ? "is-selected" : ""}
              key={option.value}
              type="button"
              onClick={() => setSelectedFeedback(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div>
          <h2>실제 진단 여부 (선택)</h2>
          <div className="checkbox-list">
            {diagnosisOptions.map((option) => (
              <label key={option.value}>
                <input checked={Boolean(actualDiagnosis[option.value])} type="checkbox" onChange={() => toggleDiagnosis(option.value)} />
                {option.label}
              </label>
            ))}
          </div>
        </div>
        <label>
          추가 의견 (선택)
          <textarea maxLength={500} placeholder="500자 이내" value={comment} onChange={(event) => setComment(event.target.value)} />
        </label>
        <div className="feedback-helper-row">
          <span>{comment.length}/500</span>
          {selectedFeedback && <strong>선택됨: {feedbackOptions.find((option) => option.value === selectedFeedback)?.label}</strong>}
        </div>
        {message && (
          <div className="warning-banner compact">
            <strong>!</strong>
            <span>{message}</span>
          </div>
        )}
        <button className="green-button" disabled={!selectedFeedback || isSubmitting || !resultId} type="button" onClick={handleSubmit}>
          {isSubmitting ? "제출 중..." : "피드백 제출"}
        </button>
      </section>
    </div>
  );
}
