import type { PropsWithChildren } from "react";
import { useEffect, useRef, useState } from "react";

import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import { getNotifications, type NotificationItem } from "../api/notifications";
import { getCurrentUser } from "../api/users";
import { Sidebar } from "../components/common/Sidebar";
import { getStoredProfileImage, profileImageUpdatedEvent } from "../utils/profileImage";

type AppLayoutProps = PropsWithChildren<{
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
}>;

const sidebarStorageKey = "all4health.sidebarCollapsed";

export function AppLayout({ children, currentRoute, onNavigate }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(sidebarStorageKey) === "true");
  const [userName, setUserName] = useState("사용자");
  const [userId, setUserId] = useState<number | null>(null);
  const [profileImageUrl, setProfileImageUrl] = useState<string | null>(null);
  const [toastNotification, setToastNotification] = useState<NotificationItem | null>(null);
  const seenNotificationIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    localStorage.setItem(sidebarStorageKey, String(collapsed));
  }, [collapsed]);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    getCurrentUser(token)
      .then((user) => {
        setUserId(user.id);
        setUserName(user.name);
        setProfileImageUrl(getStoredProfileImage(user.id) ?? user.profile_image_url);
      })
      .catch(() => {
        setUserId(null);
        setUserName("사용자");
        setProfileImageUrl(null);
      });
  }, []);

  useEffect(() => {
    const handleProfileImageUpdated = (event: Event) => {
      const detail = (event as CustomEvent<{ userId: number; profileImageUrl: string }>).detail;
      if (userId !== null && detail?.userId === userId) {
        setProfileImageUrl(detail.profileImageUrl);
      }
    };

    window.addEventListener(profileImageUpdatedEvent, handleProfileImageUpdated);
    return () => window.removeEventListener(profileImageUpdatedEvent, handleProfileImageUpdated);
  }, [userId]);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    let ignore = false;
    let initialized = false;
    const fetchUnread = async () => {
      try {
        const response = await getNotifications(token);
        if (ignore) return;
        const unread = response.data.filter((item) => !item.is_read);
        const ids = new Set(unread.map((item) => item.notification_id));
        if (!initialized) {
          initialized = true;
          seenNotificationIdsRef.current = ids;
          return;
        }
        const newest = unread.find((item) => !seenNotificationIdsRef.current.has(item.notification_id));
        seenNotificationIdsRef.current = ids;
        if (newest) {
          setToastNotification(newest);
          window.setTimeout(() => setToastNotification((current) => (
            current?.notification_id === newest.notification_id ? null : current
          )), 5000);
        }
      } catch {
        // 알림 토스트 폴링 실패는 화면 사용을 막지 않습니다.
      }
    };

    void fetchUnread();
    const timer = window.setInterval(fetchUnread, 5000);
    return () => {
      ignore = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className={`app-shell ${collapsed ? "is-sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={collapsed}
        currentRoute={currentRoute}
        onNavigate={onNavigate}
        onToggle={() => setCollapsed((value) => !value)}
        userName={userName}
        profileImageUrl={profileImageUrl}
      />
      <div className="app-main">
        {toastNotification && (
          <button
            className="notification-toast"
            type="button"
            onClick={() => {
              const link = toastNotification.link_url;
              setToastNotification(null);
              if (link) {
                window.history.pushState({}, "", link);
                onNavigate(link.split("?")[0] as AppRoute);
              }
            }}
          >
            <strong>{toastNotification.title}</strong>
            <span>{toastNotification.message}</span>
          </button>
        )}
        <main className="page-container">{children}</main>
      </div>
    </div>
  );
}
