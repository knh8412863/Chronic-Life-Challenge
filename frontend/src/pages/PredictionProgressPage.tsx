import type { AppRoute } from "../App";

type PredictionProgressPageProps = {
  onNavigate: (route: AppRoute) => void;
};

export function PredictionProgressPage({ onNavigate }: PredictionProgressPageProps) {
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
        <div className="progress-ring">73%</div>
        <h2>AI가 건강 데이터를 분석하고 있습니다</h2>
        <p>보통 1~2분 소요됩니다. 잠시만 기다려 주세요...</p>
        <div className="process-list">
          {["데이터 수집 완료", "건강 지표 분석 중", "위험 요인 평가 중", "예측 모델 실행 중"].map((item) => (
            <div key={item}>
              <span>✓</span>
              {item}
            </div>
          ))}
        </div>
        <p>분석이 완료되면 알림으로 안내해드립니다.</p>
        <button className="link-button" type="button" onClick={() => onNavigate("/prediction/result")}>
          결과 화면 보기
        </button>
      </section>
    </div>
  );
}
