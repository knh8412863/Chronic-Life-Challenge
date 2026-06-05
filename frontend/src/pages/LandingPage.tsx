import type { AppRoute } from "../App";

type LandingPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const featureCards = [
  ["AI 건강 예측", "당뇨·고혈압·만성신장질환 위험 신호를 사전에 확인합니다.", "green"],
  ["실시간 모니터링", "혈압, 혈당 등 건강 지표를 추적하고 이상 징후를 알려드립니다.", "yellow"],
  ["생활습관 챌린지", "걷기, 식단, 수면 등 맞춤형 챌린지로 건강 습관을 형성합니다.", "blue"],
  ["전문의 연계", "위험 신호가 감지되면 전문의 상담을 권장합니다.", "pink"],
  ["개인 맞춤 대시보드", "나의 건강 데이터를 한눈에 볼 수 있는 대시보드를 제공합니다.", "violet"],
  ["복약·건강관리", "복약 여부와 건강검진 정보를 조언 컨텍스트로 활용합니다.", "mint"],
];

const diseaseCards = [
  ["고혈압", "혈압 변화 패턴을 분석하여 고혈압 위험 신호를 조기에 감지합니다.", "위험도 예측", "green"],
  ["당뇨병", "혈당 추이와 생활습관 데이터를 결합하여 당뇨 위험 가능성을 분석합니다.", "혈당 모니터링", "yellow"],
  ["만성 신장질환", "신장 기능 지표를 지속적으로 추적하여 신장 건강을 평가합니다.", "기능 추적", "blue"],
  ["고지혈증", "콜레스테롤 수치 기반으로 지질 관리 상태를 확인합니다.", "지질 상태 체크", "pink"],
  ["비만·체중 관리", "체중, BMI, 허리둘레 변화를 분석하여 맞춤 체중 관리 계획을 제공합니다.", "체중 분석", "orange"],
];

const challengeItems = [
  ["매일 걷기 6,000보", "꾸준한 걷기 운동으로 심폐 기능을 향상시키세요.", "green"],
  ["저염 식단 챌린지", "나트륨 섭취를 줄여 혈압을 자연스럽게 조절합니다.", "yellow"],
  ["7시간 수면 확보", "규칙적인 수면 습관으로 신체 회복력을 높이세요.", "blue"],
  ["혈압 매일 측정", "일관된 혈압 측정으로 건강 변화를 놓치지 마세요.", "pink"],
];

const testimonials = [
  ["김지수", "고혈압 관리 6개월차 · 52세", "3개월 동안 꾸준히 챌린지를 하니 혈압이 정상 범위로 돌아왔어요. AI 예측 덕분에 미리 대비할 수 있었습니다.", "김"],
  ["박민준", "당뇨 관리 4개월차 · 47세", "당뇨 전단계라는 진단을 받고 시작했는데, 식단 챌린지와 AI 모니터링 덕분에 혈당이 많이 안정됐어요.", "박"],
  ["이수연", "생활습관 개선 2개월차 · 38세", "바쁜 직장 생활에도 매일 알림으로 건강 관리를 놓치지 않게 해줘요. 대시보드가 직관적이라 편리합니다.", "이"],
];

function scrollToSection(sectionId: string) {
  document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth" });
}

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
              <span>모델 검증 지표</span>
            </div>
            <div>
              <strong>5대</strong>
              <span>만성질환 관리</span>
            </div>
          </div>
          <div className="hero-actions">
            <button className="dark-button" type="button" onClick={() => onNavigate("/login")}>
              무료로 시작하기
            </button>
            <button className="outline-button" type="button" onClick={() => scrollToSection("features")}>
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
          <span>모델 검증 지표</span>
        </div>
        <div>
          <strong>24만+</strong>
          <span>가입 사용자</span>
        </div>
        <div>
          <strong>5대</strong>
          <span>질환 관리</span>
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

      <section className="landing-section process-section" aria-label="이용 방법">
        <p className="section-label">이용 방법</p>
        <h2>4단계로 시작하는 건강 관리</h2>
        <p>복잡한 절차 없이 간단하게 시작할 수 있습니다.</p>
        <div className="process-line">
          {[
            ["회원가입", "기본 건강 정보를 입력하고 무료 계정을 만드세요."],
            ["건강 데이터 입력", "혈압, 혈당 등 건강 수치를 등록하면 AI가 분석합니다."],
            ["AI 예측 확인", "맞춤형 질환 위험도와 건강 리포트를 확인하세요."],
            ["챌린지 시작", "추천 챌린지를 수행하며 건강한 습관을 만들어가세요."],
          ].map(([title, description], index) => (
            <article className="process-step" key={title}>
              <span>{index + 1}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section" id="diseases">
        <p className="section-label">질환 관리</p>
        <h2>5대 만성질환을 체계적으로 관리합니다</h2>
        <p>AI 예측 질환과 수치 기반 관리 질환을 구분하여 건강 상태를 확인합니다.</p>
        <div className="disease-grid">
          {diseaseCards.map(([title, description, badge, tone]) => (
            <article className={`disease-card disease-${tone}`} key={title}>
              <h3>{title}</h3>
              <p>{description}</p>
              <span>{badge}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section challenge-section" id="challenge">
        <p className="section-label">챌린지 시스템</p>
        <h2>건강 챌린지로 습관을 바꾸세요</h2>
        <p>작은 목표부터 시작해 건강한 생활 습관을 단계적으로 형성합니다.</p>
        <div className="challenge-showcase">
          <div className="challenge-list">
            {challengeItems.map(([title, description, tone]) => (
              <article className="challenge-card" key={title}>
                <span className={`challenge-swatch tone-${tone}`} />
                <div>
                  <h3>{title}</h3>
                  <p>{description}</p>
                </div>
              </article>
            ))}
          </div>
          <aside className="challenge-status" aria-label="이번 주 챌린지 현황">
            <h3>이번 주 챌린지 현황</h3>
            <div className="challenge-lines">
              {[
                ["걷기 6,000보", "92%", "green"],
                ["저염 식단", "78%", "yellow"],
                ["7시간 수면", "85%", "blue"],
                ["혈압 측정", "100%", "pink"],
              ].map(([label, percent, tone]) => (
                <div className="challenge-progress" key={label}>
                  <p>
                    <span>{label}</span>
                    <strong>{percent}</strong>
                  </p>
                  <span className={`progress-track progress-${tone}`}>
                    <i style={{ width: percent }} />
                  </span>
                </div>
              ))}
            </div>
            <p className="preview-label">이번 달 달성 현황</p>
            <div className="weekly-checks" aria-hidden="true">
              <span>✓</span>
              <span>✓</span>
              <span>✓</span>
              <span>✓</span>
              <span>✓</span>
              <span>오</span>
              <span>-</span>
            </div>
          </aside>
        </div>
      </section>

      <section className="landing-section testimonial-section">
        <p className="section-label">사용자 후기</p>
        <h2>24만 명이 선택한 건강 관리 플랫폼</h2>
        <p>실제 사용자들의 생생한 경험을 확인해 보세요.</p>
        <div className="testimonial-grid">
          {testimonials.map(([name, meta, quote, initial]) => (
            <article className="testimonial-card" key={name}>
              <span className="stars">★★★★★</span>
              <p>"{quote}"</p>
              <div>
                <span className="testimonial-avatar">{initial}</span>
                <strong>{name}</strong>
                <small>{meta}</small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-cta">
        <h2>지금 바로 건강을 시작하세요</h2>
        <p>무료로 가입하고 AI 건강 예측 서비스를 경험해 보세요.</p>
        <div className="hero-actions">
          <button className="dark-button" type="button" onClick={() => onNavigate("/login")}>
            무료로 시작하기
          </button>
          <button className="outline-button" type="button" onClick={() => scrollToSection("features")}>
            서비스 둘러보기
          </button>
        </div>
      </section>
    </>
  );
}
