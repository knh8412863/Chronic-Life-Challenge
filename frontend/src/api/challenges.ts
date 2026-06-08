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
  sort?: "POPULAR" | "NEWEST" | "COMPLETION_RATE";
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

export async function getDashboard(token?: string): Promise<{ data: ChallengeDashboard }> {
  const data = await apiRequest<ChallengeDashboard>("/challenges/dashboard", { token });
  return { data };
}

export async function getChallengeList(
  query: ChallengeListQuery,
  token?: string,
): Promise<{ data: ChallengeListData }> {
  const params = new URLSearchParams();
  if (query.category && query.category !== "ALL") params.set("category", query.category);
  if (query.difficulty && query.difficulty !== "ALL") params.set("difficulty", query.difficulty);
  if (query.sort) params.set("sort", query.sort);
  if (query.page) params.set("page", String(query.page));
  const data = await apiRequest<ChallengeListData>(`/challenges?${params.toString()}`, { token });
  return { data };
}

export async function getChallengeDetail(
  challengeId: number,
  token?: string,
): Promise<{ data: Challenge }> {
  const data = await apiRequest<Challenge>(`/challenges/${challengeId}`, { token });
  return { data };
}

export async function joinChallenge(
  challengeId: number,
  token?: string,
): Promise<{ data: MyChallenge }> {
  const data = await apiRequest<MyChallenge>(`/challenges/${challengeId}/join`, {
    method: "POST",
    token,
  });
  return { data };
}

export async function abandonChallenge(
  myChallengeId: number,
  token?: string,
): Promise<void> {
  await apiRequest<void>(`/challenges/my/${myChallengeId}/abandon`, {
    method: "POST",
    token,
  });
}

export async function checkInMission(
  challengeId: number,
  token?: string,
): Promise<void> {
  await apiRequest<void>(`/challenges/${challengeId}/checkin`, {
    method: "POST",
    token,
  });
}

export async function getBadges(token?: string): Promise<{ data: BadgeListData }> {
  const data = await apiRequest<BadgeListData>("/challenges/badges", { token });
  return { data };
}

export async function getLeaderboard(token?: string): Promise<{ data: LeaderboardData }> {
  const data = await apiRequest<LeaderboardData>("/challenges/leaderboard", { token });
  return { data };
}

export async function getMyChallenges(token?: string): Promise<{ data: MyChallengeData }> {
  const data = await apiRequest<MyChallengeData>("/challenges/my", { token });
  return { data };
}
