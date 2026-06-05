import { useEffect, useMemo, useState } from "react";

import { AppLayout } from "./layouts/AppLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { HomePage } from "./pages/HomePage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { MyProfilePage } from "./pages/MyProfilePage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

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
  | "/mypage"
  | "/mypage/profile"
  | "/health"
  | "/food"
  | "/reports"
  | "/challenges"
  | "/pet";

// 로그인 없이 접근 가능한 경로
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
    "/mypage",
    "/mypage/profile",
    "/health",
    "/food",
    "/reports",
    "/challenges",
    "/pet",
  ];
  return knownRoutes.includes(pathname as AppRoute) ? (pathname as AppRoute) : "/home";
}

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => normalizePath(window.location.pathname));

  // TODO: API 연결 시 sessionStorage 토큰 체크로 교체
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

  // 로그인 안 된 상태에서 보호된 경로 접근 시 → /login으로
  const effectiveRoute = useMemo(() => {
    if (!isLoggedIn && !publicRoutes.has(route) && route !== "/health-survey" && route !== "/onboarding-complete") {
      return "/login" as AppRoute;
    }
    return route;
  }, [route, isLoggedIn]);

  const page = useMemo(() => {
    switch (effectiveRoute) {
      // ── 기존 코드 그대로 유지 ──
      case "/":
        return <LandingPage onNavigate={navigate} />;
      case "/login":
        return (
          <LoginPage
            onLogin={() => {
              setIsLoggedIn(true);
              navigate("/home");
            }}
            onNavigate={navigate}
          />
        );
      case "/home":
        return <HomePage />;
      case "/notifications":
        return <NotificationsPage />;
      case "/mypage":
      case "/mypage/profile":
        return <MyProfilePage />;
      case "/health":
        return <PlaceholderPage title="건강 관리" description="건강 기록 입력/조회 화면을 연결할 영역입니다." />;
      case "/food":
        return <PlaceholderPage title="식단 관리" description="식단 입력, 분석 결과, 기록 목록 화면을 연결할 영역입니다." />;
      case "/reports":
        return <PlaceholderPage title="리포트" description="주간 리포트 목록과 상세 화면을 연결할 영역입니다." />;
      case "/challenges":
        return <PlaceholderPage title="챌린지 관리" description="챌린지 목록, 참여, 체크인 화면을 연결할 영역입니다." />;
      case "/pet":
        return <PlaceholderPage title="마이펫" description="펫 현황, 보상 과제, 도감 화면을 연결할 영역입니다." />;

      // ── front/auth-onboarding 브랜치에서 추가한 라우트 ──
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

  if (publicRoutes.has(effectiveRoute) || effectiveRoute === "/health-survey" || effectiveRoute === "/onboarding-complete") {
    return <PublicLayout onNavigate={navigate}>{page}</PublicLayout>;
  }

  return (
    <AppLayout currentRoute={effectiveRoute} onNavigate={navigate}>
      {page}
    </AppLayout>
  );
}
