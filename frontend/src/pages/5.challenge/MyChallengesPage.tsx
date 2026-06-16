import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getMyChallenges,
  abandonChallenge,
  CATEGORY_LABELS,
  type MyChallenge,
  type MyChallengeData,
} from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK: MyChallengeData = {
  in_progress_count: 3,
  completed_count: 8,
  completion_rate: 78,
  streak_days: 12,
  earned_badge_count: 12,
  in_progress: [
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
  completed: [
    { id: 10, challenge: { id: 10, name: "7일 물 마시기", description: "", category: "WATER", difficulty: "EASY", duration_days: 7, participant_count: 500, avg_completion_rate: 90 }, status: "COMPLETED", progress_percent: 100, completed_at: "2026-05-01" },
    { id: 11, challenge: { id: 11, name: "21일 금연", description: "", category: "COMPREHENSIVE", difficulty: "HARD", duration_days: 21, participant_count: 300, avg_completion_rate: 60 }, status: "COMPLETED", progress_percent: 100, completed_at: "2026-04-20" },
    { id: 12, challenge: { id: 12, name: "14일 수면 개선", description: "", category: "SLEEP", difficulty: "NORMAL", duration_days: 14, participant_count: 450, avg_completion_rate: 75 }, status: "COMPLETED", progress_percent: 100, completed_at: "2026-04-10" },
  ],
};

function catClass(cat: string) {
  return { WALK: "walk", WATER: "water", EXERCISE: "exercise", SLEEP: "sleep", DIET: "diet", COMPREHENSIVE: "comprehensive" }[cat] ?? "walk";
}

type Props = { onNavigate?: (route: AppRoute) => void };

export function MyChallengesPage({ onNavigate }: Props) {
  const [data, setData] = useState<MyChallengeData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [abandonTarget, setAbandonTarget] = useState<MyChallenge | null>(null);
  const [abandonMessage, setAbandonMessage] = useState("");
  const [isAbandoning, setIsAbandoning] = useState(false);

  function fetchData() {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getMyChallenges(token)
      .then((res) => { setData(res.data); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }

  useEffect(() => { fetchData(); }, []);

  function handleAbandon(mc: MyChallenge) {
    setAbandonMessage("");
    setAbandonTarget(mc);
  }

  async function confirmAbandon() {
    if (!abandonTarget) return;
    const token = getStoredAccessToken();
    setIsAbandoning(true);
    setAbandonMessage("");
    try {
      if (token) await abandonChallenge(abandonTarget.id, token);
      setAbandonTarget(null);
      fetchData();
    } catch {
      setAbandonMessage("챌린지 포기에 실패했습니다.\n잠시 후 다시 시도해주세요.");
    } finally {
      setIsAbandoning(false);
    }
  }

  function handleDetail(challengeId: number) {
    sessionStorage.setItem("selectedChallengeId", String(challengeId));
    onNavigate?.("/challenges/detail");
  }

  if (isLoading) return <LoadingState message="내 챌린지 정보를 불러오는 중입니다." />;

  const d = data ?? FALLBACK;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지</p>
          <h1>내 챌린지 현황</h1>
        </div>
        <button type="button" className="green-button" onClick={() => onNavigate?.("/challenges/list")}>
          + 챌린지 참여하기
        </button>
      </section>

      {hasError && <ErrorState title="데이터를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />}

      {/* 통계 4개 */}
      <div className="challenge-stat-grid">
        <div className="challenge-stat-card">
          <span className="stat-label">진행 중</span>
          <strong className="stat-value">{d.in_progress_count}<span className="stat-unit">개</span></strong>
        </div>
        <div className="challenge-stat-card">
          <span className="stat-label">완료</span>
          <strong className="stat-value">{d.completed_count}<span className="stat-unit">개</span></strong>
        </div>
        <div className="challenge-stat-card yellow">
          <span className="stat-label">달성률</span>
          <strong className="stat-value">{d.completion_rate}<span className="stat-unit">%</span></strong>
        </div>
        <div className="challenge-stat-card">
          <span className="stat-label">연속 일수</span>
          <strong className="stat-value">{d.streak_days}<span className="stat-unit">일</span></strong>
        </div>
      </div>

      {/* 참여 중 챌린지 */}
      <section className="dashboard-card">
        <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>참여 중 챌린지</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {d.in_progress.map((mc, idx) => (
            <div key={mc.id}>
              {idx > 0 && <div className="my-challenge-divider" />}
              <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
                {/* 헤더 */}
                <div className="my-challenge-header">
                  <span style={{ fontSize: 20 }}>{mc.challenge.icon_emoji ?? "🏆"}</span>
                  <span className="my-challenge-name">{mc.challenge.name}</span>
                  <span className={`challenge-tag status-in-progress`}>진행 중</span>
                </div>

                {/* 바디 */}
                <div className="my-challenge-body">
                  <div className="my-challenge-progress-col">
                    <div className="my-challenge-progress-label">
                      <span>진행률</span>
                      <span>{mc.progress_percent}%</span>
                    </div>
                    <div className="challenge-progress-bar">
                      <div className="challenge-progress-fill" style={{ width: `${mc.progress_percent}%` }} />
                    </div>
                    {mc.days_remaining != null && (
                      <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>남은 기간: {mc.days_remaining}일</span>
                    )}
                  </div>

                  <div className="my-challenge-mission-col">
                    <div className={`challenge-mission-check ${mc.today_completed ? "done" : ""}`} style={{ width: 20, height: 20 }}>
                      {mc.today_completed && <span style={{ fontSize: 11 }}>✓</span>}
                    </div>
                    <span style={{ color: mc.today_completed ? "var(--muted-foreground)" : "inherit" }}>
                      오늘의 미션: {mc.today_mission}
                    </span>
                  </div>

                  <div className="my-challenge-action-col">
                    <button type="button" className="my-challenge-detail-btn" onClick={() => handleDetail(mc.challenge.id)}>상세보기</button>
                    <button type="button" className="my-challenge-abandon-btn" onClick={() => handleAbandon(mc)}>포기하기</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 하단 2열 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 20 }}>
        {/* 완료한 챌린지 */}
        <section className="dashboard-card">
          <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>완료한 챌린지</h2>
          <div style={{ padding: "0 20px 16px" }}>
            {d.completed.map((mc) => (
              <div key={mc.id} className="completed-challenge-item">
                <div className="completed-check-icon">✓</div>
                <div style={{ flex: 1 }}>
                  <p className="completed-challenge-name">{mc.challenge.name}</p>
                  {mc.completed_at && (
                    <p style={{ margin: 0, fontSize: 12, color: "var(--muted-foreground)" }}>
                      완료일: {mc.completed_at}
                    </p>
                  )}
                </div>
                <button type="button" className="my-challenge-detail-link" onClick={() => handleDetail(mc.challenge.id)}>
                  상세보기 →
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* 나의 성과 요약 */}
        <section className="dashboard-card">
          <h2 style={{ padding: "20px 20px 12px", margin: 0, fontSize: "15px", fontWeight: 700 }}>나의 성과 요약</h2>
          <div style={{ padding: "0 20px 16px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
              <div className="achievement-card">
                <p className="ach-label">완료한 챌린지</p>
                <strong className="ach-value">{d.completed_count}<span className="ach-unit">개</span></strong>
              </div>
              <div className="achievement-card">
                <p className="ach-label">연속 성공 일수</p>
                <strong className="ach-value">{d.streak_days}<span className="ach-unit">일</span></strong>
              </div>
              <div className="achievement-card">
                <p className="ach-label">획득 뱃지</p>
                <strong className="ach-value">{d.earned_badge_count}<span className="ach-unit">개</span></strong>
              </div>
            </div>
            <div className="streak-record-box">
              <span style={{ fontSize: 20 }}>🔥</span>
              <div>
                <p className="streak-text" style={{ margin: 0 }}>연속 성공 기록</p>
                <p className="streak-sub" style={{ margin: 0 }}>{d.streak_days}일 연속 미션 완료 중!</p>
                <p className="streak-sub" style={{ margin: 0 }}>목표: 30일 연속 성공</p>
              </div>
            </div>
          </div>
        </section>
      </div>
      {abandonTarget && (
        <div className="app-modal-backdrop" role="dialog" aria-modal="true">
          <div className="app-modal-card">
            <h2>챌린지 포기</h2>
            <p>
              {abandonTarget.challenge.name}
              <br />
              챌린지를 포기하시겠습니까?
            </p>
            {abandonMessage && (
              <p className="modal-error-text">
                {abandonMessage.split("\n").map((line) => (
                  <span key={line}>
                    {line}
                    <br />
                  </span>
                ))}
              </p>
            )}
            <div className="button-row modal-button-row">
              <button
                type="button"
                className="small-button"
                onClick={() => setAbandonTarget(null)}
                disabled={isAbandoning}
              >
                취소
              </button>
              <button
                type="button"
                className="my-challenge-abandon-btn"
                onClick={confirmAbandon}
                disabled={isAbandoning}
              >
                {isAbandoning ? "처리 중..." : "포기하기"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
