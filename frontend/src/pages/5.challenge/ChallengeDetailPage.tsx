import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { ApiError } from "../../api/client";
import {
  getChallengeDetail,
  joinChallenge,
  CATEGORY_LABELS,
  type Challenge,
} from "../../api/challenges";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

function catClass(cat: string) {
  return { WALK: "walk", WATER: "water", EXERCISE: "exercise", SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive" }[cat] ?? "walk";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function ChallengeDetailPage({ onNavigate }: Props) {
  const [data, setData] = useState<Challenge | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isJoined, setIsJoined] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [joinErrorMessage, setJoinErrorMessage] = useState("");

  const challengeId = Number(sessionStorage.getItem("selectedChallengeId") ?? "1");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getChallengeDetail(challengeId, token)
      .then((res) => { setData(res.data); setIsJoined(Boolean(res.data.is_joined)); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, [challengeId]);

  async function handleJoin() {
    const token = getStoredAccessToken();
    if (!token) {
      setJoinErrorMessage("로그인 후 챌린지에 참여할 수 있습니다.");
      return;
    }

    setIsJoining(true);
    try {
      await joinChallenge(challengeId, token);
      setIsJoined(true);
    } catch (error) {
      const detail = error instanceof ApiError ? error.detail : undefined;
      setJoinErrorMessage(typeof detail === "string" ? detail : "챌린지 참여에 실패했습니다. 로그인 상태 또는 참여 조건을 확인해 주세요.");
    } finally {
      setIsJoining(false);
    }
  }

  if (isLoading) return <LoadingState message="챌린지 정보를 불러오는 중입니다." />;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지</p>
          <h1>챌린지 상세</h1>
        </div>
        <button type="button" className="green-button" onClick={() => onNavigate?.("/challenges/list")}>
          ← 목록으로
        </button>
      </section>

      {hasError && <ErrorState title="챌린지 정보를 불러오지 못했습니다." description="선택한 챌린지가 삭제되었거나 서버 연결에 실패했습니다." />}

      {!hasError && !data && (
        <EmptyState title="챌린지 정보를 찾을 수 없습니다." description="목록에서 다시 챌린지를 선택해 주세요." />
      )}

      {data && (
      <>

      <div className="challenge-detail-grid">
        {/* 좌측 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 대표 이미지 + 제목 */}
          <div className="dashboard-card" style={{ padding: 20 }}>
            <div className="challenge-detail-image">
              {data.icon_emoji ? (
                <span style={{ fontSize: 64 }}>{data.icon_emoji}</span>
              ) : (
                <span>대표 이미지</span>
              )}
            </div>
            <h2 className="challenge-detail-title">
              {data.name}
              <span className={`challenge-tag ${catClass(data.category)}`}>{CATEGORY_LABELS[data.category]}</span>
            </h2>
            <p className="challenge-detail-subtitle">{data.description}</p>
          </div>

          {/* 챌린지 소개 */}
          <div className="challenge-detail-section">
            <h3>챌린지 소개</h3>

            <div>
              <h4>목표</h4>
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>
                {data.goal_description ?? "건강한 생활 습관 형성을 목표로 합니다."}
              </p>
              <div style={{ height: 4, background: "var(--muted)", borderRadius: 2, marginTop: 10 }} />
              <div style={{ height: 4, width: "60%", background: "var(--muted)", borderRadius: 2, marginTop: 6 }} />
            </div>

            {data.how_to_join && (
              <div>
                <h4>참여 방법</h4>
                <ul className="challenge-how-list">
                  {data.how_to_join.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.daily_mission_example && (
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
              <p className="challenge-sidebar-value">{data.duration_days}일</p>
            </div>

            <div className="challenge-sidebar-section">
              <p className="challenge-sidebar-label">참여 현황</p>
              <p style={{ margin: 0, fontSize: 12, color: "var(--muted-foreground)" }}>현재 참여자</p>
              <p className="challenge-sidebar-value">{data.participant_count.toLocaleString()}명</p>
              <p style={{ margin: "6px 0 4px", fontSize: 12, color: "var(--muted-foreground)" }}>평균 완료율</p>
              <div className="challenge-participants-bar">
                <div className="challenge-participants-fill" style={{ width: `${data.avg_completion_rate}%` }} />
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
      </>
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
