import { fetchApi } from "./api";

export interface NotificationItem {
  notification_id: number;
  recipient_user_id: number;
  notification_type: string;
  title: string;
  message: string;
  payload?: Record<string, unknown> | null;
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

type UnreadCountListener = (count: number) => void;
const unreadListeners = new Set<UnreadCountListener>();
let cachedUnreadCount = 0;
let inFlightRefresh: Promise<number> | null = null;

export const notificationService = {
  subscribeUnreadCount(listener: UnreadCountListener): () => void {
    unreadListeners.add(listener);
    // Immediately notify with current known count
    listener(cachedUnreadCount);
    return () => {
      unreadListeners.delete(listener);
    };
  },

  getUnreadCountSync(): number {
    return cachedUnreadCount;
  },

  setUnreadCount(count: number): void {
    const sanitized = Math.max(0, Math.floor(count || 0));
    cachedUnreadCount = sanitized;
    unreadListeners.forEach((fn) => {
      try {
        fn(sanitized);
      } catch {}
    });
  },

  async refreshUnreadCount(): Promise<number> {
    if (typeof window === "undefined" || !localStorage.getItem("vynk_token")) {
      this.setUnreadCount(0);
      return 0;
    }

    if (inFlightRefresh) {
      return inFlightRefresh;
    }

    inFlightRefresh = (async () => {
      try {
        const res = await fetchApi<NotificationInboxResponse>("/notifications?limit=1&offset=0");
        if (typeof res?.unread_count === "number") {
          this.setUnreadCount(res.unread_count);
          return res.unread_count;
        }
      } catch (err: unknown) {
        if (typeof err === "object" && err !== null && "status" in err && (err as { status: number }).status === 401) {
          this.setUnreadCount(0);
        }
      } finally {
        inFlightRefresh = null;
      }
      return cachedUnreadCount;
    })();

    return inFlightRefresh;
  },

  async getNotifications(limit = 50, offset = 0): Promise<NotificationInboxResponse> {
    const res = await fetchApi<NotificationInboxResponse>(`/notifications?limit=${limit}&offset=${offset}`);
    if (typeof res?.unread_count === "number") {
      this.setUnreadCount(res.unread_count);
    }
    return res;
  },

  async markAsRead(notificationId: number): Promise<NotificationItem> {
    const res = await fetchApi<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
    });
    await this.refreshUnreadCount();
    return res;
  },

  async acceptNotification(notificationId: number, execute = true): Promise<unknown> {
    const res = await fetchApi(`/notifications/${notificationId}/accept?execute=${execute}`, {
      method: "PATCH",
    });
    await this.refreshUnreadCount();
    return res;
  },

  async dismissNotification(notificationId: number): Promise<unknown> {
    const res = await fetchApi(`/notifications/${notificationId}/dismiss`, {
      method: "PATCH",
    });
    await this.refreshUnreadCount();
    return res;
  },
};

export default notificationService;