import type { AppRoute } from "../../App";
import logoUrl from "../../assets/all4health-logo.png";

type SidebarProps = {
  collapsed: boolean;
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
  onToggle: () => void;
};

const menuItems: Array<{ label: string; route: AppRoute }> = [
  { label: "홈", route: "/home" },
  { label: "건강 관리", route: "/health" },
  { label: "식단 관리", route: "/food" },
  { label: "리포트", route: "/reports" },
  { label: "챌린지 관리", route: "/challenges" },
  { label: "가상 펫", route: "/pet" },
  { label: "마이페이지", route: "/mypage/profile" },
];

function isActive(currentRoute: AppRoute, itemRoute: AppRoute) {
  if (itemRoute === "/mypage/profile") {
    return currentRoute.startsWith("/mypage");
  }
  return currentRoute === itemRoute;
}

export function Sidebar({ collapsed, currentRoute, onNavigate, onToggle }: SidebarProps) {
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
        {menuItems.map((item) => (
          <button
            className={`sidebar-item ${isActive(currentRoute, item.route) ? "is-active" : ""}`}
            key={item.route}
            type="button"
            onClick={() => onNavigate(item.route)}
            title={collapsed ? item.label : undefined}
          >
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      <button
        className="sidebar-profile"
        type="button"
        onClick={() => onNavigate("/mypage/profile")}
        aria-label="내 정보 화면으로 이동"
      >
        <span className="sidebar-profile-avatar" aria-hidden="true" />
        {!collapsed && (
          <span className="sidebar-profile-text">
            <strong>홍길동</strong>
            <small>내 정보</small>
          </span>
        )}
      </button>
    </aside>
  );
}
