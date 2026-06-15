import { apiRequest } from "./client";

export type ChallengeCategory = "WALK" | "WATER" | "EXERCISE" | "SLEEP" | "DIET" | "COMPREHENSIVE";
export type ChallengeDifficulty = "EASY" | "NORMAL" | "HARD";
export type BadgeType = "3_STREAK" | "7_STREAK" | "30_STREAK";
export type MyChallengeStatus = "IN_PROGRESS" | "COMPLETED" | "ABANDONED";

export const CATEGORY_LABELS: Record<ChallengeCategory, string> = {
  WALK: "걸음수",
  WATER: "수분",
  EXERCISE: "운동",
  SLEEP: "수면",
  DIET: "식단",
  COMPREHENSIVE: "종합",
};

export const DIFFICULTY_LABELS: Record<ChallengeDifficulty, string> = {
  EASY: "쉬움",
  NORMAL: "보통",
  HARD: "어려움",
};

export const CATEGORY_COLORS: Record<ChallengeCategory, string> = {
  WALK: "#4ba35f",
  WATER: "#4a82bf",
  EXERCISE: "#d0a81e",
  SLEEP: "#7c5cbf",
  DIET: "#e07050",
  COMPREHENSIVE: "#bf5c7c",
};

export type Challenge = {
  id: number;
  name: string;
  description: string;
  category: ChallengeCategory;
  difficulty: ChallengeDifficulty;
  duration_days: number;
  participant_count: number;
  avg_completion_rate: number;
  image_url?: string;
  daily_mission_example?: string;
  goal_description?: string;
  how_to_join?: string[];
  icon_emoji?: string;
  is_joined?: boolean;
};

export type MyChallenge = {
  id: number;
  challenge: Challenge;
  status: MyChallengeStatus;
  progress_percent: number;
  days_remaining?: number;
  completed_at?: string;
  today_mission?: string;
  today_completed?: boolean;
};

export type DailyMission = {
  challenge_id: number;
  challenge_name: string;
  description: string;
  completed: boolean;
};

export type Badge = {
  id: number;
  challenge_id: number;
  challenge_name: string;
  badge_type: BadgeType;
  streak_days: number;
  is_earned: boolean;
  earned_at?: string;
  current_streak?: number;
  points: number;
  icon_emoji?: string;
  progress_percent?: number;
};

export type LeaderboardEntry = {
  rank: number;
  user_id: number;
  nickname: string;
  score: number;
  completed_missions: number;
  is_me?: boolean;
};

export type ChallengeDashboard = {
  in_progress_count: number;
  weekly_completion_rate: number;
  streak_days: number;
  total_completed_missions: number;
  in_progress_challenges: MyChallenge[];
  today_missions: DailyMission[];
  completed_challenge_count: number;
  earned_badge_count: number;
  weekly_activity: boolean[];
};

export type ChallengeListQuery = {
  category?: ChallengeCategory | "ALL";
  difficulty?: ChallengeDifficulty | "ALL";
  sort?: "POPULAR" | "LATEST" | "DURATION" | "NEWEST" | "COMPLETION_RATE";
  page?: number;
};

export type ChallengeListData = {
  items: Challenge[];
  total_count: number;
  has_more: boolean;
};

export type BadgeListData = {
  earned_count: number;
  total_count: number;
  badges: Badge[];
};

export type LeaderboardData = {
  period_start: string;
  period_end: string;
  my_rank: number;
  my_score: number;
  my_completed_missions: number;
  entries: LeaderboardEntry[];
  top_three?: LeaderboardEntry[];
};

export type MyChallengeData = {
  in_progress_count: number;
  completed_count: number;
  completion_rate: number;
  streak_days: number;
  in_progress: MyChallenge[];
  completed: MyChallenge[];
  earned_badge_count: number;
};

type ApiChallengeSummary = {
  challenge_id: number;
  title: string;
  description: string;
  category: ChallengeCategory;
  target_metric: string;
  goal_value: number;
  duration_days: number;
  difficulty: ChallengeDifficulty;
  reward_points: number;
  participant_count: number;
  is_joined: boolean;
  today_checked: boolean;
};

type ApiChallengeDetail = ApiChallengeSummary & {
  average_completion_rate: number;
  how_to_join: string[];
  daily_mission_examples: string[];
  created_at: string;
  updated_at: string;
};

type ApiChallengeJoin = {
  participation_id: number;
  challenge_id: number;
  status: "JOINED" | "COMPLETED" | "CANCELED";
  start_date: string;
  end_date: string;
  progress_count: number;
  completion_rate: number;
  created_at: string;
};

type ApiMyChallenge = {
  participation_id: number;
  challenge_id: number;
  title: string;
  status: "JOINED" | "COMPLETED" | "CANCELED";
  start_date: string;
  end_date: string;
  progress_count: number;
  duration_days: number;
  completion_rate: number;
  today_checked: boolean;
};

type ApiDashboardSummary = {
  active_count: number;
  completed_count: number;
  weekly_completion_rate: number;
  current_streak_days: number;
  completed_mission_count: number;
  earned_badge_count: number;
  today_missions: Array<{
    participation_id: number;
    challenge_id: number;
    title: string;
    mission_text: string;
    today_checked: boolean;
  }>;
  weekly_activity: Array<{
    activity_date: string;
    completed_count: number;
  }>;
};

type ApiBadge = {
  badge_id: number;
  badge_name: string;
  badge_type: "STREAK_3" | "STREAK_7" | "STREAK_30";
  is_earned: boolean;
  current_streak: number;
  target_streak: number;
  progress_rate: number;
  earned_at: string | null;
};

type ApiBadgeList = {
  earned_count: number;
  total_completion_rate: number;
  items: ApiBadge[];
  recent_earned: ApiBadge[];
};

type ApiLeaderboardItem = {
  rank: number;
  user_id: number;
  nickname_masked: string;
  score: number;
  completed_mission_count: number;
};

type ApiLeaderboard = {
  week_start: string;
  week_end: string;
  top_three: ApiLeaderboardItem[];
  my_rank: {
    rank: number | null;
    score: number;
    completed_mission_count: number;
  };
  items: ApiLeaderboardItem[];
};

function targetMetricLabel(metric: string): string {
  const labels: Record<string, string> = {
    STEPS: "걸음",
    WATER: "수분",
    EXERCISE: "운동",
    SLEEP: "수면",
    DIET: "식단",
    COMPREHENSIVE: "종합",
  };
  return labels[metric] ?? "건강 습관";
}

function categoryIcon(category: ChallengeCategory): string {
  const icons: Record<ChallengeCategory, string> = {
    WALK: "🚶",
    WATER: "💧",
    EXERCISE: "🏃",
    SLEEP: "😴",
    DIET: "🥗",
    COMPREHENSIVE: "🎯",
  };
  return icons[category];
}

function mapChallenge(summary: ApiChallengeSummary | ApiChallengeDetail): Challenge {
  const detail = summary as ApiChallengeDetail;
  const missionExample = detail.daily_mission_examples?.[0];
  const completionRate =
    "average_completion_rate" in detail ? detail.average_completion_rate : summary.is_joined ? 100 : 0;

  return {
    id: summary.challenge_id,
    name: summary.title,
    description: summary.description,
    category: summary.category,
    difficulty: summary.difficulty,
    duration_days: summary.duration_days,
    participant_count: summary.participant_count,
    avg_completion_rate: completionRate,
    daily_mission_example: missionExample,
    goal_description: `${targetMetricLabel(summary.target_metric)} 목표 ${summary.goal_value}을 ${summary.duration_days}일 동안 실천합니다.`,
    how_to_join: detail.how_to_join,
    icon_emoji: categoryIcon(summary.category),
    is_joined: summary.is_joined,
  };
}

function mapStatus(status: ApiMyChallenge["status"]): MyChallengeStatus {
  if (status === "COMPLETED") return "COMPLETED";
  if (status === "CANCELED") return "ABANDONED";
  return "IN_PROGRESS";
}

function daysRemaining(endDate: string): number {
  const end = new Date(`${endDate}T23:59:59`);
  const diff = end.getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function mapMyChallenge(item: ApiMyChallenge): MyChallenge {
  return {
    id: item.participation_id,
    challenge: {
      id: item.challenge_id,
      name: item.title,
      description: "",
      category: "COMPREHENSIVE",
      difficulty: "NORMAL",
      duration_days: item.duration_days,
      participant_count: 0,
      avg_completion_rate: item.completion_rate,
      icon_emoji: "🏆",
    },
    status: mapStatus(item.status),
    progress_percent: Math.round(item.completion_rate),
    days_remaining: item.status === "JOINED" ? daysRemaining(item.end_date) : undefined,
    completed_at: item.status === "COMPLETED" ? item.end_date : undefined,
    today_mission: `${item.title} 오늘 미션 수행`,
    today_completed: item.today_checked,
  };
}

function mapJoinResponse(item: ApiChallengeJoin): MyChallenge {
  return {
    id: item.participation_id,
    challenge: {
      id: item.challenge_id,
      name: "참여한 챌린지",
      description: "",
      category: "COMPREHENSIVE",
      difficulty: "NORMAL",
      duration_days: Math.max(1, daysRemaining(item.end_date)),
      participant_count: 0,
      avg_completion_rate: item.completion_rate,
      icon_emoji: "🏆",
    },
    status: mapStatus(item.status),
    progress_percent: Math.round(item.completion_rate),
    days_remaining: daysRemaining(item.end_date),
  };
}

function mapBadgeType(type: ApiBadge["badge_type"]): BadgeType {
  if (type === "STREAK_3") return "3_STREAK";
  if (type === "STREAK_7") return "7_STREAK";
  return "30_STREAK";
}

function badgePoints(targetStreak: number): number {
  if (targetStreak >= 30) return 10;
  if (targetStreak >= 7) return 5;
  return 3;
}

function badgeIcon(targetStreak: number): string {
  if (targetStreak >= 30) return "🥇";
  if (targetStreak >= 7) return "🥈";
  return "🥉";
}

function mapBadge(item: ApiBadge): Badge {
  return {
    id: item.badge_id,
    challenge_id: item.badge_id,
    challenge_name: item.badge_name,
    badge_type: mapBadgeType(item.badge_type),
    streak_days: item.target_streak,
    is_earned: item.is_earned,
    earned_at: item.earned_at ?? undefined,
    current_streak: item.current_streak,
    points: badgePoints(item.target_streak),
    icon_emoji: badgeIcon(item.target_streak),
    progress_percent: Math.round(item.progress_rate),
  };
}

function mapLeaderboardItem(item: ApiLeaderboardItem, myUserId?: number): LeaderboardEntry {
  return {
    rank: item.rank,
    user_id: item.user_id,
    nickname: item.nickname_masked,
    score: item.score,
    completed_missions: item.completed_mission_count,
    is_me: myUserId != null && item.user_id === myUserId,
  };
}

function mapSort(sort?: ChallengeListQuery["sort"]): "LATEST" | "POPULAR" | "DURATION" | undefined {
  if (sort === "NEWEST") return "LATEST";
  if (sort === "COMPLETION_RATE") return "POPULAR";
  return sort;
}

export async function getDashboard(token?: string): Promise<{ data: ChallengeDashboard }> {
  const [summaryResponse, myResponse] = await Promise.all([
    apiRequest<{ data: ApiDashboardSummary }>("/challenges/summary", { token }),
    apiRequest<{ data: ApiMyChallenge[] }>("/challenge-participations/me", { token }),
  ]);

  const inProgress = myResponse.data.map(mapMyChallenge).filter((item) => item.status === "IN_PROGRESS");
  const weeklyActivity = summaryResponse.data.weekly_activity.map((item) => item.completed_count > 0);

  return {
    data: {
      in_progress_count: summaryResponse.data.active_count,
      weekly_completion_rate: Math.round(summaryResponse.data.weekly_completion_rate),
      streak_days: summaryResponse.data.current_streak_days,
      total_completed_missions: summaryResponse.data.completed_mission_count,
      in_progress_challenges: inProgress,
      today_missions: summaryResponse.data.today_missions.map((mission) => ({
        challenge_id: mission.challenge_id,
        challenge_name: mission.title,
        description: mission.mission_text,
        completed: mission.today_checked,
      })),
      completed_challenge_count: summaryResponse.data.completed_count,
      earned_badge_count: summaryResponse.data.earned_badge_count,
      weekly_activity: [...weeklyActivity, ...Array(7).fill(false)].slice(0, 7),
    },
  };
}

export async function getChallengeList(
  query: ChallengeListQuery,
  token?: string,
): Promise<{ data: ChallengeListData }> {
  const params = new URLSearchParams();
  if (query.category && query.category !== "ALL") params.set("category", query.category);
  const sort = mapSort(query.sort);
  if (sort) params.set("sort", sort);

  const response = await apiRequest<{ data: ApiChallengeSummary[] }>(
    `/challenges${params.toString() ? `?${params.toString()}` : ""}`,
    { token },
  );
  const items = response.data
    .map(mapChallenge)
    .filter((item) => !query.difficulty || query.difficulty === "ALL" || item.difficulty === query.difficulty);

  return { data: { items, total_count: items.length, has_more: false } };
}

export async function getChallengeDetail(
  challengeId: number,
  token?: string,
): Promise<{ data: Challenge }> {
  const response = await apiRequest<{ data: ApiChallengeDetail }>(`/challenges/${challengeId}`, { token });
  return { data: mapChallenge(response.data) };
}

export async function joinChallenge(
  challengeId: number,
  token?: string,
): Promise<{ data: MyChallenge }> {
  const response = await apiRequest<{ data: ApiChallengeJoin }>(`/challenges/${challengeId}/participations`, {
    method: "POST",
    token,
  });
  return { data: mapJoinResponse(response.data) };
}

export async function abandonChallenge(
  myChallengeId: number,
  token?: string,
): Promise<void> {
  await apiRequest<void>(`/challenge-participations/${myChallengeId}/cancellations`, {
    method: "POST",
    token,
  });
}

export async function checkInMission(
  participationId: number,
  token?: string,
): Promise<void> {
  await apiRequest<void>(`/challenge-participations/${participationId}/checkins/today`, {
    method: "POST",
    body: JSON.stringify({ note: null }),
    token,
  });
}

export async function getBadges(token?: string): Promise<{ data: BadgeListData }> {
  const response = await apiRequest<{ data: ApiBadgeList }>("/badges", { token });
  const badges = response.data.items.map(mapBadge);
  return {
    data: {
      earned_count: response.data.earned_count,
      total_count: badges.length,
      badges,
    },
  };
}

export async function getLeaderboard(token?: string): Promise<{ data: LeaderboardData }> {
  const response = await apiRequest<{ data: ApiLeaderboard }>("/challenge-leaderboards/weekly", { token });
  const myRank = response.data.my_rank;
  const entries = response.data.items.map((item) => ({
    ...mapLeaderboardItem(item),
    is_me: myRank.rank != null && item.rank === myRank.rank,
  }));
  const topThree = response.data.top_three.map((item) => ({
    ...mapLeaderboardItem(item),
    is_me: myRank.rank != null && item.rank === myRank.rank,
  }));

  return {
    data: {
      period_start: response.data.week_start,
      period_end: response.data.week_end,
      my_rank: myRank.rank ?? 0,
      my_score: myRank.score,
      my_completed_missions: myRank.completed_mission_count,
      entries,
      top_three: topThree,
    },
  };
}

export async function getMyChallenges(token?: string): Promise<{ data: MyChallengeData }> {
  const response = await apiRequest<{ data: ApiMyChallenge[] }>("/challenge-participations/me", { token });
  const items = response.data.map(mapMyChallenge);
  const inProgress = items.filter((item) => item.status === "IN_PROGRESS");
  const completed = items.filter((item) => item.status === "COMPLETED");
  const completionRate = items.length > 0
    ? Math.round(items.reduce((sum, item) => sum + item.progress_percent, 0) / items.length)
    : 0;

  return {
    data: {
      in_progress_count: inProgress.length,
      completed_count: completed.length,
      completion_rate: completionRate,
      streak_days: 0,
      in_progress: inProgress,
      completed,
      earned_badge_count: 0,
    },
  };
}
