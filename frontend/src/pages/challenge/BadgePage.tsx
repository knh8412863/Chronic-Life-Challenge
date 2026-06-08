import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getBadges, type Badge, type BadgeListData } from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type BadgeFilter = "ALL" | "3_STREAK" | "7_STREAK" | "30_STREAK";

const FALLBACK: BadgeListData = {
  earned_count: 8,
  total_count: 12,
  badges: [
    { id: 1, challenge_id: 1, challenge_name: "30일 걷기 챌린지", badge_type: "3_STREAK", streak_days: 3, is_earned: true, earned_at: "2026.05.14", points: 3, icon_emoji: "🥉", progress_percent: 100 },
    { id: 2, challenge_id: 1, challenge_name: "30일 걷기 챌린지", badge_type: "7_STREAK", streak_days: 7, is_earned: true, earned_at: "2026.05.10", points: 5, icon_emoji: "🥈", progress_percent: 100 },
    { id: 3, challenge_id: 1, challenge_name: "30일 걷기 챌린지", badge_type: "30_STREAK", streak_days: 30, is_earned: true, earned_at: "2026.05.01", points: 10, icon_emoji: "🥇", progress_percent: 100 },
    { id: 4, challenge_id: 2, challenge_name: "혈당 관리 마스터", badge_type: "3_STREAK", streak_days: 3, is_earned: true, earned_at: "2026.04.28", points: 3, icon_emoji: "🥉", progress_percent: 100 },
    { id: 5, challenge_id: 2, challenge_name: "혈당 관리 마스터", badge_type: "7_STREAK", streak_days: 7, is_earned: false, points: 5, icon_emoji: "🥈", current_streak: 5, progress_percent: 71 },
    { id: 6, challenge_id: 2, challenge_name: "혈당 관리 마스터", badge_type: "30_STREAK", streak_days: 30, is_earned: false, points: 10, icon_emoji: "🥇", current_streak: 5, progress_percent: 17 },
    { id: 7, challenge_id: 3, challenge_name: "저염식 습관", badge_type: "3_STREAK", streak_days: 3, is_earned: true, earned_at: "2026.05.05", points: 3, icon_emoji: "🥉", progress_percent: 100 },
    { id: 8, challenge_id: 3, challenge_name: "저염식 습관", badge_type: "7_STREAK", streak_days: 7, is_earned: false, points: 5, icon_emoji: "🥈", current_streak: 2, progress_percent: 29 },
    { id: 9, challenge_id: 3, challenge_name: "저염식 습관", badge_type: "30_STREAK", streak_days: 30, is_earned: false, points: 10, icon_emoji: "🥇", current_streak: 2, progress_percent: 7 },
    { id: 10, challenge_id: 4, challenge_name: "수면 개선 챌린지", badge_type: "3_STREAK", streak_days: 3, is_earned: false, points: 3, icon_emoji: "🥉", current_streak: 0, progress_percent: 0 },
    { id: 11, challenge_id: 4, challenge_name: "수면 개선 챌린지", badge_type: "7_STREAK", streak_days: 7, is_earned: false, points: 5, icon_emoji: "🥈", current_streak: 0, progress_percent: 0 },
    { id: 12, challenge_id: 4, challenge_name: "수면 개선 챌린지", badge_type: "30_STREAK", streak_days: 30, is_earned: false, points: 10, icon_emoji: "🥇", current_streak: 0, progress_percent: 0 },
  ],
};

const FILTER_TABS: Array<{ key: BadgeFilter; label: string }> = [
  { key: "ALL", label: "전체" },
  { key: "3_STREAK", label: "3일 스트릭" },
  { key: "7_STREAK", label: "7일 스트릭" },
  { key: "30_STREAK", label: "30일 스트릭" },
];

function badgeTypeLabel(t: string) {
  if (t === "3_STREAK") return "3일 연속";
  if (t === "7_STREAK") return "7일 연속";
  return "30일 연속";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function BadgePage({ onNavigate }: Props) {
  const [data, setData] = useState<BadgeListData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [filter, setFilter] = useState<BadgeFilter>("ALL");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getBadges(token)
      .then((res) => { setData(res.data); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState message="뱃지 정보를 불러오는 중입니다." />;

  const d = data ?? FALLBACK;
  const displayBadges = filter === "ALL" ? d.badges : d.badges.filter((b) => b.badge_type === filter);
  const earnedBadges = d.badges.filter((b) => b.is_earned).sort((a, b) => (b.earned_at ?? "").localeCompare(a.earned_at ?? "")).slice(0, 3);

  const earnedPct = d.total_count > 0 ? Math.round((d.earned_count / d.total_count) * 100) : 0;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지 관리</p>
          <h1>뱃지 목록</h1>
        </div>
      </section>

      {hasError && <ErrorState title="뱃지 정보를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />}

      {/* 뱃지 획득 요약 */}
      <div className="badge-summary-row">
        <div>
          <p className="badge-earned-count">획득한 뱃지</p>
          <p className="badge-earned-num">{d.earned_count}개 획득</p>
        </div>
        <div className="badge-total-bar-wrap">
          <p className="badge-total-label">전체 달성률</p>
          <div className="badge-total-bar">
            <div className="badge-total-fill" style={{ width: `${earnedPct}%` }} />
          </div>
        </div>
        <button type="button" className="badge-view-all-btn">전체 보기</button>
      </div>

      {/* 필터 탭 */}
      <div className="badge-filter-tabs">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`badge-filter-tab ${filter === tab.key ? "active" : ""}`}
            onClick={() => setFilter(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 뱃지 카드 그리드 */}
      <div className="badge-card-grid">
        {displayBadges.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} />
        ))}
      </div>

      {/* 최근 획득한 뱃지 */}
      {earnedBadges.length > 0 && (
        <section className="dashboard-card">
          <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>최근 획득한 뱃지</h2>
          <div className="recent-badge-list">
            {earnedBadges.map((badge) => (
              <div key={badge.id} className="recent-badge-item">
                <div className="recent-badge-icon">{badge.icon_emoji ?? "🏅"}</div>
                <div className="recent-badge-info">
                  <p className="recent-badge-name">{badge.challenge_name}</p>
                  <p className="recent-badge-streak">{badgeTypeLabel(badge.badge_type)}</p>
                </div>
                {badge.earned_at && (
                  <span className="recent-badge-date">획득일: {badge.earned_at}</span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function BadgeCard({ badge }: { badge: Badge }) {
  const isEarned = badge.is_earned;

  return (
    <div className={`badge-card ${isEarned ? "earned" : "not-earned"}`}>
      <div className={`badge-icon-wrap ${isEarned ? "" : "not-earned"}`}>
        {badge.icon_emoji ?? "🏅"}
      </div>
      <p className="badge-card-name">{badge.challenge_name}</p>
      <p className="badge-card-streak">{badgeTypeLabel(badge.badge_type)}</p>
      <p className="badge-card-points">+{badge.points}점</p>

      {isEarned ? (
        <div className="badge-card-status earned-status">획득 완료</div>
      ) : (
        <div className="badge-card-progress-wrap">
          {badge.current_streak != null ? (
            <>
              <div className="challenge-progress-bar">
                <div className="challenge-progress-fill" style={{ width: `${badge.progress_percent ?? 0}%` }} />
              </div>
              <p className="badge-card-target-label">
                현재 {badge.current_streak}일 연속 중
              </p>
              <p className="badge-card-target-label">
                {badge.streak_days}일 달성 시 획득
              </p>
            </>
          ) : (
            <p className="badge-card-target-label">미취득</p>
          )}
        </div>
      )}
    </div>
  );
}
