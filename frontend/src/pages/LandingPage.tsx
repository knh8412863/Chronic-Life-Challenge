import type { AppRoute } from "../App";

type LandingPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const featureCards = [
  ["AI 건강 예측", "98.5%의 정확도로 만성질환 위험도를 사전에 예측합니다.", "green"],
  ["실시간 모니터링", "혈압, 혈당 등 건강 지표를 추적하고 이상 징후를 알려드립니다.", "yellow"],
  ["생활습관 챌린지", "걷기, 식단, 수면 등 맞춤형 챌린지로 건강 습관을 형성합니다.", "blue"],
  ["전문의 연계", "AI 분석 결과를 바탕으로 상담 필요 시 전문의 연계를 안내합니다.", "pink"],
  ["개인 맞춤 대시보드", "나의 건강 데이터를 한눈에 볼 수 있는 대시보드를 제공합니다.", "violet"],
  ["약물 복용 관리", "처방 약물의 복용 일정을 관리하고 기록을 추적합니다.", "mint"],
];

export function LandingPage({ onNavigate }: LandingPageProps) {
  return (
    <>
      <section className="landing-hero" id="service">
        <div className="landing-copy">
          <div className="tag-row">
            <span className="pill pill-green">만성질환 관리</span>
            <span className="pill pill-yellow">AI 기반 예측</span>
            <span className="pill pill-blue">생활습관 챌린지</span>
          </div>
          <h1>생활습관 개선으로 시작하는 만성질환 관리</h1>
          <p>AI 기반 건강 예측과 챌린지 시스템으로 당뇨, 고혈압, 만성신장질환을 체계적으로 관리하세요.</p>
          <div className="landing-metrics">
            <div>
              <strong>94%</strong>
              <span>챌린지 달성률</span>
            </div>
            <div>
              <strong>98.5%</strong>
              <span>예측 정확도</span>
            </div>
            <div>
              <strong>3대</strong>
              <span>질환 예측</span>
            </div>
          </div>
          <div className="hero-actions">
            <button className="dark-button" type="button" onClick={() => onNavigate("/login")}>
              무료로 시작하기
            </button>
            <button className="outline-button" type="button" onClick={() => onNavigate("/home")}>
              서비스 둘러보기
            </button>
          </div>
        </div>

        <aside className="dashboard-preview" aria-label="나의 건강 대시보드 미리보기">
          <div className="preview-header">
            <strong>나의 건강 대시보드</strong>
            <span>2026. 05. 29</span>
          </div>
          <div className="risk-grid">
            <div className="risk-card risk-low">
              <span>고혈압 위험도</span>
              <strong>낮음</strong>
            </div>
            <div className="risk-card risk-mid">
              <span>당뇨 위험도</span>
              <strong>보통</strong>
            </div>
            <div className="risk-card risk-good">
              <span>신장 건강</span>
              <strong>양호</strong>
            </div>
          </div>
          <p className="preview-label">혈압 변화 추이 최근 7일</p>
          <div className="bar-chart" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <p className="preview-label">오늘의 챌린지</p>
          <div className="progress-lines" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </aside>
      </section>

      <section className="stat-strip" aria-label="서비스 지표">
        <div>
          <strong>98.5%</strong>
          <span>예측 정확도</span>
        </div>
        <div>
          <strong>24만+</strong>
          <span>가입 사용자</span>
        </div>
        <div>
          <strong>3대</strong>
          <span>질환 예측</span>
        </div>
        <div>
          <strong>실시간</strong>
          <span>모니터링</span>
        </div>
      </section>

      <section className="landing-section" id="features">
        <p className="section-label">주요 기능</p>
        <h2>AI가 함께하는 스마트 건강 관리</h2>
        <p>개인 맞춤 건강 예측과 습관 개선을 지원합니다.</p>
        <div className="feature-grid">
          {featureCards.map(([title, description, tone]) => (
            <article className="feature-card" key={title}>
              <span className={`feature-icon tone-${tone}`} />
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
