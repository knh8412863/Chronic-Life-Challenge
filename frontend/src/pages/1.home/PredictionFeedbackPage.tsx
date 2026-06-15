import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { createPredictionFeedback, getPredictionResult, type PredictionResult } from "../../api/predictions";

type PredictionFeedbackPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const feedbackOptions = [
  { label: "정확함", value: "CORRECT" },
  { label: "불확실", value: "UNSURE" },
  { label: "부정확", value: "INCORRECT" },
] as const;

function formatPredictionDate(value?: string) {
  if (!value) {
    return "확인 필요";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "확인 필요";
  }
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function PredictionFeedbackPage({ onNavigate }: PredictionFeedbackPageProps) {
  const resultId = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const value = params.get("result_id") ?? sessionStorage.getItem("predictionResultId");
    return value ? Number(value) : null;
  }, []);
  const [selectedFeedback, setSelectedFeedback] = useState<(typeof feedbackOptions)[number]["value"] | null>(null);
  const [actualDiagnosis, setActualDiagnosis] = useState("");
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!resultId || !token) {
      return;
    }

    getPredictionResult(resultId, token)
      .then((response) => setResult(response.data))
      .catch(() => setMessage("예측 결과 정보를 불러오지 못했습니다."));
  }, [resultId]);

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
      const diagnosis = actualDiagnosis.trim();
      await createPredictionFeedback(
        resultId,
        {
          feedback_type: selectedFeedback,
          actual_diagnosis: diagnosis ? { [diagnosis]: true } : null,
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
    <div className="page-stack prediction-feedback-page">
      <h1>예측 피드백</h1>
      <section className="dashboard-card feedback-form prediction-feedback-card">
        <h2>예측 결과가 도움이 되셨나요?</h2>
        <p className="prediction-feedback-meta">
          예측일: {formatPredictionDate(result?.created_at)} · 예측 결과 ID: {resultId ?? "확인 필요"} · 3대 만성질환
        </p>

        <div className="prediction-feedback-divider" />

        <div className="prediction-feedback-section">
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
        </div>

        <label className="prediction-feedback-section">
          <h2>실제 진단 여부 (선택)</h2>
          <input
            maxLength={40}
            placeholder="실제로 받은 진단이 있다면 입력해주세요"
            value={actualDiagnosis}
            onChange={(event) => setActualDiagnosis(event.target.value)}
          />
          <span className="prediction-feedback-note">이 정보는 AI 모델 개선에만 사용됩니다.</span>
        </label>

        <label className="prediction-feedback-section">
          <h2>추가 의견 (선택)</h2>
          <textarea maxLength={500} placeholder="500자 이내" value={comment} onChange={(event) => setComment(event.target.value)} />
        </label>

        <div className="feedback-helper-row">
          <span>{comment.length}/500</span>
        </div>
        {message && (
          <div className="warning-banner compact">
            <strong>!</strong>
            <span>{message}</span>
          </div>
        )}
        <button
          className="green-button prediction-feedback-submit"
          disabled={!selectedFeedback || isSubmitting || !resultId}
          type="button"
          onClick={handleSubmit}
        >
          {isSubmitting ? "제출 중..." : "피드백 제출"}
        </button>
      </section>
    </div>
  );
}
