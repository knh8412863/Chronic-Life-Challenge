import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { ApiError } from "../../api/client";
import {
  getChallengeList,
  joinChallenge,
  CATEGORY_LABELS,
  type Challenge,
  type ChallengeCategory,
  type ChallengeListQuery,
} from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK_CHALLENGES: Challenge[] = [
  { id: 1, name: "30일 걷기 챌린지", description: "매일 30분 이상 걷기", category: "WALK", difficulty: "EASY", duration_days: 30, participant_count: 1245, avg_completion_rate: 78, icon_emoji: "🚶" },
  { id: 2, name: "수분 섭취 챌린지", description: "매일 물 2L 마시기", category: "WATER", difficulty: "NORMAL", duration_days: 30, participant_count: 876, avg_completion_rate: 65, icon_emoji: "💧" },
  { id: 3, name: "저염식 습관", description: "나트륨 섭취 줄이기", category: "DIET", difficulty: "NORMAL", duration_days: 30, participant_count: 654, avg_completion_rate: 72, icon_emoji: "🥗" },
  { id: 4, name: "규칙적 운동", description: "주 5회 운동 실천", category: "EXERCISE", difficulty: "HARD", duration_days: 21, participant_count: 432, avg_completion_rate: 55, icon_emoji: "🏃" },
  { id: 5, name: "수면 개선 프로젝트", description: "규칙적인 수면 습관", category: "SLEEP", difficulty: "EASY", duration_days: 30, participant_count: 987, avg_completion_rate: 70, icon_emoji: "😴" },
  { id: 6, name: "종합 건강 관리", description: "전반적 건강 습관", category: "COMPREHENSIVE", difficulty: "NORMAL", duration_days: 90, participant_count: 1543, avg_completion_rate: 62, icon_emoji: "🎯" },
];

type CategoryFilter = "ALL" | ChallengeCategory;
type SortOption = "POPULAR" | "LATEST" | "DURATION";

const CATEGORY_TABS: Array<{ key: CategoryFilter; label: string }> = [
  { key: "ALL", label: "전체" },
  { key: "WALK", label: "걸음수" },
  { key: "WATER", label: "수분" },
  { key: "EXERCISE", label: "운동" },
  { key: "SLEEP", label: "수면" },
  { key: "DIET", label: "식단" },
  { key: "COMPREHENSIVE", label: "종합" },
];

function catClass(cat: ChallengeCategory) {
  return { WALK: "walk", WATER: "water", EXERCISE: "exercise", SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive" }[cat] ?? "walk";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function ChallengeListPage({ onNavigate }: Props) {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [joinedIds, setJoinedIds] = useState<Set<number>>(new Set());
  const [joinErrorMessage, setJoinErrorMessage] = useState("");

  const [category, setCategory] = useState<CategoryFilter>("ALL");
  const [sort, setSort] = useState<SortOption>("POPULAR");

  function fetchList(query: ChallengeListQuery) {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getChallengeList(query, token)
      .then((res) => {
        setChallenges(res.data.items);
        setJoinedIds(new Set(res.data.items.filter((item) => item.is_joined).map((item) => item.id)));
        setHasMore(res.data.has_more);
        setHasError(false);
      })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    fetchList({ category: category === "ALL" ? "ALL" : category, sort });
  }, [category, sort]);

  const isUsingFallback = challenges.length === 0;
  const displayItems = isUsingFallback ? filterFallback(FALLBACK_CHALLENGES, category) : challenges;

  function filterFallback(items: Challenge[], cat: CategoryFilter) {
    return items.filter((c) => cat === "ALL" || c.category === cat);
  }

  async function handleJoin(challengeId: number) {
    const token = getStoredAccessToken();
    if (!token) {
      setJoinErrorMessage("로그인 후 챌린지에 참여할 수 있습니다.");
      return;
    }

    try {
      await joinChallenge(challengeId, token);
      const next = new Set(joinedIds);
      next.add(challengeId);
      setJoinedIds(next);
      sessionStorage.setItem("selectedChallengeId", String(challengeId));
      onNavigate?.("/challenges/detail");
    } catch (error) {
      const detail = error instanceof ApiError ? error.detail : undefined;
      setJoinErrorMessage(typeof detail === "string" ? detail : "챌린지 참여에 실패했습니다. 로그인 상태 또는 참여 조건을 확인해 주세요.");
    }
  }

  function handleDetail(challengeId: number) {
    sessionStorage.setItem("selectedChallengeId", String(challengeId));
    onNavigate?.("/challenges/detail");
  }

  if (isLoading) return <LoadingState message="챌린지 목록을 불러오는 중입니다." />;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지</p>
          <h1>챌린지 목록</h1>
        </div>
      </section>

      {hasError && <ErrorState title="목록을 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />}

      {/* 카테고리 탭 */}
      <div className="challenge-category-tabs">
        {CATEGORY_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`challenge-category-tab ${category === tab.key ? "active" : ""}`}
            onClick={() => setCategory(tab.key)}
          >
            {tab.label}
          </button>
        ))}
        <select
          className="challenge-filter-select"
          value={sort}
          onChange={(e) => setSort(e.target.value as SortOption)}
          style={{ marginLeft: "auto", maxWidth: 140 }}
        >
          <option value="POPULAR">인기순</option>
          <option value="LATEST">최신순</option>
          <option value="DURATION">기간순</option>
        </select>
      </div>

      {/* 챌린지 카드 그리드 */}
      <div className="challenge-card-grid">
        {displayItems.map((c) => {
          const isJoined = joinedIds.has(c.id);
          return (
            <div key={c.id} className="challenge-card" onClick={() => handleDetail(c.id)} style={{ cursor: "pointer" }}>
              {c.id % 3 === 0 && <span className="challenge-dot-new" />}
              <div className="challenge-card-icon">{c.icon_emoji ?? "🏆"}</div>
              <p className="challenge-card-name">{c.name}</p>
              <p className="challenge-card-desc">{c.description}</p>
              <div className="challenge-card-tags">
                <span className="challenge-diff-tag">{c.duration_days}일</span>
              </div>
              <p className="challenge-card-participants">참여 {c.participant_count.toLocaleString()}명</p>
              {isUsingFallback ? (
                <button
                  type="button"
                  className="challenge-joined-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setJoinErrorMessage("현재 화면은 예시 챌린지입니다. 실제 챌린지 데이터가 등록된 뒤 참여할 수 있습니다.");
                  }}
                >
                  참여 불가
                </button>
              ) : isJoined ? (
                <button type="button" className="challenge-joined-btn" onClick={(e) => e.stopPropagation()}>참여 중</button>
              ) : (
                <button
                  type="button"
                  className="challenge-join-btn"
                  onClick={(e) => { e.stopPropagation(); handleJoin(c.id); }}
                >
                  참여하기
                </button>
              )}
            </div>
          );
        })}
      </div>

      {hasMore && (
        <button
          type="button"
          className="challenge-load-more"
          onClick={() => fetchList({ category: category === "ALL" ? "ALL" : category, sort, page: 2 })}
        >
          더 보기
        </button>
      )}
      {!hasMore && displayItems.length > 0 && (
        <button type="button" className="challenge-load-more" disabled style={{ opacity: 0.5 }}>
          더 보기
        </button>
      )}
      {joinErrorMessage && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div style={{ width: 360, background: "#fff", borderRadius: 12, padding: 22, boxShadow: "0 18px 40px rgba(15,23,42,0.16)" }}>
            <h3 style={{ margin: "0 0 10px", fontSize: 16 }}>챌린지 참여 실패</h3>
            <p style={{ margin: "0 0 18px", color: "#555", fontSize: 13, lineHeight: 1.5 }}>{joinErrorMessage}</p>
            <button type="button" className="green-button" style={{ width: "100%" }} onClick={() => setJoinErrorMessage("")}>
              확인
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
