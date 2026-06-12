import { useEffect, useMemo, useState } from "react";

import { AppLayout } from "./layouts/AppLayout";
import { AdviceHistoryPage } from "./pages/1.home/AdviceHistoryPage";
import { AdviceFeedbackPage } from "./pages/1.home/AdviceFeedbackPage";
import { AdviceTodayPage } from "./pages/1.home/AdviceTodayPage";
import { TermsAgreementPage, EmailVerifyPage, PasswordResetPage, OnboardingCompletePage } from "./pages/0.auth/AuthOnboardingPages";
import { BadgePage } from "./pages/5.challenge/BadgePage";
import { ChallengeDashboardPage } from "./pages/5.challenge/ChallengeDashboardPage";
import { ChallengeDetailPage } from "./pages/5.challenge/ChallengeDetailPage";
import { ChallengeListPage } from "./pages/5.challenge/ChallengeListPage";
import { LeaderboardPage } from "./pages/5.challenge/LeaderboardPage";
import { MyChallengesPage } from "./pages/5.challenge/MyChallengesPage";
import { PublicLayout } from "./layouts/PublicLayout";
import { FoodPage } from "./pages/3.food/FoodPage";
import { HomePage } from "./pages/1.home/HomePage";
import { ActivityPage } from "./pages/2.health/ActivityPage";
import { ExercisePage } from "./pages/2.health/ExercisePage";
import { GoalEditPage } from "./pages/2.health/GoalEditPage";
import { GoalPage } from "./pages/2.health/GoalPage";
import { HealthProfilePage } from "./pages/2.health/HealthProfilePage";
import { VitalsDetailPage } from "./pages/2.health/VitalsDetailPage";
import { VitalsInputPage } from "./pages/2.health/VitalsInputPage";
import { VitalsListPage } from "./pages/2.health/VitalsListPage";
import { HealthSurveyPage } from "./pages/0.auth/HealthSurveyPage";
import { LandingPage } from "./pages/0.auth/LandingPage";
import { LoginPage } from "./pages/0.auth/LoginPage";
import { NotificationsPage } from "./pages/1.home/NotificationsPage";
import { PetEncyclopediaPage } from "./pages/6.pet/PetEncyclopediaPage";
import { PetPage } from "./pages/6.pet/PetPage";
import { PetSelectPage } from "./pages/6.pet/PetSelectPage";
import { PredictionFeedbackPage } from "./pages/1.home/PredictionFeedbackPage";
import { PredictionHistoryPage } from "./pages/1.home/PredictionHistoryPage";
import { PredictionProgressPage } from "./pages/1.home/PredictionProgressPage";
import { PredictionRequestPage } from "./pages/1.home/PredictionRequestPage";
import { PredictionResultPage } from "./pages/1.home/PredictionResultPage";
import ReportDetailPage from "./pages/4.report/ReportDetailPage";
import ReportExportPage from "./pages/4.report/ReportExportPage";
import ReportListPage from "./pages/4.report/ReportListPage";
import { SignUpPage } from "./pages/0.auth/SignUpPage";

// ── front/mypage-management 브랜치에서 추가
import { MyInfoPage } from "./pages/7.mypage/MyInfoPage";
import { EditProfilePage } from "./pages/7.mypage/EditProfilePage";
import { MyPagePasswordVerifyPage } from "./pages/7.mypage/MyPagePasswordVerifyPage";
import { ChangePasswordPage, NotificationSettingsPage, TermsManagementPage, WithdrawalPage } from "./pages/7.mypage/MyPageSubPages";

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
  | "/advices/feedback"
  | "/prediction/request"
  | "/prediction/progress"
  | "/prediction/result"
  | "/prediction/history"
  | "/prediction/feedback"
  | "/mypage/verify"
  | "/mypage"
  | "/mypage/profile"
  | "/mypage/edit"
  | "/mypage/change-password"
  | "/mypage/notifications"
  | "/mypage/terms"
  | "/mypage/withdrawal"
  | "/health"
  | "/health/goal"
  | "/health/goal/edit"
  | "/health/profile"
  | "/health/vitals"
  | "/health/vitals/input"
  | "/health/vitals/detail"
  | "/health/exercise"
  | "/health/activity"
  | "/food"
  | "/food/analyze"
  | "/reports"
  | "/reports/detail"
  | "/reports/export"
  | "/challenges"
  | "/challenges/list"
  | "/challenges/detail"
  | "/challenges/my"
  | "/challenges/leaderboard"
  | "/challenges/badges"
  | "/pet"
  | "/pet/select"
  | "/pet/encyclopedia";

const publicRoutes = new Set<AppRoute>(["/"]);

const standaloneRoutes = new Set<AppRoute>([
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
    "/advices/feedback",
    "/prediction/request",
    "/prediction/progress",
    "/prediction/result",
    "/prediction/history",
    "/prediction/feedback",
    "/mypage/verify",
    "/mypage",
    "/mypage/profile",
    "/mypage/edit",
    "/mypage/change-password",
    "/mypage/notifications",
    "/mypage/terms",
    "/mypage/withdrawal",
    "/health",
    "/health/goal",
    "/health/goal/edit",
    "/health/profile",
    "/health/vitals",
    "/health/vitals/input",
    "/health/vitals/detail",
    "/health/exercise",
    "/health/activity",
    "/food",
    "/food/analyze",
    "/reports",
    "/reports/detail",
    "/reports/export",
    "/challenges",
    "/challenges/list",
    "/challenges/detail",
    "/challenges/my",
    "/challenges/leaderboard",
    "/challenges/badges",
    "/pet",
    "/pet/select",
    "/pet/encyclopedia",
  ];

  return knownRoutes.includes(pathname as AppRoute) ? (pathname as AppRoute) : "/home";
}

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => normalizePath(window.location.pathname));
  const [verifiedMypageRoute, setVerifiedMypageRoute] = useState<AppRoute | null>(null);

  useEffect(() => {
    const onPopState = () => setRoute(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!route.startsWith("/mypage")) {
      setVerifiedMypageRoute(null);
    }
  }, [route]);

  const navigate = (nextRoute: AppRoute) => {
    const nextUrl =
      window.location.pathname === nextRoute && window.location.search
        ? `${nextRoute}${window.location.search}`
        : nextRoute;
    window.history.pushState({}, "", nextUrl);
    setRoute(nextRoute);
  };

  const page = useMemo(() => {
    const isMypageProtectedRoute = route.startsWith("/mypage") && route !== "/mypage/verify";
    if (isMypageProtectedRoute && verifiedMypageRoute !== route) {
      return (
        <MyPagePasswordVerifyPage
          onNavigate={navigate}
          onVerified={() => setVerifiedMypageRoute(route)}
          targetRoute={route}
        />
      );
    }

    switch (route) {
      case "/":
        return <LandingPage onNavigate={navigate} />;
      case "/login":
        return <LoginPage onLogin={() => navigate("/home")} onNavigate={navigate} />;
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
      case "/home":
        return <HomePage onNavigate={navigate} />;
      case "/notifications":
        return <NotificationsPage onNavigate={navigate} />;
      case "/advices/today":
        return <AdviceTodayPage onNavigate={navigate} />;
      case "/advices/history":
        return <AdviceHistoryPage onNavigate={navigate} />;
      case "/advices/feedback":
        return <AdviceFeedbackPage onNavigate={navigate} />;
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
      case "/mypage/verify":
        return (
          <MyPagePasswordVerifyPage
            onNavigate={navigate}
            onVerified={() => setVerifiedMypageRoute("/mypage/profile")}
            targetRoute="/mypage/profile"
          />
        );
      case "/mypage":
      case "/mypage/profile":
        return <MyInfoPage onNavigate={navigate} />;
      case "/mypage/edit":
        return <EditProfilePage onNavigate={navigate} />;
      case "/mypage/change-password":
        return <ChangePasswordPage onNavigate={navigate} />;
      case "/mypage/notifications":
        return <NotificationSettingsPage onNavigate={navigate} />;
      case "/mypage/terms":
        return <TermsManagementPage onNavigate={navigate} />;
      case "/mypage/withdrawal":
        return <WithdrawalPage onNavigate={navigate} />;
      case "/health":
        return <HealthProfilePage onNavigate={navigate} />;
      case "/health/goal":
        return <GoalPage onNavigate={navigate} />;
      case "/health/goal/edit":
        return <GoalEditPage onNavigate={navigate} />;
      case "/health/profile":
        return <HealthProfilePage onNavigate={navigate} />;
      case "/health/vitals":
        return <VitalsListPage onNavigate={navigate} />;
      case "/health/vitals/input":
        return <VitalsInputPage onNavigate={navigate} />;
      case "/health/vitals/detail":
        return <VitalsDetailPage onNavigate={navigate} />;
      case "/health/exercise":
        return <ExercisePage onNavigate={navigate} />;
      case "/health/activity":
        return <ActivityPage onNavigate={navigate} />;
      case "/food":
        return <FoodPage onNavigate={navigate} />;
      case "/food/analyze":
        return <FoodPage onNavigate={navigate} view="input" />;
      case "/reports":
        return <ReportListPage onNavigate={navigate} />;
      case "/reports/detail":
        return <ReportDetailPage onNavigate={navigate} />;
      case "/reports/export":
        return <ReportExportPage onNavigate={navigate} />;
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
        return <PetPage onNavigate={navigate} />;
      case "/pet/select":
        return <PetSelectPage onNavigate={navigate} />;
      case "/pet/encyclopedia":
        return <PetEncyclopediaPage onNavigate={navigate} />;
      default:
        return <HomePage onNavigate={navigate} />;
    }
  }, [route, verifiedMypageRoute]);

  if (publicRoutes.has(route)) {
    return <PublicLayout onNavigate={navigate}>{page}</PublicLayout>;
  }

  if (standaloneRoutes.has(route)) {
    return page;
  }

  return (
    <AppLayout currentRoute={route} onNavigate={navigate}>
      {page}
    </AppLayout>
  );
}
