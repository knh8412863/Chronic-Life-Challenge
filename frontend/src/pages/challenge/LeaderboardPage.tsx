import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getLeaderboard, type LeaderboardData } from "../../api/challenges";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const FALLBACK: LeaderboardData = {
  period_start: "2026-05-20",
  period_end: "2026-05-26",
  my_rank: 15,
  my_score: 1840,
  my_completed_missions: 24,
  entries: [
    { rank: 4, user_id: 4, nickname: "사용자***", score: 2180, completed_missions: 95, is_me: false },
    { rank: 5, user_id: 5, nickname: "사용자***", score: 2050, completed_missions: 88, is_me: false },
    { rank: 6, user_id: 6, nickname: "사용자***", score: 1920, completed_missions: 82, is_me: false },
    { rank: 7, user_id: 7, nickname: "사용자***", score: 1850, completed_missions: 76, is_me: false },
    { rank: 8, user_id: 8, nickname: "사용자***", score: 1780, completed_missions: 71, is_me: false },
    { rank: 9, user_id: 9, nickname: "사용자***", score: 1720, completed_missions: 68, is_me: false },
    { rank: 10, user_id: 10, nickname: "사용자***", score: 1650, completed_missions: 64, is_me: false },
  ],
  top_three: [
    { rank: 1, user_id: 1, nickname: "사용자***", score: 2850, completed_missions: 128 },
    { rank: 2, user_id: 2, nickname: "사용자***", score: 2640, completed_missions: 115 },
    { rank: 3, user_id: 3, nickname: "사용자***", score: 2420, completed_missions: 102 },
  ],
};

const MEDALS = ["🥇", "🥈", "🥉"];

type Props = { onNavigate?: (route: AppRoute) => void };

export function LeaderboardPage({ onNavigate }: Props) {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;
    setIsLoading(true);
    getLeaderboard(token)
      .then((res) => { setData(res.data); setHasError(false); })
      .catch(() => setHasError(true))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState message="리더보드를 불러오는 중입니다." />;

  const d = data ?? FALLBACK;
  const topThree = d.top_three ?? [];

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지 관리</p>
          <h1>리더보드</h1>
        </div>
      </section>

      {hasError && <ErrorState title="리더보드를 불러오지 못했습니다." description="예시 데이터로 표시됩니다." />}

      <p className="leaderboard-period">
        {d.period_start} ~ {d.period_end} 주간 기준
      </p>

      {/* Top 3 */}
      <div className="leaderboard-top3">
        {topThree.map((entry, i) => (
          <div key={i} className="leaderboard-top-card">
            <div className="leaderboard-avatar">
              <span>👤</span>
              <span className="leaderboard-medal">{MEDALS[i]}</span>
            </div>
            <p className="leaderboard-nickname">{entry.nickname}</p>
            <p className="leaderboard-rank-label">#{entry.rank}</p>
            <p className="leaderboard-score">
              {entry.score.toLocaleString()}
              <span className="leaderboard-score-unit"> 점</span>
            </p>
            <p className="leaderboard-completed">완료 미션 {entry.completed_missions}개</p>
          </div>
        ))}
      </div>

      {/* 내 순위 */}
      <div className="leaderboard-my-rank">
        <span>내 순위:</span>
        <span className="rank-highlight">#{d.my_rank}</span>
        <span>{d.my_score.toLocaleString()}점</span>
        <span style={{ color: "var(--muted-foreground)" }}>완료 미션 {d.my_completed_missions}개</span>
      </div>

      {/* 순위 테이블 */}
      <section className="dashboard-card">
        <div className="table-card" style={{ border: "none", borderRadius: 0 }}>
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>프로필</th>
                <th>닉네임</th>
                <th>점수</th>
                <th>완료 미션</th>
              </tr>
            </thead>
            <tbody>
              {d.entries.map((entry) => (
                <tr key={entry.rank} style={{ background: entry.is_me ? "var(--soft-green)" : "transparent" }}>
                  <td style={{ fontWeight: 700 }}>#{entry.rank}</td>
                  <td>
                    <div className="leaderboard-table-avatar">👤</div>
                  </td>
                  <td style={{ fontWeight: entry.is_me ? 700 : 400 }}>
                    {entry.nickname}
                    {entry.is_me && <span style={{ marginLeft: 6, fontSize: 12, color: "var(--brand-green)" }}>(나)</span>}
                  </td>
                  <td style={{ fontWeight: 600 }}>{entry.score.toLocaleString()}</td>
                  <td>{entry.completed_missions}개</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
