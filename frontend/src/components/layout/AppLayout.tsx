import {
  useState,
  type ReactNode
} from "react";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout({
  children
}: {
  children: ReactNode;
}) {

  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#080d18]">

      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="min-h-screen lg:pl-64">

        <Topbar
          onMenu={() => setSidebarOpen(true)}
        />

        <main className="mx-auto w-full max-w-[1600px] p-4 md:p-8">

          {children}

        </main>

      </div>

    </div>
  );
}