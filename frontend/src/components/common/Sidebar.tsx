import type { AppRoute } from "../../App";
import { logout } from "../../api/auth";
import logoUrl from "../../assets/all4health-logo.png";

type SidebarProps = {
  collapsed: boolean;
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
  onToggle: () => void;
  userName?: string;
};

type MenuItem = {
  label: string;
  route: AppRoute;
  children?: Array<{ label: string; route: AppRoute }>;
};

const menuItems: MenuItem[] = [
  { label: "홈", route: "/home" },
  {
    label: "오늘의 조언",
    route: "/advices/today",
    children: [
      { label: "오늘의 조언", route: "/advices/today" },
      { label: "내 조언 이력", route: "/advices/history" },
    ],
  },
  {
    label: "질환 예측",
    route: "/prediction/request",
    children: [
      { label: "예측 요청하기", route: "/prediction/request" },
      { label: "예측 이력", route: "/prediction/history" },
    ],
  },
  {
    label: "건강 관리",
    route: "/health/profile",
    children: [
      { label: "건강 프로필", route: "/health/profile" },
      { label: "건강 목표", route: "/health/goal" },
      { label: "건강 수치 기록하기", route: "/health/vitals/input" },
      { label: "건강 기록 목록", route: "/health/vitals" },
      { label: "식단 입력", route: "/food/analyze" },
      { label: "식단 기록 목록", route: "/food" },
    ],
  },
  { label: "리포트", route: "/reports" },
  {
    label: "챌린지",
    route: "/challenges/list",
    children: [
      { label: "챌린지 목록", route: "/challenges/list" },
      { label: "내 챌린지 요약", route: "/challenges" },
      { label: "내 챌린지 현황", route: "/challenges/my" },
      { label: "챌린지 리더보드", route: "/challenges/leaderboard" },
      { label: "뱃지 목록", route: "/challenges/badges" },
    ],
  },
  { label: "나만의 펫 키우기", route: "/pet" },
  {
    label: "마이페이지",
    route: "/mypage/profile",
    children: [
      { label: "내 정보", route: "/mypage/profile" },
      { label: "알림 설정", route: "/mypage/notifications" },
      { label: "약관 동의 관리", route: "/mypage/terms" },
    ],
  },
];

function isActive(currentRoute: AppRoute, itemRoute: AppRoute) {
  if (itemRoute === "/home") {
    return currentRoute === "/home";
  }
  if (itemRoute === "/mypage/profile") {
    return currentRoute === "/mypage" || currentRoute.startsWith("/mypage/");
  }
  if (itemRoute === "/health/profile") {
    return currentRoute === "/health" || currentRoute.startsWith("/health/") || currentRoute.startsWith("/food");
  }
  if (itemRoute === "/advices/today") {
    return currentRoute.startsWith("/advices/");
  }
  if (itemRoute === "/prediction/request") {
    return currentRoute.startsWith("/prediction/");
  }
  if (itemRoute === "/challenges/list") {
    return currentRoute.startsWith("/challenges");
  }
  return currentRoute === itemRoute || currentRoute.startsWith(`${itemRoute}/`);
}

export function Sidebar({ collapsed, currentRoute, onNavigate, onToggle, userName = "사용자" }: SidebarProps) {
  const handleLogout = async () => {
    await logout();
    onNavigate("/login");
  };

  return (
    <aside className="sidebar" aria-label="주요 메뉴">
      <div className="sidebar-header">
        <button className="brand-button" type="button" onClick={() => onNavigate("/home")} aria-label="홈으로 이동">
          {!collapsed && <img src={logoUrl} alt="All4Health Chronic Care" />}
          {collapsed && <span className="logo-heart" aria-hidden="true" />}
        </button>
        <button className="sidebar-toggle" type="button" onClick={onToggle} aria-label="사이드바 접기 또는 펼치기">
          {collapsed ? ">" : "<"}
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const active = isActive(currentRoute, item.route);
          const expanded = !collapsed && active && item.children;
          return (
            <div className="sidebar-menu-group" key={item.route}>
              <button
                className={`sidebar-item ${active ? "is-active" : ""}`}
                type="button"
                onClick={() => onNavigate(item.route)}
                title={collapsed ? item.label : undefined}
              >
                {!collapsed && <span>{item.label}</span>}
              </button>
              {expanded && (
                <div className="sidebar-subnav">
                  {item.children?.map((child) => (
                    <button
                      key={child.route}
                      type="button"
                      className={`sidebar-subitem ${currentRoute === child.route ? "is-active" : ""}`}
                      onClick={() => onNavigate(child.route)}
                    >
                      {child.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <button className="sidebar-logout" type="button" onClick={handleLogout} title={collapsed ? "로그아웃" : undefined}>
        {!collapsed ? "로그아웃" : "↪"}
      </button>

      <button
        className="sidebar-profile"
        type="button"
        onClick={() => onNavigate("/mypage/profile")}
        aria-label="내 정보 화면으로 이동"
      >
        <span className="sidebar-profile-avatar" aria-hidden="true" />
        {!collapsed && (
          <span className="sidebar-profile-text">
            <strong>{userName}</strong>
            <small>내 정보</small>
          </span>
        )}
      </button>
    </aside>
  );
}
