import { useState } from "react";

import type { AppRoute } from "../App";

type PredictionFeedbackPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const feedbackOptions = [
  { label: "정확함", value: "CORRECT" },
  { label: "불확실", value: "UNSURE" },
  { label: "부정확", value: "INCORRECT" },
] as const;

export function PredictionFeedbackPage({ onNavigate }: PredictionFeedbackPageProps) {
  const [selectedFeedback, setSelectedFeedback] = useState<(typeof feedbackOptions)[number]["value"] | null>(null);
  const [actualDiagnosis, setActualDiagnosis] = useState("");
  const [comment, setComment] = useState("");

  const handleSubmit = () => {
    if (!selectedFeedback) {
      return;
    }
    onNavigate("/prediction/result");
  };

  return (
    <div className="page-stack">
      <h1>예측 피드백</h1>
      <section className="dashboard-card feedback-form">
        <h2>예측 결과가 도움이 되셨나요?</h2>
        <p>예측일: 2026-05-10 · 3대 만성질환</p>
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
        <label>
          실제 진단명 (선택)
          <input
            placeholder="실제로 받은 진단이 있다면 입력해주세요"
            value={actualDiagnosis}
            onChange={(event) => setActualDiagnosis(event.target.value)}
          />
        </label>
        <label>
          추가 의견 (선택)
          <textarea maxLength={500} placeholder="500자 이내" value={comment} onChange={(event) => setComment(event.target.value)} />
        </label>
        <div className="feedback-helper-row">
          <span>{comment.length}/500</span>
          {selectedFeedback && <strong>선택됨: {feedbackOptions.find((option) => option.value === selectedFeedback)?.label}</strong>}
        </div>
        <button className="green-button" disabled={!selectedFeedback} type="button" onClick={handleSubmit}>
          피드백 제출
        </button>
      </section>
    </div>
  );
}
