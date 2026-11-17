import {
  Menu,
  LogOut,
  UserRound
} from "lucide-react";

import { useAuth } from "../../context/AuthContext";

export default function Topbar({
  onMenu
}: {
  onMenu: () => void;
}) {

  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-800 bg-[#080d18]/95 px-4 backdrop-blur md:px-8">

      <div className="flex items-center gap-3">

        <button
          onClick={onMenu}
          className="text-slate-400 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={22} />
        </button>

        <div>
          <p className="text-sm font-medium text-white">
            Finance Workspace
          </p>

          <p className="text-[11px] text-slate-500">
            Invoice Intelligence & Security
          </p>
        </div>

      </div>

      <div className="flex items-center gap-4">

        <div className="hidden text-right sm:block">

          <p className="text-sm font-medium text-white">
            {user?.full_name}
          </p>

          <p className="text-[10px] text-slate-500">
            {user?.role.replaceAll("_", " ")}
          </p>

        </div>

        <div className="rounded-full border border-slate-700 bg-slate-800 p-2">
          <UserRound
            size={18}
            className="text-slate-300"
          />
        </div>

        <button
          onClick={logout}
          title="Logout"
          className="text-slate-400 transition hover:text-red-400"
        >
          <LogOut size={18} />
        </button>

      </div>

    </header>
  );
}