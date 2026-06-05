import { useMemo, useState } from "react";

import type { AppRoute } from "../App";

type PredictionRequestPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const diseases = ["당뇨병", "고혈압", "만성신장질환"];
const dataRows = [
  ["건강 프로필", "완료"],
  ["혈압 기록", "30개 · 최근 128/82"],
  ["혈당 기록", "24개 · 최근 105mg/dL"],
  ["운동 기록", "12개 · 최근 30분"],
  ["생활 습관", "완료"],
  ["가족력", "완료"],
];

export function PredictionRequestPage({ onNavigate }: PredictionRequestPageProps) {
  const [selectedDiseases, setSelectedDiseases] = useState(() => new Set(diseases));
  const [analysisMode, setAnalysisMode] = useState<"BASIC" | "DEEP">("BASIC");

  const isAllSelected = selectedDiseases.size === diseases.length;
  const selectedCount = selectedDiseases.size;
  const selectedDataRows = useMemo(() => {
    if (analysisMode === "BASIC") {
      return dataRows.slice(0, 3);
    }
    return dataRows;
  }, [analysisMode]);

  const toggleDisease = (disease: string) => {
    setSelectedDiseases((prev) => {
      const next = new Set(prev);
      if (next.has(disease)) {
        next.delete(disease);
      } else {
        next.add(disease);
      }
      return next;
    });
  };

  const toggleAllDiseases = () => {
    setSelectedDiseases(isAllSelected ? new Set() : new Set(diseases));
  };

  return (
    <div className="page-stack">
      <section className="prediction-title-row">
        <h1>질환 예측 요청</h1>
        <span className="usage-badge">오늘 예측 가능 횟수: 2/3회 남음</span>
      </section>
      <div className="prediction-stepper">
        {["질환 선택", "데이터 확인", "예측 실행"].map((label, index) => (
          <div className={index === 0 ? "is-current" : ""} key={label}>
            <span>{index === 0 ? "✓" : index + 1}</span>
            <small>{label}</small>
          </div>
        ))}
      </div>
      <section className="prediction-request-grid">
        <article className="dashboard-card">
          <h2>예측할 질환을 선택하세요 (3대 만성질환)</h2>
          <div className="checkbox-list">
            {diseases.map((disease) => (
              <label key={disease}>
                <input checked={selectedDiseases.has(disease)} type="checkbox" onChange={() => toggleDisease(disease)} />
                {disease}
              </label>
            ))}
          </div>
          <div className="request-footer">
            <span>선택된 질환: {selectedCount}개</span>
            <button className="small-button" type="button" onClick={toggleAllDiseases}>
              {isAllSelected ? "전체 해제" : "전체 선택"}
            </button>
          </div>
        </article>
        <aside className="dashboard-card">
          <h2>분석 모드</h2>
          <div className="segment-control">
            <button className={analysisMode === "BASIC" ? "is-active" : ""} type="button" onClick={() => setAnalysisMode("BASIC")}>
              기본
            </button>
            <button className={analysisMode === "DEEP" ? "is-active" : ""} type="button" onClick={() => setAnalysisMode("DEEP")}>
              심화
            </button>
          </div>
          <h2>분석 데이터</h2>
          <div className="data-check-list">
            {selectedDataRows.map(([label, value]) => (
              <div key={label}>
                <span>✓ {label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <button className="green-button" type="button" onClick={() => onNavigate("/prediction/progress")}>
            예측 시작
          </button>
        </aside>
      </section>
      <section className="warning-banner compact">
        <strong>⚠</strong>
        <span>본 결과는 의료 진단이 아닌 생활습관 개선을 위한 참고 지표입니다.</span>
      </section>
    </div>
  );
}
