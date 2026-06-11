import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import {
  createAdviceFeedback,
  getAdviceHistory,
  type AdviceFeedbackPayload,
  type AdviceHistoryItem,
  type AdviceHistorySort,
} from "../../api/advices";
import { getStoredAccessToken } from "../../api/auth";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type AdviceHistoryPageProps = {
  onNavigate: (route: AppRoute) => void;
};

function sourceLabel(sourceType: AdviceHistoryItem["source_type"]) {
  return sourceType === "LLM" ? "AI 생성" : "기본 규칙";
}

export function AdviceHistoryPage({ onNavigate }: AdviceHistoryPageProps) {
  const [sort, setSort] = useState<AdviceHistorySort>("LATEST");
  const [items, setItems] = useState<AdviceHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedAdvice, setSelectedAdvice] = useState<AdviceHistoryItem | null>(null);
  const [selectedFeedback, setSelectedFeedback] = useState<AdviceFeedbackPayload["feedback_type"] | null>(null);
  const [comment, setComment] = useState("");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    getAdviceHistory(sort, token)
      .then((response) => setItems(response.data))
      .catch(() => setErrorMessage("조언 이력을 불러오지 못했습니다."))
      .finally(() => setIsLoading(false));
  }, [onNavigate, sort]);

  async function handleSubmitFeedback() {
    const token = getStoredAccessToken();
    if (!token) {
      onNavigate("/login");
      return;
    }
    if (!selectedAdvice || !selectedFeedback) {
      setErrorMessage("피드백 종류를 선택해 주세요.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    try {
      await createAdviceFeedback(
        selectedAdvice.advice_id,
        {
          feedback_type: selectedFeedback,
          comment: comment.trim() || null,
        },
        token,
      );
      setItems((prev) =>
        prev.map((item) =>
          item.advice_id === selectedAdvice.advice_id ? { ...item, feedback_type: selectedFeedback } : item,
        ),
      );
      setSelectedAdvice(null);
      setSelectedFeedback(null);
      setComment("");
    } catch {
      setErrorMessage("피드백 등록에 실패했습니다. 이미 등록한 조언인지 확인해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) return <LoadingState message="조언 이력을 불러오는 중입니다." />;

  return (
    <div className="page-stack">
      <section className="section-header-row">
        <h1>조언 이력</h1>
        <div className="button-row">
          <button
            className={sort === "LATEST" ? "green-button" : "small-button"}
            type="button"
            onClick={() => setSort("LATEST")}
          >
            최신순
          </button>
          <button
            className={sort === "OLDEST" ? "green-button" : "small-button"}
            type="button"
            onClick={() => setSort("OLDEST")}
          >
            과거순
          </button>
        </div>
      </section>

      {errorMessage && <ErrorState title={errorMessage} />}

      {items.length === 0 && !errorMessage && (
        <section className="dashboard-card empty-state-card">
          <h2>아직 생성된 조언이 없습니다.</h2>
          <p>오늘의 조언 화면에서 조언을 생성하면 이곳에 누적됩니다.</p>
          <button className="green-button" type="button" onClick={() => onNavigate("/advices/today")}>
            오늘의 조언 받기
          </button>
        </section>
      )}

      <section className="advice-history-list">
        {items.map((item) => {
          const hasFeedback = item.feedback_type !== null;
          const isHelpful = item.feedback_type === "HELPFUL";
          return (
            <article className="dashboard-card advice-history-item" key={item.advice_id}>
              <div>
                <span>{item.advice_date}</span>
                <span className="chip">{sourceLabel(item.source_type)}</span>
                {isHelpful && <span className="advice-feedback-positive">👍도움됨</span>}
              </div>
              <p>{item.advice_text}</p>
              {!hasFeedback && (
                <button
                  className="green-button"
                  type="button"
                  onClick={() => {
                    setSelectedAdvice(item);
                    setSelectedFeedback(null);
                    setComment("");
                  }}
                >
                  피드백 남기기
                </button>
              )}
            </article>
          );
        })}
      </section>

      {selectedAdvice && (
        <div className="modal-backdrop">
          <section className="modal-card advice-feedback-card advice-feedback-modal">
            <div className="section-header-row">
              <h2>조언 피드백</h2>
              <button className="small-button" type="button" onClick={() => setSelectedAdvice(null)}>
                닫기
              </button>
            </div>
            <div className="advice-text-box">{selectedAdvice.advice_text}</div>
            <div className="feedback-choice-grid">
              <button
                className={selectedFeedback === "HELPFUL" ? "is-selected" : ""}
                type="button"
                onClick={() => setSelectedFeedback("HELPFUL")}
              >
                도움됨
                <span>오늘 조언이 실천에 도움이 되었어요.</span>
              </button>
              <button
                className={selectedFeedback === "NOT_HELPFUL" ? "is-selected" : ""}
                type="button"
                onClick={() => setSelectedFeedback("NOT_HELPFUL")}
              >
                도움 안됨
                <span>조언 내용이 맞지 않거나 도움이 부족했어요.</span>
              </button>
            </div>
            <label className="advice-feedback-comment">
              의견
              <textarea
                value={comment}
                maxLength={500}
                onChange={(event) => setComment(event.target.value)}
                placeholder="선택 입력"
              />
            </label>
            <button className="green-button" type="button" disabled={isSubmitting} onClick={handleSubmitFeedback}>
              {isSubmitting ? "저장 중..." : "피드백 저장"}
            </button>
          </section>
        </div>
      )}
    </div>
  );
}
