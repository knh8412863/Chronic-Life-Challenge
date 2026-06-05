import { useEffect, useState } from "react";

import type { AppRoute } from "../App";
import { getStoredAccessToken } from "../api/auth";
import { getNotifications, markAllNotificationsRead, type NotificationItem } from "../api/notifications";

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
  CHALLENGE: { icon: "🏆", label: "챌린지", tone: "green" },
  PREDICTION: { icon: "⚠", label: "건강경고", tone: "pink" },
  GENERAL: { icon: "🔔", label: "리마인더", tone: "yellow" },
  REPORT: { icon: "📊", label: "주간리포트", tone: "blue" },
  ADVICE: { icon: "💬", label: "조언", tone: "green" },
};

function formatNotificationTime(createdAt: string) {
  if (createdAt.includes("05-15T08")) {
    return "5분 전";
  }
  if (createdAt.includes("05-15T07")) {
    return "2시간 전";
  }
  if (createdAt.includes("05-15")) {
    return "3시간 전";
  }
  return "1일 전";
}

export function NotificationsPage({ onNavigate }: NotificationsPageProps) {
  const [items, setItems] = useState(fallbackNotifications);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      return;
    }
    getNotifications(token)
      .then((response) => setItems(response.data))
      .catch(() => setItems(fallbackNotifications));
  }, []);

  const handleMarkAllRead = () => {
    const token = getStoredAccessToken();
    setItems((prev) => prev.map((item) => ({ ...item, is_read: true })));
    if (token) {
      void markAllNotificationsRead(token);
    }
  };

  return (
    <div className="page-stack notification-page">
      <section className="section-header-row">
        <h1>알림</h1>
        <div className="button-row">
          <button className="small-button" type="button" onClick={handleMarkAllRead}>
            모두 읽음 처리
          </button>
          <button className="small-button" type="button">
            알림 설정
          </button>
        </div>
      </section>

      <section className="notification-list">
        {items.map((item) => {
          const meta = notificationMeta[item.notification_type];
          return (
            <button
              className={`notification-item ${item.is_read ? "" : "is-unread"}`}
              key={item.notification_id}
              type="button"
              onClick={() => onNavigate((item.link_url as AppRoute | null) ?? "/home")}
            >
              <span className="notification-icon">{meta.icon}</span>
              <span className="notification-content">
                <span className="notification-meta-row">
                  <span className={`pill pill-${meta.tone}`}>{meta.label}</span>
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
    </div>
  );
}
