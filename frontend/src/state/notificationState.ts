import { Notification } from "@/types/notification";

export type NotificationState = {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  error: string | null;
};

export const initialNotificationState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: null,
};