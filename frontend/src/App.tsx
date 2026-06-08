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

// ── front/food-management 브랜치에서 추가
import { FoodPage } from "./pages/FoodPage";
import { FoodAnalyzePage } from "./pages/FoodAnalyzePage";

// -- front/report-ㅡmanagement 브랜치에서 추가
import ReportListPage from "./pages/report/ReportListPage";
import ReportDetailPage from "./pages/report/ReportDetailPage";
import ReportExportPage from "./pages/report/ReportExportPage";

export type AppRoute =
  | "/"
  | "/login"
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
  | "/food"
  | "/food/analyze"
  | "/reports"
  | "/challenges"
  | "/pet"
  | "/reports/detail"
  | "/reports/export";

const publicRoutes = new Set<AppRoute>(["/", "/login"]);

function normalizePath(pathname: string): AppRoute {
  const knownRoutes: AppRoute[] = [
    "/",
    "/login",
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
    "/food",
    "/food/analyze",
    "/reports",
    "/challenges",
    "/pet",
    "/reports/detail",
    "/reports/export",
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
    window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
  };

  const page = useMemo(() => {
    switch (route) {
      case "/":
        return <LandingPage onNavigate={navigate} />;
      case "/login":
        return <LoginPage onLogin={() => navigate("/home")} />;
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
        return <PlaceholderPage title="건강 관리" description="건강 기록 입력/조회 화면을 연결할 영역입니다." />;
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
        return <PlaceholderPage title="마이펫" description="펫 현황, 보상 과제, 도감 화면을 연결할 영역입니다." />;
      default:
        return <HomePage />;
    }
  }, [route]);

  if (publicRoutes.has(route)) {
    return <PublicLayout onNavigate={navigate}>{page}</PublicLayout>;
  }

  return (
    <AppLayout currentRoute={route} onNavigate={navigate}>
      {page}
    </AppLayout>
  );
}
