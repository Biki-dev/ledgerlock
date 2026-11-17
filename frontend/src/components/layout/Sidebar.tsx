import {
  NavLink
} from "react-router-dom";

import {
  LayoutDashboard,
  Files,
  ShieldAlert,
  History,
  ShieldCheck,
  X,
  FlaskConical
} from "lucide-react";

const links = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard
  },
  {
    label: "Invoice Queue",
    path: "/invoices",
    icon: Files
  },
  {
    label: "Risk Findings",
    path: "/invoices?filter=risk",
    icon: ShieldAlert
  },
  {
    label: "Audit History",
    path: "/audit",
    icon: History
  },
  {
    label: "Kane Assurance Lab",
    path: "/assurance",
    icon: FlaskConical
  }
];

export default function Sidebar({
  open,
  onClose
}: {
  open: boolean;
  onClose: () => void;
}) {

  return (
    <>
      {open && (
        <button
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          aria-label="Close navigation"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800 bg-[#0c1220] transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"
          }`}
      >

        <div className="flex h-20 items-center justify-between border-b border-slate-800 px-6">

          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              Ledger<span className="text-blue-500">Lock</span>
            </h1>

            <p className="mt-1 text-[10px] uppercase tracking-[0.2em] text-slate-500">
              AP Security Platform
            </p>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>

        </div>

        <div className="px-4 py-6">

          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            Workspace
          </p>

          <nav className="space-y-1">

            {links.map(({ label, path, icon: Icon }) => (

              <NavLink
                key={label}
                to={path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-3 text-sm transition ${isActive
                    ? "bg-blue-600/15 font-medium text-blue-400"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }`
                }
              >

                <Icon size={18} />

                {label}

              </NavLink>

            ))}

          </nav>

        </div>

        <div className="mt-auto border-t border-slate-800 p-4">

          <div className="rounded-lg bg-slate-800/60 p-3">

            <div className="flex items-center gap-2">

              <ShieldCheck
                size={17}
                className="text-emerald-400"
              />

              <span className="text-xs font-medium text-slate-300">
                Security monitoring active
              </span>

            </div>

            <p className="mt-2 text-[11px] leading-5 text-slate-500">
              Invoice verification and approval controls are enabled.
            </p>

          </div>

        </div>

      </aside>
    </>
  );
}