import type { AppRoute } from "../../App";

type TopBarProps = {
  onNavigate: (route: AppRoute) => void;
};

export function TopBar({ onNavigate }: TopBarProps) {
  return (
    <header className="topbar">
      <button className="topbar-brand" type="button" onClick={() => onNavigate("/home")}>
        ALL4Health
      </button>
      <div className="topbar-actions">
        <button className="icon-button" type="button" onClick={() => onNavigate("/notifications")} aria-label="알림 목록">
          <span aria-hidden="true">!</span>
        </button>
        <button className="profile-button" type="button" onClick={() => onNavigate("/mypage/profile")}>
          <span className="profile-avatar" aria-hidden="true">
            나
          </span>
          <span>내 정보</span>
        </button>
      </div>
    </header>
  );
}
