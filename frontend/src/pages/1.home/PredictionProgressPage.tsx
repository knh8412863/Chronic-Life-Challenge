import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getPredictionTaskStatus, type PredictionTaskStatus } from "../../api/predictions";

type PredictionProgressPageProps = {
  onNavigate: (route: AppRoute) => void;
};

export function PredictionProgressPage({ onNavigate }: PredictionProgressPageProps) {
  const taskUuid = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("task_uuid") ?? sessionStorage.getItem("predictionTaskUuid") ?? "";
  }, []);
  const [taskStatus, setTaskStatus] = useState<PredictionTaskStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!taskUuid) {
      setErrorMessage("예측 요청 정보를 찾을 수 없습니다. 예측을 다시 요청해 주세요.");
      return;
    }

    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 예측 진행 상태를 확인할 수 있습니다.");
      return;
    }

    let isActive = true;
    let timeoutId: number | undefined;

    const pollStatus = async () => {
      try {
        const response = await getPredictionTaskStatus(taskUuid, token);
        if (!isActive) return;
        setTaskStatus(response.data);

        if (response.data.status === "SUCCESS" && response.data.result_id) {
          sessionStorage.setItem("predictionResultId", String(response.data.result_id));
          window.history.pushState({}, "", `/prediction/result?result_id=${response.data.result_id}`);
          onNavigate("/prediction/result");
          return;
        }

        if (response.data.status === "FAILED") {
          setErrorMessage(response.data.error_message ?? "예측 처리 중 오류가 발생했습니다.");
          return;
        }

        timeoutId = window.setTimeout(pollStatus, 1500);
      } catch {
        if (isActive) {
          setErrorMessage("예측 진행 상태를 불러오지 못했습니다.");
        }
      }
    };

    pollStatus();

    return () => {
      isActive = false;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [onNavigate, taskUuid]);

  const progress = taskStatus?.progress_percent ?? 0;
  const currentStep = taskStatus?.current_step ?? "예측 요청 확인 중";

  return (
    <div className="page-stack">
      <h1>질환 예측 진행중</h1>
      <div className="prediction-stepper is-running">
        {["질환 선택", "데이터 확인", "예측 실행"].map((label, index) => (
          <div key={label}>
            <span>{index < 2 ? "✓" : "3"}</span>
            <small>{label}</small>
          </div>
        ))}
      </div>
      <section className="dashboard-card prediction-running-card">
        <div className="progress-ring">{progress}%</div>
        <h2>AI가 건강 데이터를 분석하고 있습니다</h2>
        <p>{currentStep}</p>
        <div className="process-list">
          {["예측 요청 접수", "AI 모델 실행 중", "예측 완료"].map((item) => (
            <div key={item}>
              <span>{progress >= (item === "예측 요청 접수" ? 0 : item === "AI 모델 실행 중" ? 60 : 100) ? "✓" : "·"}</span>
              {item}
            </div>
          ))}
        </div>
        {errorMessage ? (
          <div className="warning-banner compact">
            <strong>!</strong>
            <span>{errorMessage}</span>
            <button type="button" onClick={() => onNavigate("/prediction/request")}>
              다시 요청
            </button>
          </div>
        ) : (
          <p>분석이 완료되면 예측 결과 화면으로 자동 이동합니다.</p>
        )}
      </section>
    </div>
  );
}
