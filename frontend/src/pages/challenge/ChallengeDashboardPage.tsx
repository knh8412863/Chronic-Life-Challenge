import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getDashboard,
  CATEGORY_LABELS,
  type ChallengeDashboard,
  type MyChallenge,
} from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK: ChallengeDashboard = {
  in_progress_count: 3,
  weekly_completion_rate: 78,
  streak_days: 12,
  total_completed_missions: 24,
  in_progress_challenges: [
    {
      id: 1,
      challenge: { id: 1, name: "30일 걷기 챌린지", description: "", category: "WALK", difficulty: "EASY", duration_days: 30, participant_count: 1245, avg_completion_rate: 78, icon_emoji: "🚶" },
      status: "IN_PROGRESS",
      progress_percent: 65,
      days_remaining: 16,
      today_mission: "30분 이상 걷기",
      today_completed: true,
    },
    {
      id: 2,
      challenge: { id: 2, name: "혈당 관리 마스터", description: "", category: "DIET", difficulty: "NORMAL", duration_days: 60, participant_count: 654, avg_completion_rate: 45, icon_emoji: "🩸" },
      status: "IN_PROGRESS",
      progress_percent: 45,
      days_remaining: 34,
      today_mission: "혈당 측정 기록",
      today_completed: false,
    },
    {
      id: 3,
      challenge: { id: 3, name: "저염식 습관", description: "", category: "DIET", difficulty: "NORMAL", duration_days: 30, participant_count: 654, avg_completion_rate: 80, icon_emoji: "🥗" },
      status: "IN_PROGRESS",
      progress_percent: 80,
      days_remaining: 6,
      today_mission: "나트륨 섭취 체크",
      today_completed: true,
    },
  ],
  today_missions: [
    { challenge_id: 1, challenge_name: "30일 걷기 챌린지", description: "30분 이상 걷기", completed: true },
    { challenge_id: 2, challenge_name: "혈당 관리 마스터", description: "혈당 측정 기록", completed: true },
    { challenge_id: 3, challenge_name: "저염식 습관", description: "저염 식단 1회", completed: false },
    { challenge_id: 3, challenge_name: "저염식 습관", description: "물 8잔 마시기", completed: false },
  ],
  completed_challenge_count: 8,
  earned_badge_count: 12,
  weekly_activity: [true, true, true, true, true, false, false],
};

const WEEK_LABELS = ["월", "화", "수", "목", "금", "토", "일"];

function categoryClass(cat: string) {
  const map: Record<string, string> = {
    WALK: "walk", WATER: "water", EXERCISE: "exercise",
    SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive",
  };
  return map[cat] ?? "walk";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function ChallengeDashboardPage({ onNavigate }: Props) {
  const [data, setData] = useState<ChallengeDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getDashboard(token)
      .then((res) => { setData(res.data); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState message="챌린지 정보를 불러오는 중입니다." />;

  const d = data ?? FALLBACK;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지 관리</p>
          <h1>챌린지 요약</h1>
        </div>
      </section>

      {hasError && (
        <ErrorState title="데이터를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />
      )}

      {/* 통계 카드 4개 */}
      <div className="challenge-stat-grid">
        <div className="challenge-stat-card blue">
          <span className="stat-label">진행 중</span>
          <strong className="stat-value">{d.in_progress_count}<span className="stat-unit">개</span></strong>
        </div>
        <div className="challenge-stat-card yellow">
          <span className="stat-label">이번 주 달성률</span>
          <strong className="stat-value">{d.weekly_completion_rate}<span className="stat-unit">%</span></strong>
        </div>
        <div className="challenge-stat-card">
          <span className="stat-label">연속 성공</span>
          <strong className="stat-value">{d.streak_days}<span className="stat-unit">일</span></strong>
        </div>
        <div className="challenge-stat-card pink">
          <span className="stat-label">완료 미션</span>
          <strong className="stat-value">{d.total_completed_missions}<span className="stat-unit">개</span></strong>
        </div>
      </div>

      <div className="challenge-dashboard-grid">
        {/* 좌측 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 진행 중 챌린지 */}
          <section className="dashboard-card">
            <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>진행 중 챌린지</h2>
            <div className="challenge-in-progress-list">
              {d.in_progress_challenges.map((mc) => (
                <InProgressItem key={mc.id} mc={mc} />
              ))}
            </div>
          </section>

          {/* 오늘의 미션 */}
          <section className="dashboard-card">
            <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>오늘의 미션</h2>
            <div className="challenge-mission-list">
              {d.today_missions.map((m, i) => (
                <div key={i} className="challenge-mission-item">
                  <div className={`challenge-mission-check ${m.completed ? "done" : ""}`}>
                    {m.completed && <span style={{ fontSize: 13 }}>✓</span>}
                  </div>
                  <span style={{ color: m.completed ? "var(--muted-foreground)" : "inherit", textDecoration: m.completed ? "line-through" : "none" }}>
                    {m.description}
                  </span>
                </div>
              ))}
            </div>
            <p className="challenge-mission-note">행동 데이터를 입력하면 자동으로 달성됩니다</p>
          </section>
        </div>

        {/* 우측 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 나의 성과 */}
          <section className="dashboard-card">
            <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>나의 성과</h2>
            <div style={{ padding: "0 20px" }}>
              <div className="achievement-grid">
                <div className="achievement-card">
                  <p className="ach-label">완료한 챌린지</p>
                  <strong className="ach-value">{d.completed_challenge_count}</strong>
                </div>
                <div className="achievement-card">
                  <p className="ach-label">획득 뱃지</p>
                  <strong className="ach-value">{d.earned_badge_count}</strong>
                </div>
              </div>
              <div className="streak-record-box" style={{ marginTop: 12, marginBottom: 16 }}>
                <span style={{ fontSize: 20 }}>🔥</span>
                <div>
                  <p className="streak-text" style={{ margin: 0 }}>연속 성공 기록</p>
                  <p className="streak-sub" style={{ margin: 0 }}>{d.streak_days}일 연속 미션 완료!</p>
                </div>
              </div>
            </div>
          </section>

          {/* 빠른 이동 */}
          <section className="dashboard-card">
            <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>빠른 이동</h2>
            <div className="challenge-quick-nav">
              <button className="challenge-quick-btn" onClick={() => onNavigate?.("/challenges/list")}>챌린지 목록 보기</button>
              <button className="challenge-quick-btn" onClick={() => onNavigate?.("/challenges/leaderboard")}>리더보드 보기</button>
              <button className="challenge-quick-btn" onClick={() => onNavigate?.("/challenges/my")}>내 챌린지 현황</button>
              <button className="challenge-quick-btn" onClick={() => onNavigate?.("/challenges/badges")}>뱃지 목록 보기</button>
            </div>
          </section>

          {/* 주간 활동 */}
          <section className="dashboard-card">
            <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>주간 활동</h2>
            <div className="challenge-weekly-grid">
              {WEEK_LABELS.map((label, i) => (
                <div key={label}>
                  <p className="challenge-weekly-label">{label}</p>
                  <div className={`challenge-weekly-dot ${d.weekly_activity[i] ? "done" : ""}`}>
                    {d.weekly_activity[i] && <span style={{ fontSize: 14 }}>✓</span>}
                  </div>
                </div>
              ))}
            </div>
            <div className="challenge-weekly-legend">
              <span>
                <span className="challenge-weekly-legend-dot" style={{ background: "var(--brand-green)" }} />
                챌린지 달성 완료
              </span>
              <span>
                <span className="challenge-weekly-legend-dot" style={{ background: "var(--border)", border: "1px solid var(--border)" }} />
                미달성 또는 기록 없음
              </span>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function InProgressItem({ mc }: { mc: MyChallenge }) {
  const cat = mc.challenge.category;
  const catClass = { WALK: "walk", WATER: "water", EXERCISE: "exercise", SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive" }[cat] ?? "walk";

  return (
    <div className="challenge-in-progress-item">
      <div className="challenge-item-header">
        <span className="challenge-item-name">
          {mc.challenge.name}
          <span className={`challenge-tag ${catClass}`}>{CATEGORY_LABELS[cat]}</span>
        </span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--muted-foreground)", marginBottom: 6 }}>
        <span>진행률</span>
        <span>{mc.progress_percent}%</span>
      </div>
      <div className="challenge-progress-bar">
        <div className="challenge-progress-fill" style={{ width: `${mc.progress_percent}%` }} />
      </div>
    </div>
  );
}
