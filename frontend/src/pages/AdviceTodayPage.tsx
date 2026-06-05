import type { AppRoute } from "../App";

type AdviceTodayPageProps = {
  onNavigate: (route: AppRoute) => void;
};

export function AdviceTodayPage({ onNavigate }: AdviceTodayPageProps) {
  return (
    <div className="page-stack">
      <section className="section-header-row">
        <h1>오늘의 조언</h1>
        <div className="button-row">
          <button className="small-button" type="button">
            재생성 1/2회 남음
          </button>
          <button className="green-button" type="button">
            조언 새로 받기
          </button>
          <button className="small-button" type="button" onClick={() => onNavigate("/advices/history")}>
            조언 이력
          </button>
        </div>
      </section>
      <section className="dashboard-card advice-detail-card">
        <div className="advice-title-row">
          <span>AI</span>
          <div>
            <h2>오늘의 AI 건강 조언</h2>
            <p>2026-05-15 08:30 생성</p>
          </div>
        </div>
        <div className="advice-text-box">
          혈압과 LDL 콜레스테롤 관리가 필요해요. 오늘은 짠 음식을 줄이고 20분 가볍게 산책을 해보세요. 수면은
          7시간 이상 확보하시고, 아침 식사는 꼭 챙기세요.
        </div>
        <p>⚠ 본 조언은 참고용이며 의료 진단을 대체하지 않습니다.</p>
      </section>
      <section className="dashboard-card feedback-week-card">
        <h2>최근 7일 조언 피드백 현황</h2>
        <div className="feedback-week-grid">
          {["월", "화", "수", "목", "금", "토", "일"].map((day, index) => (
            <div className={index < 3 ? "good" : index < 5 ? "bad" : ""} key={day}>
              <span>{day}</span>
              <strong>{index < 3 ? "👍" : index < 5 ? "👎" : ""}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
