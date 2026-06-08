import { apiRequest } from "./client";

export type NotificationItem = {
  notification_id: number;
  notification_type: "GENERAL" | "PREDICTION" | "CHALLENGE" | "ADVICE" | "REPORT";
  title: string;
  message: string;
  link_url: string | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
};

export async function getUnreadNotificationCount(token?: string) {
  return apiRequest<{ data: { unread_count: number } }>("/notifications/unread-count", { token });
}

export async function getNotifications(token?: string) {
  return apiRequest<{ data: NotificationItem[] }>("/notifications", { token });
}

export async function markNotificationRead(notificationId: number, token?: string) {
  return apiRequest<{ data: { notification_id: number; is_read: boolean; read_at: string } }>(
    `/notifications/${notificationId}/read`,
    {
      method: "PATCH",
      token,
    },
  );
}

export async function markAllNotificationsRead(token?: string) {
  return apiRequest<{ data: { updated_count: number; unread_count: number } }>("/notifications/read-all", {
    method: "PATCH",
    token,
  });
}
