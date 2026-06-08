import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getChallengeDetail,
  joinChallenge,
  CATEGORY_LABELS,
  DIFFICULTY_LABELS,
  type Challenge,
} from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK: Challenge = {
  id: 1,
  name: "30일 걷기 챌린지",
  description: "매일 30분 이상 걷기를 실천하여 건강한 생활 습관을 만들어보세요!",
  category: "WALK",
  difficulty: "EASY",
  duration_days: 30,
  participant_count: 1245,
  avg_completion_rate: 78,
  icon_emoji: "🚶",
  goal_description: "매일 30분 이상 걷기를 통해 심폐 기능 향상과 체중 관리를 목표로 합니다.",
  how_to_join: ["매일 30분 이상 걷기 실천", "운동 기록 앱에 기록하기", "연속 성공 일수 유지하기"],
  daily_mission_example: "오늘의 미션: 30분 이상 걷고 운동 앱에 기록하기",
};

function catClass(cat: string) {
  return { WALK: "walk", WATER: "water", EXERCISE: "exercise", SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive" }[cat] ?? "walk";
}

function diffClass(d: string) {
  return { EASY: "easy", NORMAL: "normal", HARD: "hard" }[d] ?? "normal";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function ChallengeDetailPage({ onNavigate }: Props) {
  const [data, setData] = useState<Challenge | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isJoined, setIsJoined] = useState(false);
  const [isJoining, setIsJoining] = useState(false);

  const challengeId = Number(sessionStorage.getItem("selectedChallengeId") ?? "1");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getChallengeDetail(challengeId, token)
      .then((res) => { setData(res.data); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, [challengeId]);

  async function handleJoin() {
    const token = getStoredAccessToken();
    setIsJoining(true);
    try {
      if (token) await joinChallenge(challengeId, token);
      setIsJoined(true);
    } catch {
      alert("참여 신청에 실패했습니다.");
    } finally {
      setIsJoining(false);
    }
  }

  if (isLoading) return <LoadingState message="챌린지 정보를 불러오는 중입니다." />;

  const c = data ?? FALLBACK;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지 관리</p>
          <h1>챌린지 상세</h1>
        </div>
        <button type="button" className="green-button" onClick={() => onNavigate?.("/challenges/list")}>
          ← 목록으로
        </button>
      </section>

      {hasError && <ErrorState title="챌린지 정보를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />}

      <div className="challenge-detail-grid">
        {/* 좌측 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 대표 이미지 + 제목 */}
          <div className="dashboard-card" style={{ padding: 20 }}>
            <div className="challenge-detail-image">
              {c.icon_emoji ? (
                <span style={{ fontSize: 64 }}>{c.icon_emoji}</span>
              ) : (
                <span>대표 이미지</span>
              )}
            </div>
            <h2 className="challenge-detail-title">
              {c.name}
              <span className={`challenge-tag ${catClass(c.category)}`}>{CATEGORY_LABELS[c.category]}</span>
              <span className={`challenge-diff-tag ${diffClass(c.difficulty)}`}>{DIFFICULTY_LABELS[c.difficulty]}</span>
            </h2>
            <p className="challenge-detail-subtitle">{c.description}</p>
          </div>

          {/* 챌린지 소개 */}
          <div className="challenge-detail-section">
            <h3>챌린지 소개</h3>

            <div>
              <h4>목표</h4>
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                {c.goal_description ?? "건강한 생활 습관 형성을 목표로 합니다."}
              </p>
              <div style={{ height: 4, background: "var(--muted)", borderRadius: 2, marginTop: 10 }} />
              <div style={{ height: 4, width: "60%", background: "var(--muted)", borderRadius: 2, marginTop: 6 }} />
            </div>

            {c.how_to_join && (
              <div>
                <h4>참여 방법</h4>
                <ul className="challenge-how-list">
                  {c.how_to_join.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </div>
            )}

            {c.daily_mission_example && (
              <div>
                <h4>하루 미션 예시</h4>
                <div style={{ height: 4, background: "var(--muted)", borderRadius: 2 }} />
                <div style={{ height: 4, width: "70%", background: "var(--muted)", borderRadius: 2, marginTop: 6 }} />
              </div>
            )}
          </div>

          {/* 획득 가능한 보상 */}
          <div className="challenge-detail-section">
            <h3>획득 가능한 보상</h3>
            <div className="challenge-reward-grid">
              <div className="challenge-reward-item">
                <span className="reward-icon">🏆</span>
                <span className="reward-label">챌린지 완료 뱃지</span>
              </div>
              <div className="challenge-reward-item">
                <span className="reward-icon">⭐</span>
                <span className="reward-label">500점</span>
              </div>
            </div>
          </div>
        </div>

        {/* 우측 사이드바 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="challenge-sidebar-card">
            <div className="challenge-sidebar-section">
              <p className="challenge-sidebar-label">기간 정보</p>
              <p style={{ margin: 0, fontSize: 12, color: "var(--muted-foreground)" }}>챌린지 기간</p>
              <p className="challenge-sidebar-value">{c.duration_days}일</p>
            </div>

            <div className="challenge-sidebar-section">
              <p className="challenge-sidebar-label">참여 현황</p>
              <p style={{ margin: 0, fontSize: 12, color: "var(--muted-foreground)" }}>현재 참여자</p>
              <p className="challenge-sidebar-value">{c.participant_count.toLocaleString()}명</p>
              <p style={{ margin: "6px 0 4px", fontSize: 12, color: "var(--muted-foreground)" }}>평균 완료율</p>
              <div className="challenge-participants-bar">
                <div className="challenge-participants-fill" style={{ width: `${c.avg_completion_rate}%` }} />
              </div>
            </div>

            <div className="challenge-sidebar-section">
              <p className="challenge-sidebar-label">참여하기</p>
              {isJoined ? (
                <button type="button" className="challenge-joined-btn" style={{ marginTop: 4 }}>
                  참여 중
                </button>
              ) : (
                <button
                  type="button"
                  className="challenge-start-btn"
                  style={{ marginTop: 4 }}
                  onClick={handleJoin}
                  disabled={isJoining}
                >
                  {isJoining ? "처리 중..." : "챌린지 시작하기"}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
