import type { AppRoute } from "../App";

type PredictionResultPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const resultCards = [
  ["고혈압", "고위험", 72, "BMI, 수축기혈압, LDL"],
  ["당뇨병", "중위험", 41, "BMI, 수축기혈압, LDL"],
  ["만성신장질환", "저위험", 18, "BMI, 수축기혈압, LDL"],
];

export function PredictionResultPage({ onNavigate }: PredictionResultPageProps) {
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
          <strong>126개</strong>
        </div>
        <div className="risk-outline pink">
          <span>고위험</span>
          <strong>1건</strong>
        </div>
        <div className="risk-outline yellow">
          <span>중위험</span>
          <strong>2건</strong>
        </div>
        <div className="risk-outline muted">
          <span>저위험</span>
          <strong>2건</strong>
        </div>
      </section>
      <section className="dashboard-card ai-summary-card">
        <strong>AI 분석 요약</strong>
        <p>3대 만성질환에 대한 위험도를 분석한 결과, 고혈압 위험도가 가장 높게 나타났습니다.</p>
        <div>
          <span className="chip">BMI 높음</span>
          <span className="chip">수축기혈압 높음</span>
          <span className="chip">LDL 콜레스테롤</span>
        </div>
      </section>
      <section className="result-card-grid">
        {resultCards.map(([name, level, percent, factors]) => (
          <article className="dashboard-card disease-card" key={name}>
            <div>
              <h2>{name}</h2>
              <span className={`risk-badge ${level === "고위험" ? "danger" : level === "중위험" ? "caution" : "safe"}`}>
                {level}
              </span>
            </div>
            <progress max="100" value={Number(percent)} />
            <strong>{percent}%</strong>
            <p>주요 위험 요인</p>
            <span>{factors}</span>
            <p>체중 관리와 규칙적인 운동이 필요합니다. 염분 섭취를 줄이고 혈압을 정기적으로 측정하세요.</p>
          </article>
        ))}
      </section>
      <section className="warning-banner">
        <strong>💡 더 정확한 예측을 위해</strong>
        <span>지질 지표 또는 신장 지표 정보를 추가하면 더 정확한 예측 결과를 확인할 수 있습니다.</span>
        <button type="button" onClick={() => onNavigate("/health")}>
          추가 정보 입력
        </button>
      </section>
      <div className="button-row">
        <button className="small-button" type="button" onClick={() => onNavigate("/prediction/feedback")}>
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
