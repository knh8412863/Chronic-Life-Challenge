import { apiRequest } from "./client";

export type NotificationItem = {
  notification_id: number;
  notification_type: "GENERAL" | "PREDICTION" | "CHALLENGE" | "ADVICE" | "REPORT";
  title: string;
  message: string;
  link_url: string | null;
  is_read: boolean;
  created_at: string;
};

export async function getNotifications(token?: string) {
  return apiRequest<{ data: NotificationItem[] }>("/notifications", { token });
}

export async function markAllNotificationsRead(token?: string) {
  return apiRequest<{ data: { updated_count: number; unread_count: number } }>("/notifications/read-all", {
    method: "PATCH",
    token,
  });
}
