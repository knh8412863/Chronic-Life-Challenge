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

// ── front/food-management 브랜치에서 추가
import { FoodPage } from "./pages/FoodPage";
import { FoodAnalyzePage } from "./pages/FoodAnalyzePage";

// -- front/report-ㅡmanagement 브랜치에서 추가
import ReportListPage from "./pages/report/ReportListPage";
import ReportDetailPage from "./pages/report/ReportDetailPage";
import ReportExportPage from "./pages/report/ReportExportPage";
// ── front/auth-onboarding 브랜치에서 추가
import { SignUpPage } from "./pages/SignUpPage";
import { TermsAgreementPage, EmailVerifyPage, PasswordResetPage, OnboardingCompletePage } from "./pages/AuthOnboardingPages";
import { HealthSurveyPage } from "./pages/HealthSurveyPage";

// ── front/pet-management 브랜치에서 추가
import { PetPage } from "./pages/PetPage";
import { PetSelectPage } from "./pages/PetSelectPage";
import { PetEncyclopediaPage } from "./pages/PetEncyclopediaPage";

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
  | "/food/analyze"
  | "/reports"
  | "/challenges"
  | "/pet"
  | "/pet/select"
  | "/pet/encyclopedia"
  | "/reports/detail"
  | "/reports/export";

const publicRoutes = new Set<AppRoute>([
  "/",
  "/login",
  "/signup",
  "/terms",
  "/email-verify",
  "/password-reset",
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
    "/food/analyze",
    "/reports",
    "/challenges",
    "/pet",
    "/pet/select",
    "/pet/encyclopedia",
    "/reports/detail",
    "/reports/export",
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

  // 로그인 안 된 상태에서 보호된 경로 접근 시 → /login으로 이동
  const onboardingRoutes = new Set(["/health-survey", "/onboarding-complete"]);
  const effectiveRoute = useMemo(() => {
    if (!isLoggedIn && !publicRoutes.has(route) && !onboardingRoutes.has(route)) {
      return "/login" as AppRoute;
    }
    return route;
  }, [route, isLoggedIn]);

  const page = useMemo(() => {
    switch (effectiveRoute) {
      case "/":
        return <LandingPage onNavigate={navigate} />;
      case "/login":
        return <LoginPage onLogin={() => { setIsLoggedIn(true); navigate("/home"); }} onNavigate={navigate} />;
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
        return <PlaceholderPage title="챌린지 관리" description="챌린지 목록, 참여, 체크인 화면을 연결할 영역입니다." />;
      case "/pet":
        return <PetPage onNavigate={navigate} />;
      case "/pet/select":
        return <PetSelectPage onNavigate={navigate} />;
      case "/pet/encyclopedia":
        return <PetEncyclopediaPage onNavigate={navigate} />;
      default:
        return <HomePage />;
    }
  }, [effectiveRoute]);

  if (publicRoutes.has(effectiveRoute) || effectiveRoute === "/health-survey" || effectiveRoute === "/onboarding-complete") {
    return <PublicLayout onNavigate={navigate}>{page}</PublicLayout>;
  }

  return (
    <AppLayout currentRoute={effectiveRoute} onNavigate={navigate}>
      {page}
    </AppLayout>
  );
}
