import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import { getLeaderboard, type LeaderboardData } from "../../api/challenges";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

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

  const topThree = data?.top_three ?? [];
  const hasEntries = data !== null && data.entries.length > 0;

  return (
    <div className="challenge-page">
      <section className="section-header-row page-heading-row">
        <div className="page-heading">
          <p className="eyebrow">챌린지</p>
          <h1>리더보드</h1>
        </div>
      </section>

      {hasError && <ErrorState title="리더보드를 불러오지 못했습니다." description="잠시 후 다시 시도해 주세요." />}

      {data && (
        <p className="leaderboard-period">
          {data.period_start} ~ {data.period_end} 주간 기준
        </p>
      )}

      {!data && !hasError && (
        <EmptyState
          title="리더보드 데이터가 없습니다."
          description="챌린지에 참여하고 미션을 완료하면 주간 순위가 표시됩니다."
          icon="🏆"
        />
      )}

      {/* Top 3 */}
      {topThree.length > 0 && (
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
      )}

      {/* 내 순위 */}
      {data && (
        <div className="leaderboard-my-rank">
          <span>내 순위:</span>
          <span className="rank-highlight">{data.my_rank > 0 ? `#${data.my_rank}` : "순위 없음"}</span>
          <span>{data.my_score.toLocaleString()}점</span>
          <span style={{ color: "var(--muted-foreground)" }}>완료 미션 {data.my_completed_missions}개</span>
        </div>
      )}

      {/* 순위 테이블 */}
      <section className="dashboard-card">
        {hasEntries && data ? (
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
              {data.entries.map((entry) => (
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
        ) : (
          <EmptyState
            title="아직 순위가 없습니다."
            description="같은 챌린지에 참여한 사용자가 이번 주 미션을 완료하면 순위가 표시됩니다."
            icon="🏆"
          />
        )}
      </section>
    </div>
  );
}
