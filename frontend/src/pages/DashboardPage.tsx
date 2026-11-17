import {
  useEffect,
  useState
} from "react";

import {
  Files,
  ShieldAlert,
  ShieldCheck,
  Clock3,
  ArrowRight
} from "lucide-react";

import {
  Link
} from "react-router-dom";

import api from "../services/api";

import type { Invoice } from "../types";

import {
  formatCurrency,
  formatDate
} from "../utils/format";

import StatCard from "../components/common/StatCard";
import StatusBadge from "../components/common/StatusBadge";
import Loading from "../components/common/Loading";
import EmptyState from "../components/common/EmptyState";


export default function DashboardPage() {

  const [invoices, setInvoices] = useState<Invoice[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");


  async function loadInvoices() {

    try {

      const { data } = await api.get<Invoice[]>(
        "/api/invoices"
      );

      setInvoices(data);

    } catch {

      setError("Unable to load invoice information.");

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadInvoices();

  }, []);


  if (loading) return <Loading />;


  const total = invoices.length;

  const clear = invoices.filter(
    i => i.risk_status === "CLEAR"
  ).length;

  const review = invoices.filter(
    i => i.risk_status === "REVIEW"
  ).length;

  const hold = invoices.filter(
    i => i.risk_status === "HOLD"
  ).length;

  const riskAmount = invoices
    .filter(i =>
      ["REVIEW", "HOLD"].includes(i.risk_status)
    )
    .reduce(
      (sum, invoice) => sum + Number(invoice.total || 0),
      0
    );

  const recent = [...invoices]
    .filter(i => ["REVIEW", "HOLD"].includes(i.risk_status))
    .slice(0, 5);


  return (

    <div className="space-y-8">


      <div className="flex flex-wrap items-start justify-between gap-4">

        <div>
          <h1 className="text-2xl font-bold text-white">
            Dashboard
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Overview of invoice activity and financial risk.
          </p>
        </div>

        <Link
          to="/invoices"
          className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500"
        >
          View invoices
        </Link>

      </div>


      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}


      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <StatCard
          title="Total invoices"
          value={total}
          description="Invoices ingested"
          icon={Files}
          color="bg-blue-500/10 text-blue-400"
        />

        <StatCard
          title="Clear invoices"
          value={clear}
          description="Passed configured checks"
          icon={ShieldCheck}
          color="bg-emerald-500/10 text-emerald-400"
        />

        <StatCard
          title="Needs review"
          value={review}
          description="Waiting for investigation"
          icon={Clock3}
          color="bg-amber-500/10 text-amber-400"
        />

        <StatCard
          title="On hold"
          value={hold}
          description="Approval restricted"
          icon={ShieldAlert}
          color="bg-red-500/10 text-red-400"
        />

      </section>


      <section className="grid gap-4 lg:grid-cols-3">

        <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 lg:col-span-2">

          <div className="flex items-center justify-between">

            <div>
              <h2 className="font-semibold text-white">
                Recent risk alerts
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Latest invoices requiring attention.
              </p>
            </div>

            <Link
              to="/invoices?filter=risk"
              className="flex items-center gap-1 text-xs text-blue-400"
            >
              View all <ArrowRight size={14} />
            </Link>

          </div>


          <div className="mt-5 space-y-3">

            {recent.length === 0 ? (

              <EmptyState
                title="No risk alerts"
                description="No invoices are currently marked REVIEW or HOLD."
              />

            ) : (

              recent.map(invoice => (

                <Link
                  key={invoice.id}
                  to={`/invoices/${invoice.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 p-4 transition hover:border-slate-600 hover:bg-slate-800/40"
                >

                  <div>

                    <p className="text-sm font-medium text-white">
                      {invoice.vendor_name || "Unknown vendor"}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {invoice.invoice_number || "No invoice number"}
                      {" · "}
                      {formatDate(invoice.uploaded_at)}
                    </p>

                  </div>

                  <div className="flex items-center gap-3">

                    <span className="text-sm font-medium text-slate-300">
                      {formatCurrency(invoice.total)}
                    </span>

                    <StatusBadge status={invoice.risk_status} />

                  </div>

                </Link>

              ))

            )}

          </div>

        </div>


        <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">

          <h2 className="font-semibold text-white">
            Financial exposure
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Total value of REVIEW and HOLD invoices.
          </p>

          <h2 className="mt-6 text-3xl font-bold text-red-400">
            {formatCurrency(riskAmount)}
          </h2>

          <div className="mt-6 space-y-4">

            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-slate-400">Clear</span>
                <span className="text-emerald-400">{clear}</span>
              </div>

              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-emerald-500"
                  style={{
                    width: `${total ? clear / total * 100 : 0}%`
                  }}
                />
              </div>
            </div>


            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-slate-400">Review</span>
                <span className="text-amber-400">{review}</span>
              </div>

              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-amber-500"
                  style={{
                    width: `${total ? review / total * 100 : 0}%`
                  }}
                />
              </div>
            </div>


            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-slate-400">Hold</span>
                <span className="text-red-400">{hold}</span>
              </div>

              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-red-500"
                  style={{
                    width: `${total ? hold / total * 100 : 0}%`
                  }}
                />
              </div>
            </div>

          </div>

        </div>

      </section>

    </div>

  );
}