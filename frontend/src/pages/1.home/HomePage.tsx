import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getHomeSummary, type HomeSummary } from "../../api/home";
import { getCurrentUser } from "../../api/users";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { localDotDateLabel, localKoreanDateLabel } from "../../utils/date";

const fallbackHomeSummary: HomeSummary = {
  today_score: {
    score: 78,
    status: "GOOD",
    message: "양호",
    calculation_basis: ["최근 7일 건강 기록", "챌린지 달성률", "예측 결과"],
  },
  recent_prediction: {
    result_id: 1,
    overall_risk_level: "HIGH",
    at_risk_diseases: ["고혈압"],
    created_at: "2026-05-10T09:00:00",
  },
  today_advice: {
    advice_id: 1,
    title: "오늘의 조언",
    content: "혈압과 LDL 콜레스테롤 관리가 필요해요. 오늘은 짠 음식을 줄이고 20분 산책을 해보세요.",
    is_placeholder: false,
  },
  challenge_summary: {
    active_count: 3,
    completion_rate: 78,
    message: "오늘 체크인할 챌린지가 있습니다.",
  },
  health_metric_summary: {
    dyslipidemia: {
      status: "CAUTION",
      label: "주의",
      message: "혈당 관리가 필요합니다.",
    },
    obesity: {
      status: "GOOD",
      label: "양호",
      message: "운동 점수가 안정적입니다.",
    },
  },
  quick_record_status: {
    has_health_survey: true,
    has_lipid_obesity_record: false,
    has_renal_record: false,
  },
  unread_notification_count: 3,
};

type HomePageProps = {
  onNavigate?: (route: AppRoute) => void;
};

function formatDateLabel() {
  return localKoreanDateLabel();
}

function recentPredictionDateLabel(summary: HomeSummary) {
  return summary.recent_prediction?.created_at?.slice(0, 10) ?? "예측 결과 없음";
}

function predictionLabel(summary: HomeSummary) {
  const prediction = summary.recent_prediction;
  if (!prediction) {
    return "아직 예측 결과가 없습니다.";
  }
  const disease = prediction.at_risk_diseases[0] ?? "만성질환";
  return `${disease} 위험도 ${prediction.overall_risk_level === "HIGH" ? "높음" : "확인 필요"}`;
}

export function HomePage({ onNavigate }: HomePageProps) {
  const [summary, setSummary] = useState<HomeSummary>(fallbackHomeSummary);
  const [userName, setUserName] = useState("사용자");
  const [isLoading, setIsLoading] = useState(false);
  const [hasApiError, setHasApiError] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      return;
    }

    setIsLoading(true);
    getCurrentUser(token)
      .then((user) => setUserName(user.name))
      .catch(() => setUserName("사용자"));
    getHomeSummary(token)
      .then((response) => {
        setSummary(response.data);
        setHasApiError(false);
      })
      .catch(() => setHasApiError(true))
      .finally(() => setIsLoading(false));
  }, []);

  const recentScoreBars = useMemo(() => [42, 48, 36, 58, 50, 62, 78], []);

  if (isLoading) {
    return <LoadingState message="홈 데이터를 불러오는 중입니다." />;
  }

  return (
    <div className="home-page">
      <section className="home-header">
        <div>
          <h1>안녕하세요, {userName}님 👋</h1>
          <p>{formatDateLabel()}</p>
        </div>
        <button className="notification-button" type="button" onClick={() => onNavigate?.("/notifications")}>
          🔔 알림
          {summary.unread_notification_count > 0 && <span>{summary.unread_notification_count}</span>}
        </button>
      </section>

      {hasApiError && (
        <ErrorState
          title="백엔드 홈 데이터를 불러오지 못했습니다."
          description="현재 화면은 와이어프레임 확인용 예시 데이터로 표시됩니다."
        />
      )}

      {!summary.quick_record_status.has_lipid_obesity_record && (
        <section className="warning-banner">
          <strong>⚠</strong>
          <span>오늘 혈당 데이터를 아직 입력하지 않았어요. 입력하면 최대 20점을 더 받을 수 있어요.</span>
          <button type="button" onClick={() => onNavigate?.("/health")}>
            입력하기
          </button>
        </section>
      )}

      <section className="home-main-grid">
        <article className="dashboard-card health-score-card">
          <h2>오늘의 건강 점수</h2>
          <div className="score-value">
            <strong>{summary.today_score.score ?? "-"}</strong>
            <span>/ 110점</span>
          </div>
          <div className="score-badges">
            <span>B등급</span>
            <span>{summary.today_score.message}</span>
          </div>
          <div className="score-delta">전일 대비 +3점 상승 ↑</div>
          <div className="recent-bars" aria-label="최근 7일 점수">
            {recentScoreBars.map((height, index) => (
              <span key={index} style={{ height: `${height}px` }} />
            ))}
          </div>
        </article>

        <article className="dashboard-card recent-prediction-card">
          <h2>최근 예측 결과</h2>
          <div className="prediction-summary-box">
            <p>{recentPredictionDateLabel(summary)} · 3대 만성질환</p>
            <strong>{predictionLabel(summary)}</strong>
            <span>신뢰도 78% · 주요 요인: BMI, 수축기혈압, LDL</span>
          </div>
          <button className="green-button" type="button" onClick={() => onNavigate?.("/prediction/request")}>
            새 예측 요청
          </button>
        </article>

        <article className="dashboard-card today-advice-card">
          <h2>오늘의 조언</h2>
          <div className="advice-inline">
            <span>AI</span>
            <p>{summary.today_advice.content}</p>
          </div>
          <button className="wide-subtle-button" type="button" onClick={() => onNavigate?.("/advices/today")}>
            조언 상세보기
          </button>
        </article>

        <article className="dashboard-card challenge-summary-card">
          <h2>진행 중 챌린지</h2>
          <div className="challenge-stat-grid">
            <div>
              <span>참여 중</span>
              <strong>{summary.challenge_summary.active_count}</strong>
            </div>
            <div>
              <span>달성률</span>
              <strong>{Math.round(summary.challenge_summary.completion_rate)}%</strong>
            </div>
            <div>
              <span>오늘</span>
              <strong>✓</strong>
            </div>
          </div>
          <button className="wide-subtle-button" type="button" onClick={() => onNavigate?.("/challenges")}>
            챌린지 보기
          </button>
        </article>
      </section>

      <section className="dashboard-card health-dashboard-card">
        <div className="section-header-row">
          <h2>나의 건강 대시보드</h2>
          <span>{localDotDateLabel()}</span>
        </div>
        <div className="metric-status-grid">
          <div className="metric-card metric-normal">
            <span>혈압 지수</span>
            <strong>정상</strong>
          </div>
          <div className="metric-card metric-warning">
            <span>혈당 관리</span>
            <strong>{summary.health_metric_summary.dyslipidemia.label}</strong>
          </div>
          <div className="metric-card metric-good">
            <span>운동 점수</span>
            <strong>{summary.health_metric_summary.obesity.label}</strong>
          </div>
        </div>
        <p className="mini-label">최근 건강 수치 최근 7일</p>
        <div className="health-bars" aria-hidden="true">
          {recentScoreBars.map((height, index) => (
            <span key={index} style={{ height: `${height + 26}px` }} />
          ))}
        </div>
        <div className="goal-lines">
          <div>
            <span>걸음수 목표</span>
            <strong>85%</strong>
          </div>
          <progress max="100" value="85" />
          <div>
            <span>수분 섭취</span>
            <strong>45%</strong>
          </div>
          <progress max="100" value="45" />
        </div>
      </section>

      <section className="quick-record-section">
        <h2>빠른 기록</h2>
        <div className="quick-record-grid">
          {[
            ["건강 수치 기록", "/health/vitals/input"],
            ["운동 기록", "/health/vitals/input"],
            ["식단 기록", "/food/analyze"],
          ].map(([label, route]) => (
            <button key={label} type="button" onClick={() => onNavigate?.(route as AppRoute)}>
              <span>+</span>
              {label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
