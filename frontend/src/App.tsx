import { useEffect, useMemo, useState } from "react";

import { AppLayout } from "./layouts/AppLayout";
import { AdviceHistoryPage } from "./pages/AdviceHistoryPage";
import { AdviceTodayPage } from "./pages/AdviceTodayPage";
import { TermsAgreementPage, EmailVerifyPage, PasswordResetPage, OnboardingCompletePage } from "./pages/AuthOnboardingPages";
import { BadgePage } from "./pages/challenge/BadgePage";
import { ChallengeDashboardPage } from "./pages/challenge/ChallengeDashboardPage";
import { ChallengeDetailPage } from "./pages/challenge/ChallengeDetailPage";
import { ChallengeListPage } from "./pages/challenge/ChallengeListPage";
import { LeaderboardPage } from "./pages/challenge/LeaderboardPage";
import { MyChallengesPage } from "./pages/challenge/MyChallengesPage";
import { PublicLayout } from "./layouts/PublicLayout";
import { FoodAnalyzePage } from "./pages/FoodAnalyzePage";
import { FoodPage } from "./pages/FoodPage";
import { HomePage } from "./pages/HomePage";
import { ActivityPage } from "./pages/health/ActivityPage";
import { ExercisePage } from "./pages/health/ExercisePage";
import { GoalEditPage } from "./pages/health/GoalEditPage";
import { GoalPage } from "./pages/health/GoalPage";
import { HealthHubPage } from "./pages/health/HealthHubPage";
import { HealthProfilePage } from "./pages/health/HealthProfilePage";
import { VitalsDetailPage } from "./pages/health/VitalsDetailPage";
import { VitalsInputPage } from "./pages/health/VitalsInputPage";
import { VitalsListPage } from "./pages/health/VitalsListPage";
import { HealthSurveyPage } from "./pages/HealthSurveyPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { PetEncyclopediaPage } from "./pages/PetEncyclopediaPage";
import { PetPage } from "./pages/PetPage";
import { PetSelectPage } from "./pages/PetSelectPage";
import { PredictionFeedbackPage } from "./pages/PredictionFeedbackPage";
import { PredictionHistoryPage } from "./pages/PredictionHistoryPage";
import { PredictionProgressPage } from "./pages/PredictionProgressPage";
import { PredictionRequestPage } from "./pages/PredictionRequestPage";
import { PredictionResultPage } from "./pages/PredictionResultPage";
import ReportDetailPage from "./pages/report/ReportDetailPage";
import ReportExportPage from "./pages/report/ReportExportPage";
import ReportListPage from "./pages/report/ReportListPage";
import { SignUpPage } from "./pages/SignUpPage";

// ── front/mypage-management 브랜치에서 추가
import { MyInfoPage } from "./pages/MyInfoPage";
import { EditProfilePage } from "./pages/EditProfilePage";
import { ChangePasswordPage, NotificationSettingsPage, TermsManagementPage, WithdrawalPage } from "./pages/MyPageSubPages";

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
    "/prediction/request",
    "/prediction/progress",
    "/prediction/result",
    "/prediction/history",
    "/prediction/feedback",
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

  useEffect(() => {
    const onPopState = () => setRoute(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = (nextRoute: AppRoute) => {
    const nextUrl =
      window.location.pathname === nextRoute && window.location.search
        ? `${nextRoute}${window.location.search}`
        : nextRoute;
    window.history.pushState({}, "", nextUrl);
    setRoute(nextRoute);
  };

  const page = useMemo(() => {
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
        return <HealthHubPage onNavigate={navigate} />;
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
        return <FoodAnalyzePage onNavigate={navigate} />;
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
  }, [route]);

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
