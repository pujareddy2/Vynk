import { fetchApi } from "./api";

export interface NotificationItem {
  notification_id: number;
  recipient_user_id: number;
  notification_type: string;
  title: string;
  message: string;
  payload?: any;
  action_type?: string;
  action_target_id?: number;
  related_community_id?: number;
  related_event_id?: number;
  is_read: boolean;
  read_at?: string;
  status: "UNREAD" | "READ" | "ACCEPTED" | "DISMISSED";
  created_at: string;
  updated_at: string;
}

export interface NotificationInboxResponse {
  notifications: NotificationItem[];
  total: number;
  unread_count: number;
  limit: number;
  offset: number;
}

export const notificationService = {
  async getNotifications(limit = 50, offset = 0): Promise<NotificationInboxResponse> {
    return await fetchApi<NotificationInboxResponse>(`/notifications?limit=${limit}&offset=${offset}`);
  },

  async markAsRead(notificationId: number): Promise<NotificationItem> {
    return await fetchApi<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
    });
  },

  async acceptNotification(notificationId: number, execute = true): Promise<any> {
    return await fetchApi(`/notifications/${notificationId}/accept?execute=${execute}`, {
      method: "PATCH",
    });
  },

  async dismissNotification(notificationId: number): Promise<any> {
    return await fetchApi(`/notifications/${notificationId}/dismiss`, {
      method: "PATCH",
    });
  },
};

export default notificationService;