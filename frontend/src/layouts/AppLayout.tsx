import type { PropsWithChildren } from "react";
import { useEffect, useState } from "react";

import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import { getCurrentUser } from "../api/users";
import { Sidebar } from "../components/common/Sidebar";

type AppLayoutProps = PropsWithChildren<{
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
}>;

const sidebarStorageKey = "all4health.sidebarCollapsed";

export function AppLayout({ children, currentRoute, onNavigate }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(sidebarStorageKey) === "true");
  const [userName, setUserName] = useState("사용자");

  useEffect(() => {
    localStorage.setItem(sidebarStorageKey, String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    getCurrentUser(token)
      .then((user) => setUserName(user.name))
      .catch(() => setUserName("사용자"));
  }, []);

  return (
    <div className={`app-shell ${collapsed ? "is-sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={collapsed}
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        onToggle={() => setCollapsed((value) => !value)}
        userName={userName}
      />
      <div className="app-main">
        <main className="page-container">{children}</main>
      </div>
    </div>
  );
}
