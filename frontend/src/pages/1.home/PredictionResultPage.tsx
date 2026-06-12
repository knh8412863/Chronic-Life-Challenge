import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getPredictionResult, type DiseaseRisk, type PredictionResult } from "../../api/predictions";

type PredictionResultPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const diseaseLabels: Record<string, string> = {
  diabetes: "당뇨병",
  hypertension: "고혈압",
  kidney: "만성신장질환",
};

const riskLevelLabels: Record<string, string> = {
  HIGH: "고위험",
  MEDIUM: "중위험",
  LOW: "저위험",
};

const missingFieldLabels: Record<string, string> = {
  total_cholesterol: "총콜레스테롤",
  hdl_cholesterol: "HDL 콜레스테롤",
  ldl_cholesterol: "LDL 콜레스테롤",
  triglycerides: "중성지방",
  waist_circumference: "허리둘레",
  creatinine: "크레아티닌",
  bun: "BUN",
  urine_protein_pos: "단백뇨",
};

function toPercent(risk: DiseaseRisk) {
  return Math.round(risk.probability * 1000) / 10;
}

function normalizeRiskFactorText(value: string) {
  return value
    .replace(/\s*[,.，]\s*$/g, "")
    .replace(/\s+/g, " ")
    .trim() + ".";
}

export function PredictionResultPage({ onNavigate }: PredictionResultPageProps) {
  const resultId = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const value = params.get("result_id") ?? sessionStorage.getItem("predictionResultId");
    return value ? Number(value) : null;
  }, []);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!resultId) {
      setErrorMessage("예측 결과 정보를 찾을 수 없습니다.");
      return;
    }

    const token = getStoredAccessToken();
    if (!token) {
      setErrorMessage("로그인 후 예측 결과를 확인할 수 있습니다.");
      return;
    }

    setIsLoading(true);
    getPredictionResult(resultId, token)
      .then((response) => {
        setResult(response.data);
        sessionStorage.setItem("predictionResultId", String(response.data.result_id));
      })
      .catch(() => setErrorMessage("예측 결과를 불러오지 못했습니다."))
      .finally(() => setIsLoading(false));
  }, [resultId]);

  const resultCards = result
    ? Object.entries(result.disease_risks).filter(([key]) => key in diseaseLabels)
    : [];
  const highRiskCount = resultCards.filter(([, risk]) => risk.risk_level === "HIGH").length;
  const mediumRiskCount = resultCards.filter(([, risk]) => risk.risk_level === "MEDIUM").length;
  const lowRiskCount = resultCards.filter(([, risk]) => risk.risk_level === "LOW").length;
  const topRisk = resultCards
    .slice()
    .sort(([, first], [, second]) => second.probability - first.probability)[0];
  const missingFields = result?.input_completeness.missing_fields ?? [];

  return (
    <div className="page-stack">
      <h1>예측 결과</h1>
      <div className="prediction-stepper complete">
        {["질환 선택", "데이터 확인", "예측 실행"].map((label) => (
          <div key={label}>
            <span>✓</span>
            <small>{label}</small>
          </div>
        ))}
      </div>
      <section className="risk-summary-row">
        <div className="risk-outline blue">
          <span>분석 데이터</span>
          <strong>{result?.input_completeness.used_default_values ? "일부 기본값" : "입력값 반영"}</strong>
        </div>
        <div className="risk-outline pink">
          <span>고위험</span>
          <strong>{highRiskCount}건</strong>
        </div>
        <div className="risk-outline yellow">
          <span>중위험</span>
          <strong>{mediumRiskCount}건</strong>
        </div>
        <div className="risk-outline muted">
          <span>저위험</span>
          <strong>{lowRiskCount}건</strong>
        </div>
      </section>
      <section className="dashboard-card ai-summary-card">
        <strong>AI 분석 요약</strong>
        {isLoading && <p>예측 결과를 불러오는 중입니다.</p>}
        {errorMessage && <p>{errorMessage}</p>}
        {!isLoading && !errorMessage && topRisk && (
          <p>
            3대 만성질환에 대한 위험도를 분석한 결과, {diseaseLabels[topRisk[0]]} 위험도가 가장 높게 나타났습니다.
          </p>
        )}
        {!isLoading && !errorMessage && result && <p>{result.input_completeness.message}</p>}
        <div>
          {missingFields.length > 0 ? (
            missingFields.slice(0, 4).map((field) => (
              <span className="chip" key={field}>
                {missingFieldLabels[field] ?? field} 미입력
              </span>
            ))
          ) : (
            <span className="chip">검사 수치 반영 완료</span>
          )}
        </div>
      </section>
      <section className="result-card-grid">
        {resultCards.map(([key, risk]) => {
          const level = riskLevelLabels[risk.risk_level] ?? risk.risk_level;
          const percent = toPercent(risk);
          return (
            <article className="dashboard-card disease-card" key={key}>
              <div>
                <h2>{diseaseLabels[key]}</h2>
                <span className={`risk-badge ${level === "고위험" ? "danger" : level === "중위험" ? "caution" : "safe"}`}>
                  {level}
                </span>
              </div>
              <progress max="100" value={Number(percent)} />
              <strong>{percent}%</strong>
              <p>주요 위험 요인</p>
              {risk.risk_factors.length > 0 ? (
                <div className="risk-factor-list">
                  {risk.risk_factors.map((factor) => (
                    <span key={factor}>{normalizeRiskFactorText(factor)}</span>
                  ))}
                </div>
              ) : (
                <span>현재 응답 기준 주요 위험 요인 없음</span>
              )}
              <p>{risk.message}</p>
            </article>
          );
        })}
      </section>
      <section className="warning-banner">
        <strong>💡 더 정확한 예측을 위해</strong>
        <span>{result?.input_completeness.message ?? "건강설문과 검사 수치를 입력하면 예측 결과를 확인할 수 있습니다."}</span>
        <button type="button" onClick={() => onNavigate("/health")}>
          추가 정보 입력
        </button>
      </section>
      <div className="button-row">
        <button
          className="small-button"
          disabled={!result}
          type="button"
          onClick={() => {
            if (!result) return;
            window.history.pushState({}, "", `/prediction/feedback?result_id=${result.result_id}`);
            onNavigate("/prediction/feedback");
          }}
        >
          예측 피드백
        </button>
        <button className="small-button" type="button" onClick={() => onNavigate("/prediction/history")}>
          예측 이력
        </button>
        <button className="green-button align-right" type="button" onClick={() => onNavigate("/prediction/request")}>
          다시 예측
        </button>
      </div>
    </div>
  );
}
