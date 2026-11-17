import {
  useEffect,
  useMemo,
  useState
} from "react";

import {
  Search,
  RefreshCw
} from "lucide-react";

import {
  useSearchParams
} from "react-router-dom";

import api from "../services/api";

import type { Invoice } from "../types";

import InvoiceTable from "../components/invoices/InvoiceTable";

import UploadInvoice from "../components/invoices/UploadInvoice";

import Loading from "../components/common/Loading";

import EmptyState from "../components/common/EmptyState";


export default function InvoiceQueuePage() {

  const [invoices, setInvoices] = useState<Invoice[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [riskFilter, setRiskFilter] = useState("ALL");

  const [approvalFilter, setApprovalFilter] = useState("ALL");

  const [params] = useSearchParams();


  async function loadInvoices() {

    setLoading(true);
    setError("");

    try {

      const { data } = await api.get<Invoice[]>(
        "/api/invoices"
      );

      setInvoices(data);

    } catch {

      setError("Unable to load invoices. Check your connection and sign-in.");

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    void Promise.resolve().then(() => {
      if (params.get("filter") === "risk") {
        setRiskFilter("RISK");
      }

      return loadInvoices();
    });

  }, [params]);


  const filteredInvoices = useMemo(() => {

    return invoices.filter(invoice => {

      const query = search.toLowerCase();

      const matchesSearch = [

        invoice.vendor_name,

        invoice.invoice_number,

        invoice.gstin,

        String(invoice.id)

      ].some(value =>
        (value || "").toLowerCase().includes(query)
      );


      const matchesRisk =

        riskFilter === "ALL" ||

        (
          riskFilter === "RISK"
          && ["REVIEW", "HOLD"].includes(invoice.risk_status)
        ) ||

        invoice.risk_status === riskFilter;


      const matchesApproval =

        approvalFilter === "ALL" ||

        invoice.approval_status === approvalFilter;


      return (
        matchesSearch &&
        matchesRisk &&
        matchesApproval
      );

    });

  }, [
    invoices,
    search,
    riskFilter,
    approvalFilter
  ]);


  return (

    <div className="space-y-6">


      <div className="flex flex-wrap items-center justify-between gap-4">

        <div>
          <h1 className="text-2xl font-bold text-white">
            Invoice Queue
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage, search and review uploaded invoices.
          </p>
        </div>

        <button
          onClick={loadInvoices}
          className="flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          <RefreshCw size={16} />
          Refresh
        </button>

      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}


      <div className="grid gap-5 xl:grid-cols-[1fr_320px]">


        <div className="min-w-0 space-y-5">


          <div className="rounded-xl border border-slate-800 bg-[#111827] p-4">

            <div className="flex flex-wrap gap-3">

              <div className="relative min-w-[220px] flex-1">

                <Search
                  size={17}
                  className="absolute left-3 top-3.5 text-slate-500"
                />

                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search invoice, vendor or GSTIN..."
                  className="w-full rounded-lg border border-slate-700 bg-[#080d18] py-3 pl-10 pr-4 text-sm text-white outline-none focus:border-blue-500"
                />

              </div>


              <select
                value={riskFilter}
                onChange={e => setRiskFilter(e.target.value)}
                className="rounded-lg border border-slate-700 bg-[#080d18] px-3 py-3 text-sm text-slate-300 outline-none"
              >
                <option value="ALL">All risk statuses</option>
                <option value="RISK">Risk alerts</option>
                <option value="CLEAR">Clear</option>
                <option value="REVIEW">Review</option>
                <option value="HOLD">Hold</option>
                <option value="PENDING">Pending analysis</option>
              </select>


              <select
                value={approvalFilter}
                onChange={e => setApprovalFilter(e.target.value)}
                className="rounded-lg border border-slate-700 bg-[#080d18] px-3 py-3 text-sm text-slate-300 outline-none"
              >
                <option value="ALL">All approvals</option>
                <option value="PENDING">Pending</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
              </select>

            </div>

          </div>


          <div className="rounded-xl border border-slate-800 bg-[#111827]">

            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">

              <div>

                <h2 className="font-semibold text-white">
                  All invoices
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  {filteredInvoices.length} matching records
                </p>

              </div>

            </div>


            {loading ? (

              <Loading />

            ) : filteredInvoices.length === 0 ? (

              <div className="p-5">

                <EmptyState
                  title="No invoices found"
                  description="Try changing your filters or upload a new invoice."
                />

              </div>

            ) : (

              <InvoiceTable invoices={filteredInvoices} />

            )}

          </div>

        </div>


        <div>
          <UploadInvoice />
        </div>


      </div>

    </div>

  );
}