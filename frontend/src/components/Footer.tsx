import Link from "next/link";

const footerLinks = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Activities", href: "/activities" },
  { label: "Events", href: "/events" },
  { label: "Communities", href: "/communities" },
  { label: "Creators", href: "/creators" },
  { label: "Profile", href: "/profile" },
];

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
          <div className="max-w-sm">
            <Link
              href="/"
              className="text-2xl font-bold tracking-tight text-slate-900"
            >
              Vynk<span className="text-teal-500">.</span>
            </Link>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Discover people, activities, communities, and experiences that
              make life more interesting.
            </p>
          </div>

          <nav>
            <p className="text-sm font-semibold text-slate-900">
              Explore
            </p>

            <ul className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2">
              {footerLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-500 transition hover:text-teal-600"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-8 border-t border-slate-100 pt-5">
          <p className="text-xs text-slate-400">
            © 2026 Vynk. Connect. Discover. Experience.
          </p>
        </div>
      </div>
    </footer>
  );
}