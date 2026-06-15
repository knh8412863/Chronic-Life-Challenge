import { useEffect, useMemo, useState } from "react";

import type { AppRoute } from "../../App";
import { getTodayActivity, type DailyActivity } from "../../api/activity";
import { getStoredAccessToken } from "../../api/auth";
import { getBadges, getMyChallenges } from "../../api/challenges";
import { getHomeSummary, type HomeSummary } from "../../api/home";
import { getMyVirtualPet, type PetGrowthStage, type PetType } from "../../api/pets";
import { getCurrentUser } from "../../api/users";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { localDotDateLabel, localKoreanDateLabel } from "../../utils/date";
import { getPetImage } from "../../utils/petAssets";

const emptyHomeSummary: HomeSummary = {
  today_score: {
    score: null,
    status: "NEEDS_INPUT",
    message: "건강 기록 입력 필요",
    calculation_basis: [],
  },
  recent_prediction: null,
  today_advice: {
    advice_id: null,
    title: "오늘의 조언",
    content: "건강 기록을 입력하면 오늘의 맞춤 조언을 확인할 수 있습니다.",
    is_placeholder: true,
  },
  challenge_summary: {
    active_count: 0,
    completion_rate: 0,
    message: "참여 중인 챌린지가 없습니다.",
  },
  health_metric_summary: {
    dyslipidemia: {
      status: "NEEDS_INPUT",
      reasons: ["지질 수치가 입력되지 않았습니다."],
      missing_fields: [],
    },
    obesity: {
      status: "NEEDS_INPUT",
      reasons: ["BMI와 허리둘레가 입력되지 않았습니다."],
      missing_fields: [],
    },
  },
  vital_summary: {
    blood_pressure_label: "미입력",
    blood_pressure_status: "NEEDS_INPUT",
    blood_pressure_value: null,
    glucose_label: "미입력",
    glucose_status: "NEEDS_INPUT",
    glucose_value: null,
    has_today_health_record: false,
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

function progressPercent(current: number | null | undefined, target: number) {
  if (current == null || current <= 0) return 0;
  return Math.min(100, Math.round((current / target) * 100));
}

function metricCardClass(status: string) {
  if (status === "HIGH") return "metric-card metric-critical";
  if (status === "CAUTION") return "metric-card metric-risk";
  if (status === "NORMAL") return "metric-card metric-normal";
  return "metric-card metric-missing";
}

function combinedMetricStatus(statuses: string[]) {
  if (statuses.includes("UNAVAILABLE") || statuses.includes("NEEDS_INPUT")) return "NEEDS_INPUT";
  if (statuses.includes("HIGH")) return "HIGH";
  if (statuses.includes("CAUTION")) return "CAUTION";
  if (statuses.includes("NORMAL")) return "NORMAL";
  return "NEEDS_INPUT";
}

function metricStatusLabel(status: string) {
  if (status === "HIGH") return "심각";
  if (status === "CAUTION") return "위험";
  if (status === "NORMAL") return "정상";
  return "미입력";
}

function bestBadgeIcon(
  badges: Array<{ is_earned: boolean; icon_emoji?: string; progress_percent?: number }>,
) {
  const earned = badges.find((badge) => badge.is_earned && badge.icon_emoji);
  if (earned?.icon_emoji) return earned.icon_emoji;
  const next = [...badges].sort((a, b) => (b.progress_percent ?? 0) - (a.progress_percent ?? 0))[0];
  return next?.icon_emoji ?? "🏅";
}

export function HomePage({ onNavigate }: HomePageProps) {
  const [summary, setSummary] = useState<HomeSummary>(emptyHomeSummary);
  const [todayActivity, setTodayActivity] = useState<DailyActivity | null>(null);
  const [userName, setUserName] = useState("사용자");
  const [challengeIcon, setChallengeIcon] = useState("🏆");
  const [badgeSummary, setBadgeSummary] = useState({ earned: 0, total: 0, icon: "🏅" });
  const [petSummary, setPetSummary] = useState<{
    hasPet: boolean;
    name: string;
    level: number;
    health: number;
    image: string | null;
  }>({ hasPet: false, name: "미선택", level: 0, health: 0, image: null });
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
    getTodayActivity(token)
      .then((response) => setTodayActivity(response.data))
      .catch(() => setTodayActivity(null));
    getBadges(token)
      .then((response) =>
        setBadgeSummary({
          earned: response.data.earned_count,
          total: response.data.total_count,
          icon: bestBadgeIcon(response.data.badges),
        }),
      )
      .catch(() => setBadgeSummary({ earned: 0, total: 0, icon: "🏅" }));
    getMyChallenges(token)
      .then((response) => {
        const active = response.data.in_progress[0];
        setChallengeIcon(active?.challenge.icon_emoji ?? "🏆");
      })
      .catch(() => setChallengeIcon("🏆"));
    getMyVirtualPet(token)
      .then((response) => {
        const pet = response.data.pet;
        setPetSummary({
          hasPet: response.data.has_pet,
          name: pet?.pet_name ?? "미선택",
          level: pet?.level ?? 0,
          health: pet?.health_percent ?? 0,
          image: pet ? getPetImage(pet.pet_type as PetType, pet.growth_stage as PetGrowthStage) : null,
        });
      })
      .catch(() => setPetSummary({ hasPet: false, name: "미선택", level: 0, health: 0, image: null }));
  }, []);

  const recentScoreBars = useMemo(() => {
    if (summary.today_score.score == null) return [];
    const base = Math.max(20, Math.min(100, summary.today_score.score));
    return [base - 18, base - 12, base - 20, base - 8, base - 14, base - 4, base].map((value) =>
      Math.max(16, value),
    );
  }, [summary.today_score.score]);
  const stepsProgress = progressPercent(todayActivity?.steps, 10000);
  const waterProgress = progressPercent(todayActivity?.water_ml, 2000);

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
          description="화면에는 예시값을 표시하지 않습니다. 잠시 후 다시 시도해주세요."
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

      <section className="home-summary-strip">
        <button type="button" className="home-summary-card" onClick={() => onNavigate?.("/challenges")}>
          <span className="home-summary-visual" aria-hidden="true">{challengeIcon}</span>
          <span className="home-summary-meta">진행 중 챌린지</span>
          <strong>{summary.challenge_summary.active_count}개</strong>
          <small>달성률 {Math.round(summary.challenge_summary.completion_rate)}%</small>
        </button>
        <button type="button" className="home-summary-card" onClick={() => onNavigate?.("/challenges/badges")}>
          <span className="home-summary-visual" aria-hidden="true">{badgeSummary.icon}</span>
          <span className="home-summary-meta">획득 뱃지</span>
          <strong>{badgeSummary.earned}개</strong>
          <small>전체 {badgeSummary.total}개 중 획득</small>
        </button>
        <button type="button" className="home-summary-card" onClick={() => onNavigate?.(petSummary.hasPet ? "/pet" : "/pet/select")}>
          <span className="home-summary-visual home-summary-pet" aria-hidden="true">
            {petSummary.image ? <img src={petSummary.image} alt="" /> : "🐾"}
          </span>
          <span className="home-summary-meta">나만의 펫</span>
          <strong>{petSummary.hasPet ? `${petSummary.name} Lv.${petSummary.level}` : "선택 필요"}</strong>
          <small>{petSummary.hasPet ? `건강도 ${petSummary.health}%` : "펫을 선택해 보세요"}</small>
        </button>
      </section>

      <section className="home-main-grid">
        <article className="dashboard-card health-score-card">
          <h2>오늘의 건강 점수</h2>
          <div className="score-value">
            <strong>{summary.today_score.score ?? "-"}</strong>
            <span>/ 110점</span>
          </div>
          <div className="score-badges">
            <span>{summary.today_score.score == null ? "미산정" : "건강 점수"}</span>
            <span>{summary.today_score.message}</span>
          </div>
          <div className="score-delta">
            {summary.today_score.score == null ? "건강 기록을 입력하면 점수를 산정합니다." : "최근 기록 기준 건강 점수입니다."}
          </div>
          {recentScoreBars.length > 0 ? (
            <div className="recent-bars" aria-label="최근 7일 점수">
              {recentScoreBars.map((height, index) => (
                <span key={index} style={{ height: `${height}px` }} />
              ))}
            </div>
          ) : (
            <div className="chart-placeholder compact">최근 점수 데이터 없음</div>
          )}
        </article>

        <article className="dashboard-card recent-prediction-card">
          <h2>최근 예측 결과</h2>
          <div className="prediction-summary-box">
            <p>{recentPredictionDateLabel(summary)} · 3대 만성질환</p>
            <strong>{predictionLabel(summary)}</strong>
            <span>{summary.recent_prediction ? "최근 예측 결과를 확인해 주세요." : "예측을 요청하면 결과가 표시됩니다."}</span>
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
          <div className={metricCardClass(summary.vital_summary.blood_pressure_status)}>
            <span>혈압 지수</span>
            <strong>{summary.vital_summary.blood_pressure_label}</strong>
            <small>{summary.vital_summary.blood_pressure_value ?? "오늘 기록 없음"}</small>
          </div>
          <div className={metricCardClass(summary.vital_summary.glucose_status)}>
            <span>공복혈당 관리</span>
            <strong>{summary.vital_summary.glucose_label}</strong>
            <small>{summary.vital_summary.glucose_value ?? "오늘 기록 없음"}</small>
          </div>
          <div
            className={metricCardClass(
              combinedMetricStatus([
                summary.health_metric_summary.obesity.status,
                summary.health_metric_summary.dyslipidemia.status,
              ]),
            )}
          >
            <span>지질/비만</span>
            <strong>{metricStatusLabel(summary.health_metric_summary.obesity.status)}</strong>
            <small>고지혈증 {metricStatusLabel(summary.health_metric_summary.dyslipidemia.status)}</small>
          </div>
        </div>
        <p className="mini-label">최근 건강 수치 최근 7일</p>
          <div className="health-bars" aria-hidden="true">
          {recentScoreBars.length > 0 ? (
            recentScoreBars.map((height, index) => (
              <span key={index} style={{ height: `${height + 26}px` }} />
            ))
          ) : (
            <span style={{ height: "16px" }} />
          )}
        </div>
        <div className="goal-lines">
          <div>
            <span>걸음수 목표</span>
            <strong>{todayActivity?.steps == null ? "미입력" : `${stepsProgress}%`}</strong>
          </div>
          <progress max="100" value={stepsProgress} />
          <div>
            <span>수분 섭취</span>
            <strong>{todayActivity?.water_ml == null ? "미입력" : `${waterProgress}%`}</strong>
          </div>
          <progress max="100" value={waterProgress} />
        </div>
      </section>

      <section className="quick-record-section">
        <h2>빠른 기록</h2>
        <div className="quick-record-grid">
          {[
            ["건강 수치 기록", "/health/vitals/input"],
            ["운동 기록", "/health/vitals/input?tab=exercise"],
            ["식단 기록", "/food/analyze"],
          ].map(([label, route]) => (
            <button key={label} type="button" onClick={() => {
              window.history.pushState({}, "", route);
              onNavigate?.(route.split("?")[0] as AppRoute);
            }}>
              <span>+</span>
              {label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
