import { useEffect, useMemo, useState } from "react";

import { AppLayout } from "./layouts/AppLayout";
import { AdviceHistoryPage } from "./pages/AdviceHistoryPage";
import { AdviceTodayPage } from "./pages/AdviceTodayPage";
import { PublicLayout } from "./layouts/PublicLayout";
import { HomePage } from "./pages/HomePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { MyProfilePage } from "./pages/MyProfilePage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { PredictionFeedbackPage } from "./pages/PredictionFeedbackPage";
import { PredictionHistoryPage } from "./pages/PredictionHistoryPage";
import { PredictionProgressPage } from "./pages/PredictionProgressPage";
import { PredictionRequestPage } from "./pages/PredictionRequestPage";
import { PredictionResultPage } from "./pages/PredictionResultPage";
import { ActivityPage } from "./pages/health/ActivityPage";
import { ExercisePage } from "./pages/health/ExercisePage";
import { GoalEditPage } from "./pages/health/GoalEditPage";
import { GoalPage } from "./pages/health/GoalPage";
import { HealthHubPage } from "./pages/health/HealthHubPage";
import { HealthProfilePage } from "./pages/health/HealthProfilePage";
import { VitalsDetailPage } from "./pages/health/VitalsDetailPage";
import { VitalsInputPage } from "./pages/health/VitalsInputPage";
import { VitalsListPage } from "./pages/health/VitalsListPage";
import { BadgePage } from "./pages/challenge/BadgePage";
import { ChallengeDashboardPage } from "./pages/challenge/ChallengeDashboardPage";
import { ChallengeDetailPage } from "./pages/challenge/ChallengeDetailPage";
import { ChallengeListPage } from "./pages/challenge/ChallengeListPage";
import { LeaderboardPage } from "./pages/challenge/LeaderboardPage";
import { MyChallengesPage } from "./pages/challenge/MyChallengesPage";

// ── front/auth-onboarding 브랜치에서 추가
import { SignUpPage } from "./pages/SignUpPage";
import { TermsAgreementPage, EmailVerifyPage, PasswordResetPage, OnboardingCompletePage } from "./pages/AuthOnboardingPages";
import { HealthSurveyPage } from "./pages/HealthSurveyPage";

export type AppRoute =
  | "/"
  | "/login"
  | "/signup"
  | "/terms"
  | "/email-verify"
  | "/password-reset"
  | "/health-survey"
  | "/onboarding-complete"
  | "/home"
  | "/notifications"
  | "/advices/today"
  | "/advices/history"
  | "/prediction/request"
  | "/prediction/progress"
  | "/prediction/result"
  | "/prediction/history"
  | "/prediction/feedback"
  | "/mypage"
  | "/mypage/profile"
  | "/health"
  | "/health/goal"
  | "/health/goal/edit"
  | "/health/profile"
  | "/health/vitals"
  | "/health/vitals/detail"
  | "/health/vitals/input"
  | "/health/exercise"
  | "/health/activity"
  | "/food"
  | "/reports"
  | "/challenges"
  | "/challenges/list"
  | "/challenges/detail"
  | "/challenges/my"
  | "/challenges/leaderboard"
  | "/challenges/badges"
  | "/pet";

const publicRoutes = new Set<AppRoute>([
  "/",
  "/login",
  "/signup",
  "/terms",
  "/email-verify",
  "/password-reset",
]);

const onboardingRoutes = new Set<AppRoute>(["/health-survey", "/onboarding-complete"]);
const serviceIntroRoutes = new Set<AppRoute>(["/"]);
const authRoutes = new Set<AppRoute>([
  "/login",
  "/signup",
  "/terms",
  "/email-verify",
  "/password-reset",
  "/health-survey",
  "/onboarding-complete",
]);

function normalizePath(pathname: string): AppRoute {
  const knownRoutes: AppRoute[] = [
    "/",
    "/login",
    "/signup",
    "/terms",
    "/email-verify",
    "/password-reset",
    "/health-survey",
    "/onboarding-complete",
    "/home",
    "/notifications",
    "/advices/today",
    "/advices/history",
    "/prediction/request",
    "/prediction/progress",
    "/prediction/result",
    "/prediction/history",
    "/prediction/feedback",
    "/mypage",
    "/mypage/profile",
    "/health",
    "/health/goal",
    "/health/goal/edit",
    "/health/profile",
    "/health/vitals",
    "/health/vitals/detail",
    "/health/vitals/input",
    "/health/exercise",
    "/health/activity",
    "/food",
    "/reports",
    "/challenges",
    "/challenges/list",
    "/challenges/detail",
    "/challenges/my",
    "/challenges/leaderboard",
    "/challenges/badges",
    "/pet",
  ];

  return knownRoutes.includes(pathname as AppRoute) ? (pathname as AppRoute) : "/home";
}

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => normalizePath(window.location.pathname));

  // TODO: API 연결 시 sessionStorage 토큰 체크로 교체 (REQ-AUTH-002, NFR-SEC-001)
  // const [isLoggedIn, setIsLoggedIn] = useState(() => !!sessionStorage.getItem("access_token"));
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const onPopState = () => setRoute(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = (nextRoute: AppRoute) => {
    window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
  };

  const effectiveRoute = useMemo(() => {
    if (!isLoggedIn && !publicRoutes.has(route) && !onboardingRoutes.has(route)) {
      return "/login" as AppRoute;
    }
    return route;
  }, [route, isLoggedIn]);

  const page = useMemo(() => {
    switch (effectiveRoute) {
      // ── 기존 라우트 유지 ──
      case "/":
        return <LandingPage onNavigate={navigate} />;
      case "/login":
        return <LoginPage onLogin={() => { setIsLoggedIn(true); navigate("/home"); }} onNavigate={navigate} />;
      case "/home":
        return <HomePage onNavigate={navigate} />;
      case "/notifications":
        return <NotificationsPage onNavigate={navigate} />;
      case "/advices/today":
        return <AdviceTodayPage onNavigate={navigate} />;
      case "/advices/history":
        return <AdviceHistoryPage />;
      case "/prediction/request":
        return <PredictionRequestPage onNavigate={navigate} />;
      case "/prediction/progress":
        return <PredictionProgressPage onNavigate={navigate} />;
      case "/prediction/result":
        return <PredictionResultPage onNavigate={navigate} />;
      case "/prediction/history":
        return <PredictionHistoryPage onNavigate={navigate} />;
      case "/prediction/feedback":
        return <PredictionFeedbackPage onNavigate={navigate} />;
      case "/mypage":
      case "/mypage/profile":
        return <MyProfilePage />;
      case "/health":
        return <HealthHubPage onNavigate={navigate} />;
      case "/health/goal":
        return <GoalPage onNavigate={navigate} />;
      case "/health/goal/edit":
        return <GoalEditPage onNavigate={navigate} />;
      case "/health/profile":
        return <HealthProfilePage onNavigate={navigate} />;
      case "/health/vitals":
        return <VitalsListPage onNavigate={navigate} />;
      case "/health/vitals/detail":
        return <VitalsDetailPage onNavigate={navigate} />;
      case "/health/vitals/input":
        return <VitalsInputPage onNavigate={navigate} />;
      case "/health/exercise":
        return <ExercisePage onNavigate={navigate} />;
      case "/health/activity":
        return <ActivityPage onNavigate={navigate} />;
      case "/food":
        return <PlaceholderPage title="식단 관리" description="식단 입력, 분석 결과, 기록 목록 화면을 연결할 영역입니다." />;
      case "/reports":
        return <PlaceholderPage title="리포트" description="주간 리포트 목록과 상세 화면을 연결할 영역입니다." />;
      case "/challenges":
        return <ChallengeDashboardPage onNavigate={navigate} />;
      case "/challenges/list":
        return <ChallengeListPage onNavigate={navigate} />;
      case "/challenges/detail":
        return <ChallengeDetailPage onNavigate={navigate} />;
      case "/challenges/my":
        return <MyChallengesPage onNavigate={navigate} />;
      case "/challenges/leaderboard":
        return <LeaderboardPage onNavigate={navigate} />;
      case "/challenges/badges":
        return <BadgePage onNavigate={navigate} />;
      case "/pet":
        return <PlaceholderPage title="마이펫" description="펫 현황, 보상 과제, 도감 화면을 연결할 영역입니다." />;

      // ── front/auth-onboarding 브랜치에서 추가 ──
      case "/signup":
        return <SignUpPage onNavigate={navigate} />;
      case "/terms":
        return <TermsAgreementPage onNavigate={navigate} />;
      case "/email-verify":
        return <EmailVerifyPage onNavigate={navigate} />;
      case "/password-reset":
        return <PasswordResetPage onNavigate={navigate} />;
      case "/health-survey":
        return <HealthSurveyPage onNavigate={navigate} />;
      case "/onboarding-complete":
        return <OnboardingCompletePage onNavigate={navigate} />;

      default:
        return <HomePage />;
    }
  }, [effectiveRoute]);

  if (serviceIntroRoutes.has(effectiveRoute)) {
    return <PublicLayout onNavigate={navigate}>{page}</PublicLayout>;
  }

  if (authRoutes.has(effectiveRoute)) {
    return page;
  }

  return (
    <AppLayout currentRoute={effectiveRoute} onNavigate={navigate}>
      {page}
    </AppLayout>
  );
}
