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
          <button className="dark-button" type="button" onClick={() => onNavigate("/signup")}>
            시작하기
          </button>
        </div>
      </header>
      <main>{children}</main>
      <footer className="public-footer">
        <div className="public-footer-inner">
          <div className="footer-brand">
            <img src={logoUrl} alt="All4Health Chronic Care" />
            <p>
              AI 기반 만성질환 관리 플랫폼으로
              <br />더 건강한 일상을 만들어 드립니다.
              <br />당뇨·고혈압·신장 건강까지 한번에.
            </p>
          </div>
          <div className="footer-links">
            <section>
              <h2>서비스</h2>
              <a href="#features">AI 건강 예측</a>
              <a href="#challenge">챌린지 시스템</a>
              <a href="#service">건강 대시보드</a>
              <a href="#features">복약 관리</a>
            </section>
            <section>
              <h2>지원</h2>
              <a href="#service">고객센터</a>
              <a href="#features">이용 가이드</a>
              <a href="#service">FAQ</a>
              <a href="#service">공지사항</a>
            </section>
            <section>
              <h2>법적 고지</h2>
              <a href="#service">이용약관</a>
              <a href="#service">개인정보처리방침</a>
              <a href="#service">의료 면책조항</a>
            </section>
          </div>
          <div className="footer-bottom">
            <span>© 2026 All4Health. All rights reserved.</span>
            <span>문의: support@all4health.kr</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
