import PageContainer from "../../components/PageContainer";

const notifications = [
  {
    title: "New match",
    message: "Maya has a 91% match with you.",
    time: "5 min ago",
    unread: true,
    icon: "♡",
  },
  {
    title: "Activity reminder",
    message: "Weekend Cycling starts tomorrow at 9:00 AM.",
    time: "1 hour ago",
    unread: true,
    icon: "✓",
  },
  {
    title: "Community update",
    message: "Creative Corner has a new discussion.",
    time: "3 hours ago",
    unread: false,
    icon: "✦",
  },
  {
    title: "Event invitation",
    message: "You were invited to Creative Coffee Meetup.",
    time: "Yesterday",
    unread: false,
    icon: "◈",
  },
  {
    title: "New recommendation",
    message: "We found an activity that might be perfect for you.",
    time: "Yesterday",
    unread: false,
    icon: "★",
  },
];

export default function NotificationsPage() {
  return (
    <PageContainer>
      <div className="mx-auto w-full max-w-4xl space-y-6">
        <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-900 p-8 text-white shadow-lg md:p-10">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-purple-300">
                Your inbox
              </p>

              <h1 className="mt-3 text-4xl font-bold md:text-5xl">
                Stay in the loop.
              </h1>

              <p className="mt-4 max-w-xl leading-7 text-slate-300">
                Your latest updates, invitations, matches, and reminders are
                all here.
              </p>
            </div>

            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-purple-500/20 text-2xl text-purple-300">
              ♢
            </div>
          </div>
        </section>

        <section className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 md:p-7">
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Notifications
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                You have 2 unread updates.
              </p>
            </div>

            <button
              type="button"
              className="self-start rounded-lg px-3 py-2 text-sm font-semibold text-purple-600 transition hover:bg-purple-50"
            >
              Mark all as read
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <article
                key={`${notification.title}-${notification.time}`}
                className={`flex gap-4 py-5 first:pt-0 last:pb-0 ${
                  notification.unread ? "bg-purple-50/50" : ""
                }`}
              >
                <div className="relative flex shrink-0">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-50 text-lg font-bold text-purple-600">
                    {notification.icon}
                  </div>

                  {notification.unread && (
                    <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full bg-purple-500 ring-2 ring-white" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <h3 className="font-semibold text-slate-900">
                      {notification.title}
                    </h3>

                    <span className="text-xs text-slate-400">
                      {notification.time}
                    </span>
                  </div>

                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    {notification.message}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </PageContainer>
  );
}