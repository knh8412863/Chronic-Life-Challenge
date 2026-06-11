import { useEffect, useState } from "react";

import type { AppRoute } from "../../App";
import { getStoredAccessToken } from "../../api/auth";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from "../../api/notifications";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

type NotificationsPageProps = {
  onNavigate: (route: AppRoute) => void;
};

const fallbackNotifications: NotificationItem[] = [
  {
    notification_id: 1,
    notification_type: "CHALLENGE",
    title: "30일 걷기 챌린지 목표를 달성했습니다!",
    message: "30일 걷기 챌린지 목표를 달성했습니다!",
    link_url: "/challenges",
    is_read: false,
    created_at: "2026-05-15T08:30:00",
  },
  {
    notification_id: 2,
    notification_type: "PREDICTION",
    title: "최근 혈압 수치가 높게 측정되었습니다.",
    message: "주의가 필요해요.",
    link_url: "/prediction/result",
    is_read: false,
    created_at: "2026-05-15T07:00:00",
  },
  {
    notification_id: 3,
    notification_type: "GENERAL",
    title: "오늘 혈당 측정을 아직 하지 않으셨어요.",
    message: "건강 기록을 입력해 주세요.",
    link_url: "/health",
    is_read: true,
    created_at: "2026-05-15T05:00:00",
  },
  {
    notification_id: 4,
    notification_type: "REPORT",
    title: "이번 주 건강 리포트가 도착했습니다.",
    message: "주간 리포트를 확인해 보세요.",
    link_url: "/reports",
    is_read: true,
    created_at: "2026-05-14T09:00:00",
  },
];

const notificationMeta = {
  CHALLENGE:  { icon: "🏆",  label: "챌린지",    iconBg: "#dcfce7", iconBorder: "1px solid #86efac", pillBg: "#dcfce7", pillBorder: "1px solid #86efac", pillColor: "#16a34a" },
  PREDICTION: { icon: "⚠️",  label: "건강경고",  iconBg: "#ffe4e6", iconBorder: "1px solid #fda4af", pillBg: "#ffe4e6", pillBorder: "1px solid #fda4af", pillColor: "#f43f5e" },
  GENERAL:    { icon: "🔔",  label: "리마인더",  iconBg: "#fef9c3", iconBorder: "1px solid #fde047", pillBg: "#fef9c3", pillBorder: "1px solid #fde047", pillColor: "#ca8a04" },
  REPORT:     { icon: "📊",  label: "주간리포트", iconBg: "#dbeafe", iconBorder: "1px solid #93c5fd", pillBg: "#dbeafe", pillBorder: "1px solid #93c5fd", pillColor: "#2563eb" },
  ADVICE:     { icon: "💬",  label: "조언",      iconBg: "#dcfce7", iconBorder: "1px solid #86efac", pillBg: "#dcfce7", pillBorder: "1px solid #86efac", pillColor: "#16a34a" },
};

const LINK_ROUTE_MAP: Record<string, AppRoute> = {
  "/home": "/home",
  "/notifications": "/notifications",
  "/prediction/request": "/prediction/request",
  "/prediction/progress": "/prediction/progress",
  "/prediction/result": "/prediction/result",
  "/prediction/history": "/prediction/history",
  "/prediction/feedback": "/prediction/feedback",
  "/advices/today": "/advices/today",
  "/advices/feedback": "/advices/feedback",
  "/advices/history": "/advices/history",
  "/health": "/health",
  "/health/goal": "/health/goal",
  "/health/goal/edit": "/health/goal/edit",
  "/health/profile": "/health/profile",
  "/health/vitals": "/health/vitals",
  "/health/vitals/input": "/health/vitals/input",
  "/health/vitals/detail": "/health/vitals/detail",
  "/health/exercise": "/health/exercise",
  "/health/activity": "/health/activity",
  "/food": "/food",
  "/food/analyze": "/food/analyze",
  "/reports": "/reports",
  "/reports/detail": "/reports/detail",
  "/reports/export": "/reports/export",
  "/challenges": "/challenges",
  "/challenges/list": "/challenges/list",
  "/challenges/detail": "/challenges/detail",
  "/challenges/my": "/challenges/my",
  "/challenges/leaderboard": "/challenges/leaderboard",
  "/challenges/badges": "/challenges/badges",
  "/pet": "/pet",
  "/pet/select": "/pet/select",
  "/pet/encyclopedia": "/pet/encyclopedia",
  "/mypage": "/mypage",
  "/mypage/profile": "/mypage/profile",
  "/mypage/edit": "/mypage/edit",
  "/mypage/change-password": "/mypage/change-password",
  "/mypage/notifications": "/mypage/notifications",
  "/mypage/terms": "/mypage/terms",
  "/mypage/withdrawal": "/mypage/withdrawal",
};

function resolveNotificationTarget(linkUrl: string | null): { route: AppRoute; url: string } {
  if (!linkUrl) return { route: "/home", url: "/home" };

  try {
    const parsed = new URL(linkUrl, window.location.origin);
    const route = LINK_ROUTE_MAP[parsed.pathname] ?? "/home";
    return { route, url: route === "/home" ? "/home" : `${route}${parsed.search}` };
  } catch {
    const route = LINK_ROUTE_MAP[linkUrl] ?? "/home";
    return { route, url: route };
  }
}

function formatNotificationTime(createdAt: string) {
  const created = new Date(createdAt);
  const diffMs = Date.now() - created.getTime();

  if (Number.isNaN(created.getTime()) || diffMs < 0) {
    return "방금 전";
  }

  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  if (diffMinutes < 1) return "방금 전";
  if (diffMinutes < 60) return `${diffMinutes}분 전`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}일 전`;

  return created.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

type LoadStatus = "loading" | "loaded" | "empty" | "error";

export function NotificationsPage({ onNavigate }: NotificationsPageProps) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [status, setStatus] = useState<LoadStatus>("loading");

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setItems(fallbackNotifications);
      setStatus(fallbackNotifications.length === 0 ? "empty" : "loaded");
      return;
    }
    getNotifications(token)
      .then((response) => {
        setItems(response.data);
        setStatus(response.data.length === 0 ? "empty" : "loaded");
      })
      .catch(() => setStatus("error"));
  }, []);

  const handleMarkAllRead = async () => {
    const token = getStoredAccessToken();
    setItems((prev) => prev.map((item) => ({ ...item, is_read: true })));
    if (token) {
      try {
        await markAllNotificationsRead(token);
      } catch {
        setStatus("error");
      }
    }
  };

  const handleNotificationClick = async (item: NotificationItem) => {
    const token = getStoredAccessToken();

    if (!item.is_read) {
      setItems((prev) =>
        prev.map((notification) =>
          notification.notification_id === item.notification_id ? { ...notification, is_read: true } : notification,
        ),
      );

      if (token) {
        try {
          await markNotificationRead(item.notification_id, token);
        } catch {
          setItems((prev) =>
            prev.map((notification) =>
              notification.notification_id === item.notification_id ? { ...notification, is_read: false } : notification,
            ),
          );
          setStatus("error");
          return;
        }
      }
    }

    const target = resolveNotificationTarget(item.link_url);
    if (target.url !== target.route) {
      window.history.pushState({}, "", target.url);
    }
    onNavigate(target.route);
  };

  return (
    <div className="page-stack notification-page">
      <section className="section-header-row">
        <h1>알림</h1>
        <div className="button-row">
          <button className="small-button" type="button" onClick={handleMarkAllRead}>
            모두 읽음 처리
          </button>
          <button className="small-button" type="button" onClick={() => onNavigate("/mypage/notifications")}>
            알림 설정
          </button>
        </div>
      </section>

      {status === "loading" && <LoadingState message="알림을 불러오는 중입니다." />}
      {status === "empty" && <EmptyState title="알림이 없습니다." description="새로운 알림이 오면 여기에 표시됩니다." />}
      {status === "error" && <ErrorState title="알림을 불러오지 못했습니다." description="잠시 후 다시 시도해 주세요." />}

      {status === "loaded" && (
        <section className="notification-list">
          {items.map((item) => {
            const meta = notificationMeta[item.notification_type];
            return (
              <button
                className={`notification-item ${item.is_read ? "" : "is-unread"}`}
                key={item.notification_id}
                type="button"
                onClick={() => void handleNotificationClick(item)}
              >
                <span className="notification-icon" style={{ background: meta.iconBg, border: meta.iconBorder }}>{meta.icon}</span>
                <span className="notification-content">
                  <span className="notification-meta-row">
                    <span className="pill" style={{ background: meta.pillBg, border: meta.pillBorder, color: meta.pillColor }}>{meta.label}</span>
                    <span className="notification-time">{formatNotificationTime(item.created_at)}</span>
                    {!item.is_read && <span className="unread-dot" />}
                  </span>
                  <strong>{item.title}</strong>
                  {item.message !== item.title && <small>{item.message}</small>}
                </span>
              </button>
            );
          })}
        </section>
      )}
    </div>
  );
}
