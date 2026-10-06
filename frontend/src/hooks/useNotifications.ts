import { useState } from "react";
import { notificationService } from "@/services/notification.service";

export function useNotifications() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getNotifications = async () => {
    setLoading(true);
    setError(null);

    try {
      return await notificationService.getNotifications();
    } catch (err) {
      setError("Failed to load notifications");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async () => {
    setLoading(true);
    setError(null);

    try {
      return await notificationService.markAsRead();
    } catch (err) {
      setError("Failed to mark notification as read");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    getNotifications,
    markAsRead,
    loading,
    error,
  };
}