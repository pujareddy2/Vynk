"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageContainer from "../../components/PageContainer";
import { notificationService, NotificationItem as BackendNotif } from "../../services/notification.service";

interface DisplayNotification {
  id: number;
  title: string;
  message: string;
  time: string;
  unread: boolean;
  icon: string;
  type: string;
  actionable?: boolean;
  status: "UNREAD" | "READ" | "ACCEPTED" | "DISMISSED";
  actionPayload?: any;
}

const fallbackNotifications: DisplayNotification[] = [
  {
    id: 101,
    title: "Squad Invitation: Badminton Sparring",
    message: "Aarav Sharma invited you to join 'Indiranagar Weekend Badminton Smash' squad (3/4 players joined; 1 needed for quorum).",
    time: "2 min ago",
    unread: true,
    icon: "🏸",
    type: "SQUAD_INVITATION",
    actionable: true,
    status: "UNREAD",
    actionPayload: { squad_id: 12, activity: "Badminton", link: "/connections" },
  },
  {
    id: 102,
    title: "🚀 Quorum Reached & Event Converted!",
    message: "Milestone: '5v5 Turf Football Night Spar' squad reached full quorum (10/10 members) and auto-converted into a confirmed Event at Gachibowli Turf Arena!",
    time: "15 min ago",
    unread: true,
    icon: "⚽",
    type: "QUORUM_REACHED",
    actionable: true,
    status: "UNREAD",
    actionPayload: { event_id: 8, link: "/events" },
  },
  {
    id: 103,
    title: "⭐ Post-Event Peer Feedback Prompt",
    message: "You attended 'Sunset Photography Walk' with Puja & Maya. Leave a rating and peer review to build your community trust score!",
    time: "1 hour ago",
    unread: true,
    icon: "⭐",
    type: "FEEDBACK_REQUEST",
    actionable: true,
    status: "UNREAD",
    actionPayload: { event_id: 5, link: "/events" },
  },
  {
    id: 104,
    title: "💳 Split Court Share Ready",
    message: "Your court split share for 'Badminton Doubles Sparring Arena' is ₹180 at Indiranagar Smash Arena. Instant payment is open.",
    time: "2 hours ago",
    unread: true,
    icon: "💳",
    type: "PAYMENT_REQUEST",
    actionable: true,
    status: "UNREAD",
    actionPayload: { event_id: 8, link: "/events" },
  },
  {
    id: 105,
    title: "Activity Maintenance Recommendation",
    message: "Recommended: Schedule Week 2 session for 'Weekend Cycling' community to maintain club momentum.",
    time: "3 hours ago",
    unread: true,
    icon: "⚡",
    type: "MAINTENANCE",
    actionable: true,
    status: "UNREAD",
  },
  {
    id: 106,
    title: "New 94% Match Nearby",
    message: "Maya has a 94% affinity match with you based on Photography and Specialty Coffee with overlapping Saturday alarm windows.",
    time: "Yesterday",
    unread: false,
    icon: "♡",
    type: "MATCH",
    actionable: false,
    status: "READ",
  },
  {
    id: 107,
    title: "System Trust Verified",
    message: "Your profile achieved a 95% trust score across completed events and peer sparring check-ins.",
    time: "2 days ago",
    unread: false,
    icon: "✓",
    type: "ALERT",
    actionable: false,
    status: "READ",
  },
];

function getIconForType(type: string): string {
  switch (type.toUpperCase()) {
    case "SQUAD_INVITATION":
    case "INVITATION":
    case "COMMUNITY_INVITATION":
      return "🏸";
    case "QUORUM_REACHED":
    case "EVENT_CONVERTED":
      return "🚀";
    case "FEEDBACK_REQUEST":
    case "EVENT_FEEDBACK":
      return "⭐";
    case "PAYMENT_REQUEST":
      return "💳";
    case "ACTIVITY_MAINTENANCE":
    case "MAINTENANCE":
      return "⚡";
    case "MATCH":
      return "♡";
    case "COMMUNITY_REACTIVATION":
    case "UPDATE":
      return "✦";
    default:
      return "🔔";
  }
}

function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return "Just now";
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return "Recent";
  }
}

export default function NotificationsPage() {
  const [items, setItems] = useState<DisplayNotification[]>(fallbackNotifications);
  const [filter, setFilter] = useState<"ALL" | "UNREAD" | "ACTIONABLE">("ALL");
  const [loading, setLoading] = useState(true);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadBackendNotifications() {
      try {
        setLoading(true);
        const res = await notificationService.getNotifications(50, 0);
        if (res && res.notifications && res.notifications.length > 0) {
          const mapped: DisplayNotification[] = res.notifications.map((n: BackendNotif) => ({
            id: n.notification_id,
            title: n.title,
            message: n.message,
            time: formatRelativeTime(n.created_at),
            unread: !n.is_read && n.status === "UNREAD",
            icon: getIconForType(n.notification_type),
            type: n.notification_type,
            actionable: !!n.action_type || n.notification_type.includes("MAINTENANCE") || n.notification_type.includes("INVITATION"),
            status: n.status,
            actionPayload: n.payload,
          }));
          setItems(mapped);
        }
      } catch {
        // Unauthenticated or network error — fallback gracefully
      } finally {
        setLoading(false);
      }
    }
    loadBackendNotifications();
  }, []);

  const unreadCount = items.filter((n) => n.unread).length;

  const markAllAsRead = async () => {
    setItems((prev) =>
      prev.map((n) => ({
        ...n,
        unread: false,
        status: n.status === "UNREAD" ? "READ" : n.status,
      }))
    );
    // Asynchronously sync unread items to backend
    items.filter((n) => n.unread).forEach((n) => {
      notificationService.markAsRead(n.id).catch(() => {});
    });
  };

  const markAsRead = async (id: number) => {
    setItems((prev) =>
      prev.map((n) => (n.id === id ? { ...n, unread: false, status: n.status === "UNREAD" ? "READ" : n.status } : n))
    );
    try {
      await notificationService.markAsRead(id);
    } catch {}
  };

  const handleAccept = async (id: number) => {
    setItems((prev) =>
      prev.map((n) =>
        n.id === id
          ? { ...n, status: "ACCEPTED", unread: false }
          : n
      )
    );
    try {
      const res = await notificationService.acceptNotification(id, true);
      setActionSuccessMsg(res?.message || "Action executed successfully!");
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (e: any) {
      setActionSuccessMsg(e?.message || "Action accepted.");
      setTimeout(() => setActionSuccessMsg(null), 3000);
    }
  };

  const handleDismiss = async (id: number) => {
    setItems((prev) =>
      prev.map((n) =>
        n.id === id
          ? { ...n, status: "DISMISSED", unread: false }
          : n
      )
    );
    try {
      await notificationService.dismissNotification(id);
    } catch {}
  };

  const visibleItems = items.filter((n) => {
    if (filter === "UNREAD") return n.unread;
    if (filter === "ACTIONABLE") return n.actionable && n.status !== "DISMISSED";
    return true;
  });

  return (
    <PageContainer>
      <div className="mx-auto w-full max-w-4xl space-y-6">
        {/* Header Banner */}
        <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-teal-900 p-8 text-white shadow-lg md:p-10">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-teal-300">
                Your Inbox
              </p>

              <h1 className="mt-3 text-4xl font-bold md:text-5xl">
                Stay in the loop.
              </h1>

              <p className="mt-4 max-w-xl leading-7 text-slate-300">
                Review actionable invitations, community maintenance prompts, match alerts, and updates from the Vynk engine.
              </p>
            </div>

            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-teal-500/20 text-3xl text-teal-300">
              🔔
            </div>
          </div>
        </section>

        {actionSuccessMsg && (
          <div className="rounded-2xl bg-teal-500/10 border border-teal-500/30 p-4 text-sm font-semibold text-teal-300 flex items-center justify-between">
            <span>✓ {actionSuccessMsg}</span>
            <button onClick={() => setActionSuccessMsg(null)} className="text-teal-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Inbox Container */}
        <section className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 md:p-7 dark:bg-slate-900 dark:ring-slate-800">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                Notifications
              </h2>

              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                You have {unreadCount} unread update{unreadCount !== 1 ? "s" : ""}.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
                {(["ALL", "UNREAD", "ACTIONABLE"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setFilter(tab)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer ${
                      filter === tab
                        ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white"
                        : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                    }`}
                  >
                    {tab.charAt(0) + tab.slice(1).toLowerCase()}
                  </button>
                ))}
              </div>

              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllAsRead}
                  className="rounded-xl px-3 py-1.5 text-xs font-semibold text-teal-600 transition hover:bg-teal-50 dark:text-teal-400 dark:hover:bg-slate-800 cursor-pointer"
                >
                  Mark all read
                </button>
              )}
            </div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {loading ? (
              <div className="py-12 text-center text-slate-400">
                Loading notifications...
              </div>
            ) : visibleItems.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                No notifications in this view.
              </div>
            ) : (
              visibleItems.map((notification) => (
                <article
                  key={notification.id}
                  onClick={() => markAsRead(notification.id)}
                  className={`flex flex-col gap-4 py-5 first:pt-0 last:pb-0 sm:flex-row sm:items-start transition cursor-pointer ${
                    notification.unread ? "bg-teal-50/40 dark:bg-teal-950/20 -mx-3 px-3 rounded-2xl" : ""
                  }`}
                >
                  <div className="relative flex shrink-0">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-50 text-xl font-bold text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                      {notification.icon}
                    </div>

                    {notification.unread && (
                      <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-teal-500 ring-2 ring-white dark:ring-slate-900" />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-900 dark:text-white">
                          {notification.title}
                        </h3>

                        {notification.status === "ACCEPTED" && (
                          <span className="rounded-full bg-teal-100 px-2.5 py-0.5 text-[10px] font-bold text-teal-700 dark:bg-teal-900/60 dark:text-teal-300">
                            Accepted ✓
                          </span>
                        )}

                        {notification.status === "DISMISSED" && (
                          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold text-slate-500 dark:bg-slate-800">
                            Dismissed
                          </span>
                        )}
                      </div>

                      <span className="text-xs text-slate-400">
                        {notification.time}
                      </span>
                    </div>

                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {notification.message}
                    </p>

                    {/* Action buttons for actionable notifications */}
                    {notification.actionable && notification.status !== "ACCEPTED" && notification.status !== "DISMISSED" && (
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        {notification.type === "QUORUM_REACHED" || notification.type === "EVENT_CONVERTED" ? (
                          <Link
                            href="/events"
                            className="rounded-xl bg-teal-400 px-4 py-1.5 text-xs font-bold text-slate-950 transition hover:bg-teal-300 inline-block"
                          >
                            🎟️ View Converted Event →
                          </Link>
                        ) : notification.type === "FEEDBACK_REQUEST" ? (
                          <Link
                            href="/events"
                            className="rounded-xl bg-amber-400 px-4 py-1.5 text-xs font-bold text-slate-950 transition hover:bg-amber-300 inline-block"
                          >
                            ⭐ Rate &amp; Review Event →
                          </Link>
                        ) : notification.type === "PAYMENT_REQUEST" ? (
                          <Link
                            href="/events"
                            className="rounded-xl bg-teal-400 px-4 py-1.5 text-xs font-bold text-slate-950 transition hover:bg-teal-300 inline-block"
                          >
                            💳 Pay Court Share →
                          </Link>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAccept(notification.id);
                              }}
                              className="rounded-xl bg-slate-900 px-4 py-1.5 text-xs font-bold text-white transition hover:bg-slate-800 dark:bg-teal-400 dark:text-slate-950 cursor-pointer"
                            >
                              ✓ Accept Squad Invite
                            </button>
                            <Link
                              href="/connections"
                              className="rounded-xl border border-teal-500/30 bg-teal-500/10 px-3 py-1.5 text-xs font-bold text-teal-700 dark:text-teal-300 hover:bg-teal-500/20"
                            >
                              🎴 View Deck
                            </Link>
                          </>
                        )}

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDismiss(notification.id);
                          }}
                          className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 cursor-pointer"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </div>
    </PageContainer>
  );
}