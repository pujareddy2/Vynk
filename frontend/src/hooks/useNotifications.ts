import { useState } from "react";
import { notificationService } from "@/services/notification.service";

export function useNotifications() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getNotifications = async (limit = 50, offset = 0) => {
    setLoading(true);
    setError(null);

    try {
      return await notificationService.getNotifications(limit, offset);
    } catch (err: any) {
      setError(err?.message || "Failed to load notifications");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: number) => {
    setLoading(true);
    setError(null);

    try {
      return await notificationService.markAsRead(id);
    } catch (err: any) {
      setError(err?.message || "Failed to mark notification as read");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const acceptNotification = async (id: number, execute = true) => {
    return await notificationService.acceptNotification(id, execute);
  };

  const dismissNotification = async (id: number) => {
    return await notificationService.dismissNotification(id);
  };

  return {
    getNotifications,
    markAsRead,
    acceptNotification,
    dismissNotification,
    loading,
    error,
  };
}