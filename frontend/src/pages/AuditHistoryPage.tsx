import { useEffect, useState } from "react";

import {
  History,
  RefreshCw
} from "lucide-react";

import { Link } from "react-router-dom";

import api from "../services/api";

import type { GlobalAuditEvent } from "../types";

import { formatDateTime } from "../utils/format";

import Loading from "../components/common/Loading";


export default function AuditHistoryPage() {

  const [events, setEvents] = useState<GlobalAuditEvent[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  async function loadEvents() {

    setLoading(true);
    setError("");

    try {

      const { data } = await api.get<GlobalAuditEvent[]>(
        "/api/audit?limit=200"
      );

      setEvents(data);

    } catch {

      setError("Unable to load audit history.");

    } finally {

      setLoading(false);

    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  return (

    <div className="space-y-6">

      <div className="flex items-center justify-between gap-4">

        <div>
          <h1 className="text-2xl font-bold text-white">
            Audit History
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Track finance operations and approval decisions.
          </p>
        </div>

        <button
          onClick={loadEvents}
          className="rounded-lg border border-slate-700 p-2.5 text-slate-300 hover:bg-slate-800"
        >
          <RefreshCw size={17} />
        </button>

      </div>


      {loading ? (

        <Loading />

      ) : error ? (

        <div className="rounded-lg bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>

      ) : (

        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#111827]">

          <table className="w-full min-w-[750px] text-left">

            <thead>
              <tr className="border-b border-slate-800 text-xs uppercase text-slate-500">
                <th className="p-4">Action</th>
                <th className="p-4">Invoice</th>
                <th className="p-4">Performed by</th>
                <th className="p-4">Outcome</th>
                <th className="p-4">Timestamp</th>
              </tr>
            </thead>

            <tbody>

              {events.map(event => (

                <tr
                  key={event.id}
                  className="border-b border-slate-800/60 text-sm hover:bg-slate-800/30"
                >

                  <td className="p-4">

                    <div className="flex items-center gap-2 text-slate-200">

                      <History
                        size={15}
                        className="text-blue-400"
                      />

                      {event.action.replaceAll("_", " ")}

                    </div>

                  </td>

                  <td className="p-4">

                    {event.invoice_id ? (

                      <Link
                        to={`/invoices/${event.invoice_id}`}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        {event.invoice_number || `#${event.invoice_id}`}
                      </Link>

                    ) : "—"}

                  </td>

                  <td className="p-4 text-slate-300">
                    {event.actor_name}
                  </td>

                  <td className="p-4">

                    <span className={
                      event.outcome === "SUCCESS"
                        ? "text-emerald-400"
                        : "text-red-400"
                    }>
                      {event.outcome}
                    </span>

                  </td>

                  <td className="p-4 text-xs text-slate-500">
                    {formatDateTime(event.created_at)}
                  </td>

                </tr>

              ))}

            </tbody>

          </table>

          {!events.length && (

            <p className="p-10 text-center text-sm text-slate-500">
              No audit events recorded.
            </p>

          )}

        </div>

      )}

    </div>

  );
}