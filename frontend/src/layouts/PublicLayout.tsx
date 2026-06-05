import type { PropsWithChildren } from "react";

import type { AppRoute } from "../App";
import logoUrl from "../assets/all4health-logo.png";

type PublicLayoutProps = PropsWithChildren<{
  onNavigate: (route: AppRoute) => void;
}>;

export function PublicLayout({ children, onNavigate }: PublicLayoutProps) {
  return (
    <div className="public-shell">
      <header className="public-header">
        <button className="public-logo" type="button" onClick={() => onNavigate("/")}>
          <img src={logoUrl} alt="All4Health Chronic Care" />
        </button>
        <nav className="public-nav" aria-label="서비스 소개 메뉴">
          <a href="#service">서비스 소개</a>
          <a href="#features">주요 기능</a>
          <a href="#diseases">질환 관리</a>
          <a href="#challenge">챌린지</a>
        </nav>
        <div className="public-actions">
          <button className="outline-button" type="button" onClick={() => onNavigate("/login")}>
            로그인
          </button>
          <button className="dark-button" type="button" onClick={() => onNavigate("/login")}>
            시작하기
          </button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
