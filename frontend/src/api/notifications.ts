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

export type NotificationPreference = {
  push_enabled: boolean;
  health_data_reminder_enabled: boolean;
  challenge_mission_enabled: boolean;
  prediction_result_enabled: boolean;
  advice_update_enabled: boolean;
  virtual_pet_enabled: boolean;
  email_enabled: boolean;
  weekly_report_enabled: boolean;
  important_notice_enabled: boolean;
  promotion_enabled: boolean;
  quiet_start_time: string;
  quiet_end_time: string;
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

export async function getNotificationPreferences(token?: string) {
  return apiRequest<{ data: NotificationPreference }>("/notification-preferences", { token });
}

export async function updateNotificationPreferences(payload: Partial<NotificationPreference>, token?: string) {
  return apiRequest<{ data: NotificationPreference }>("/notification-preferences", {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}
