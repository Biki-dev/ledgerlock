import {
  useCallback,
  useEffect,
  useState
} from "react";

import {
  useParams
} from "react-router-dom";

import {
  FileText,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  History,
  RefreshCw
} from "lucide-react";

import api from "../services/api";

import type {
  Invoice,
  AuditEvent
} from "../types";

import {
  formatCurrency,
  formatDate,
  formatDateTime,
  getErrorMessage
} from "../utils/format";

import {
  useAuth
} from "../context/AuthContext";

import StatusBadge from "../components/common/StatusBadge";

import Loading from "../components/common/Loading";


export default function InvoiceDetailsPage() {

  const { id } = useParams();

  const invoiceId = Number(id);

  const { user } = useAuth();

  const [invoice, setInvoice] = useState<Invoice | null>(null);

  const [events, setEvents] = useState<AuditEvent[]>([]);

  const [pdfUrl, setPdfUrl] = useState("");

  const [loading, setLoading] = useState(true);

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");

  const [message, setMessage] = useState("");


  // Reviewer forms

  const [reviewNote, setReviewNote] = useState("");

  const [bankMethod, setBankMethod] = useState(
    "PHONE_TO_KNOWN_CONTACT"
  );

  const [bankReference, setBankReference] = useState("");

  const [bankNote, setBankNote] = useState("");

  const [rejectReason, setRejectReason] = useState("");


  const canReview =
    user?.role === "FINANCE_REVIEWER" ||
    user?.role === "ADMIN";

  const canApprove =
    user?.role === "FINANCE_APPROVER" ||
    user?.role === "ADMIN";

  const isPending =
    invoice?.approval_status === "PENDING";


  const loadData = useCallback(async () => {

    if (!Number.isInteger(invoiceId) || invoiceId < 1) {
      setError("Invalid invoice ID.");
      setLoading(false);
      return;
    }

    try {

      setError("");

      const [invoiceResponse, auditResponse, pdfResponse] =
        await Promise.allSettled([

          api.get<Invoice>(
            `/api/invoices/${invoiceId}`
          ),

          api.get<AuditEvent[]>(
            `/api/invoices/${invoiceId}/audit`
          ),

          api.get(
            `/api/invoices/${invoiceId}/source`,
            { responseType: "blob" }
          )

        ]);


      if (invoiceResponse.status === "rejected") {
        throw invoiceResponse.reason;
      }

      setInvoice(invoiceResponse.value.data);


      if (auditResponse.status === "fulfilled") {
        setEvents(auditResponse.value.data);
      } else {
        setEvents([]);
      }


      if (pdfResponse.status === "fulfilled") {

        const nextUrl = URL.createObjectURL(
          pdfResponse.value.data
        );

        setPdfUrl(nextUrl);

      } else {

        setPdfUrl("");

      }

    } catch (err) {

      setError(getErrorMessage(err));

    } finally {

      setLoading(false);

    }

  }, [invoiceId]);


  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);


  async function performAction(
    action: () => Promise<unknown>,
    successMessage: string
  ) {

    setBusy(true);
    setError("");
    setMessage("");

    try {

      await action();

      setMessage(successMessage);

      await loadData();

      setReviewNote("");
      setBankReference("");
      setBankNote("");
      setRejectReason("");

    } catch (err) {

      setError(getErrorMessage(err));

    } finally {

      setBusy(false);

    }

  }


  if (loading) return <Loading />;

  if (!invoice) {

    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-red-400">
        {error || "Invoice not found"}
      </div>
    );

  }


  const findings = invoice.risk_findings || [];

  const holdCodes = findings
    .filter(f => f.action === "HOLD")
    .map(f => f.rule_code);

  const onlyBankChangeHold =
    holdCodes.length > 0 &&
    new Set(holdCodes).size === 1 &&
    holdCodes[0] === "BANK_DETAILS_CHANGED" &&
    findings.every(f => f.action === "HOLD" || f.action === "REVIEW");

  const hasAdditionalFindings =
    findings.some(f => f.action !== "HOLD");

  const canVerifyBank =
    canReview &&
    isPending &&
    invoice.risk_status === "HOLD" &&
    invoice.verification_status === "PENDING" &&
    onlyBankChangeHold &&
    !hasAdditionalFindings;

  const canReviewInvoice =
    canReview &&
    isPending &&
    invoice.risk_status === "REVIEW" &&
    invoice.review_status === "PENDING";

  const canAttemptApproval =
    canApprove &&
    isPending &&
    (
      invoice.risk_status === "CLEAR" ||

      (
        invoice.risk_status === "REVIEW" &&
        invoice.review_status === "CLEARED" &&
        invoice.reviewed_by_id !== user?.id
      ) ||

      (
        invoice.risk_status === "HOLD" &&
        onlyBankChangeHold &&
        !hasAdditionalFindings &&
        invoice.verification_status === "VERIFIED" &&
        invoice.verified_by_id !== user?.id
      )
    );


  return (

    <div className="space-y-6">


      {/* HEADER */}

      <div className="flex flex-wrap items-start justify-between gap-4">

        <div>

          <p className="text-xs text-slate-500">
            Invoices / #{invoice.id}
          </p>

          <h1 className="mt-2 text-2xl font-bold text-white">
            {invoice.invoice_number || `Invoice #${invoice.id}`}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            {invoice.vendor_name || "Unknown vendor"}
          </p>

        </div>


        <div className="flex flex-wrap items-center gap-2">

          <StatusBadge status={invoice.risk_status} />

          <StatusBadge status={invoice.approval_status} />

          <button
            onClick={loadData}
            className="rounded-lg border border-slate-700 p-2 text-slate-400 hover:bg-slate-800"
          >
            <RefreshCw size={17} />
          </button>

        </div>

      </div>


      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-400">
          {message}
        </div>
      )}


      {/* MAIN GRID */}

      <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">


        {/* LEFT SIDE */}

        <div className="space-y-5">


          {/* PDF PREVIEW */}

          <section className="overflow-hidden rounded-xl border border-slate-800 bg-[#111827]">

            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">

              <div className="flex items-center gap-2">

                <FileText
                  size={17}
                  className="text-blue-400"
                />

                <h2 className="font-semibold text-white">
                  Original invoice
                </h2>

              </div>

              <span className="text-xs text-slate-500">
                {invoice.source_filename}
              </span>

            </div>


            {pdfUrl ? (

              <iframe
                src={pdfUrl}
                title="Invoice PDF"
                className="h-[650px] w-full bg-white"
              />

            ) : (

              <div className="p-8 text-center text-sm text-slate-500">
                PDF preview unavailable.
              </div>

            )}

          </section>


          {/* EXTRACTED DETAILS */}

          <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

            <h2 className="font-semibold text-white">
              Extracted invoice details
            </h2>

            <div className="mt-5 grid gap-5 sm:grid-cols-2">

              {[
                ["Vendor", invoice.vendor_name],
                ["Invoice number", invoice.invoice_number],
                ["Invoice date", formatDate(invoice.invoice_date)],
                ["GSTIN", invoice.gstin],
                ["Bank account", invoice.bank_account],
                ["IFSC", invoice.ifsc],
                ["Subtotal", formatCurrency(invoice.subtotal)],
                ["Tax", formatCurrency(invoice.tax)],
                ["Total", formatCurrency(invoice.total)]
              ].map(([label, value]) => (

                <div key={label}>

                  <p className="text-xs text-slate-500">
                    {label}
                  </p>

                  <p className="mt-2 break-all text-sm font-medium text-slate-200">
                    {value || "Not extracted"}
                  </p>

                </div>

              ))}

            </div>


            <div className="mt-6 border-t border-slate-800 pt-5">

              <div className="flex justify-between text-sm">

                <span className="text-slate-400">
                  Extraction method
                </span>

                <span className="text-slate-200">
                  {invoice.extraction_method}
                </span>

              </div>

              <div className="mt-3 flex justify-between text-sm">

                <span className="text-slate-400">
                  Extraction coverage
                </span>

                <span className="text-slate-200">
                  {Math.round(invoice.extraction_confidence * 100)}%
                </span>

              </div>

              <StatusBadge status={invoice.extraction_status} />

            </div>

          </section>


          {/* LINE ITEMS */}

          <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

            <h2 className="font-semibold text-white">
              Invoice line items
            </h2>

            <div className="mt-4 overflow-x-auto">

              <table className="w-full min-w-[450px] text-left">

                <thead>
                  <tr className="border-b border-slate-800 text-xs text-slate-500">
                    <th className="py-3">Description</th>
                    <th>Quantity</th>
                    <th>Unit price</th>
                    <th>Amount</th>
                  </tr>
                </thead>

                <tbody>

                  {invoice.items?.map(item => (

                    <tr
                      key={item.id}
                      className="border-b border-slate-800/60 text-sm text-slate-300"
                    >

                      <td className="py-4">
                        {item.description}
                      </td>

                      <td>{item.quantity}</td>

                      <td>{formatCurrency(item.unit_price)}</td>

                      <td>{formatCurrency(item.line_total)}</td>

                    </tr>

                  ))}

                </tbody>

              </table>

              {!invoice.items?.length && (

                <p className="py-5 text-sm text-slate-500">
                  No line items extracted.
                </p>

              )}

            </div>

          </section>

        </div>


        {/* RIGHT SIDE */}

        <div className="space-y-5">


          {/* RISK SUMMARY */}

          <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

            <div className="flex items-center justify-between">

              <div className="flex items-center gap-2">

                <ShieldAlert
                  size={18}
                  className="text-amber-400"
                />

                <h2 className="font-semibold text-white">
                  Risk assessment
                </h2>

              </div>

              <StatusBadge status={invoice.risk_status} />

            </div>


            <div className="mt-6">

              <p className="text-xs text-slate-500">
                Heuristic risk score
              </p>

              <div className="mt-2 flex items-end justify-between">

                <h2 className="text-4xl font-bold text-white">
                  {invoice.risk_score}
                  <span className="text-lg text-slate-500">
                    /100
                  </span>
                </h2>

                <span className="text-xs text-slate-500">
                  Not a fraud probability
                </span>

              </div>

              <div className="mt-4 h-2 rounded-full bg-slate-800">

                <div
                  className={`h-2 rounded-full ${
                    invoice.risk_status === "HOLD"
                      ? "bg-red-500"
                      : invoice.risk_status === "REVIEW"
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.min(invoice.risk_score, 100)}%`
                  }}
                />

              </div>

            </div>


            <div className="mt-6 space-y-3">

              {findings.map(finding => (

                <div
                  key={finding.id}
                  className="rounded-lg border border-slate-700 bg-slate-900/70 p-4"
                >

                  <div className="flex flex-wrap items-center justify-between gap-2">

                    <span className="text-xs font-semibold text-slate-200">
                      {finding.rule_code.replaceAll("_", " ")}
                    </span>

                    <StatusBadge status={finding.severity} />

                  </div>

                  <p className="mt-3 text-sm leading-6 text-slate-400">
                    {finding.message}
                  </p>

                  <pre className="mt-3 overflow-x-auto rounded bg-black/30 p-3 text-[11px] text-slate-500">
                    {JSON.stringify(finding.evidence, null, 2)}
                  </pre>

                </div>

              ))}

              {!findings.length && (

                <div className="rounded-lg bg-emerald-500/5 p-4">

                  <CheckCircle2
                    size={20}
                    className="text-emerald-400"
                  />

                  <p className="mt-2 text-sm text-emerald-400">
                    No configured risk findings.
                  </p>

                </div>

              )}

            </div>

          </section>


          {/* APPROVAL CONTROL */}

          <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

            <div className="flex items-center gap-2">

              <ShieldCheck
                size={18}
                className="text-blue-400"
              />

              <h2 className="font-semibold text-white">
                Approval controls
              </h2>

            </div>


            <div className="mt-5 space-y-4">


              {/* REVIEW FORM */}

              {canReviewInvoice && (

                <div className="space-y-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">

                  <h3 className="text-sm font-semibold text-amber-400">
                    Reviewer investigation
                  </h3>

                  <textarea
                    value={reviewNote}
                    onChange={e => setReviewNote(e.target.value)}
                    placeholder="Explain the checks performed and evidence reviewed..."
                    rows={3}
                    className="w-full rounded-lg border border-slate-700 bg-[#080d18] p-3 text-sm text-white outline-none focus:border-blue-500"
                  />

                  <button
                    disabled={busy || reviewNote.trim().length < 10}
                    onClick={() => performAction(
                      () => api.post(
                        `/api/invoices/${invoice.id}/review`,
                        {
                          decision: "CLEAR_FOR_APPROVAL",
                          note: reviewNote
                        }
                      ),
                      "Review cleared. A different approver is required."
                    )}
                    className="w-full rounded-lg bg-amber-600 py-2.5 text-sm font-medium text-white hover:bg-amber-500"
                  >
                    Clear for approval
                  </button>

                </div>

              )}


              {/* BANK VERIFICATION FORM */}

              {canVerifyBank && (

                <div className="space-y-3 rounded-lg border border-red-500/20 bg-red-500/5 p-4">

                  <h3 className="text-sm font-semibold text-red-400">
                    Independent bank verification
                  </h3>

                  <select
                    value={bankMethod}
                    onChange={e => setBankMethod(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-[#080d18] p-3 text-sm text-slate-200"
                  >

                    <option value="PHONE_TO_KNOWN_CONTACT">
                      Call previously known vendor contact
                    </option>

                    <option value="VERIFIED_VENDOR_PORTAL">
                      Verified vendor portal
                    </option>

                    <option value="IN_PERSON">
                      In-person verification
                    </option>

                  </select>


                  <input
                    value={bankReference}
                    onChange={e => setBankReference(e.target.value)}
                    placeholder="Verification reference"
                    className="w-full rounded-lg border border-slate-700 bg-[#080d18] p-3 text-sm text-white"
                  />

                  <textarea
                    value={bankNote}
                    onChange={e => setBankNote(e.target.value)}
                    placeholder="Describe the independent verification..."
                    rows={3}
                    className="w-full rounded-lg border border-slate-700 bg-[#080d18] p-3 text-sm text-white"
                  />

                  <button
                    disabled={
                      busy ||
                      bankReference.trim().length < 3 ||
                      bankNote.trim().length < 10
                    }
                    onClick={() => performAction(
                      () => api.post(
                        `/api/invoices/${invoice.id}/verify-bank-change`,
                        {
                          method: bankMethod,
                          reference: bankReference,
                          note: bankNote
                        }
                      ),
                      "Verification recorded. A different approver must approve."
                    )}
                    className="w-full rounded-lg bg-red-600 py-2.5 text-sm font-medium text-white hover:bg-red-500"
                  >
                    Record bank verification
                  </button>

                </div>

              )}


              {/* APPROVE */}

              {canApprove && isPending && (

                <div className="space-y-2">

                  <button
                    disabled={busy || !canAttemptApproval}
                    onClick={() => performAction(
                      () => api.post(
                        `/api/invoices/${invoice.id}/approve`
                      ),
                      "Invoice approved successfully."
                    )}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 py-3 text-sm font-semibold text-white hover:bg-emerald-500"
                  >

                    <CheckCircle2 size={17} />

                    Approve invoice

                  </button>


                  {!canAttemptApproval && (

                    <p className="text-xs leading-5 text-amber-400">
                      {invoice.risk_status === "REVIEW"
                        ? "Reviewer clearance and a different approver are required."
                        : invoice.risk_status === "HOLD"
                        ? "Independent verification and a different approver are required. Other HOLD types require separate investigation."
                        : invoice.risk_status === "PENDING"
                        ? "Risk analysis must finish first."
                        : "Approval requirements are not satisfied."
                      }
                    </p>

                  )}

                </div>

              )}


              {/* REJECTION */}

              {isPending && (

                <div className="space-y-3 border-t border-slate-800 pt-4">

                  <label className="text-xs font-medium text-slate-400">
                    Rejection reason
                  </label>

                  <textarea
                    value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)}
                    placeholder="Explain why this invoice is being rejected..."
                    rows={2}
                    className="w-full rounded-lg border border-slate-700 bg-[#080d18] p-3 text-sm text-white"
                  />

                  <button
                    disabled={
                      busy ||
                      rejectReason.trim().length < 10
                    }
                    onClick={() => performAction(
                      () => api.post(
                        `/api/invoices/${invoice.id}/reject`,
                        {
                          reason: rejectReason
                        }
                      ),
                      "Invoice rejected."
                    )}
                    className="w-full rounded-lg border border-red-500/30 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/10"
                  >
                    Reject invoice
                  </button>

                </div>

              )}


              {!isPending && (

                <div className="rounded-lg bg-slate-900 p-4">

                  <p className="text-sm text-slate-300">
                    This invoice has been finalized.
                  </p>

                  <div className="mt-3 flex items-center gap-2">
                    {invoice.approval_status === "APPROVED"
                      ? <CheckCircle2 className="text-emerald-400" />
                      : <XCircle className="text-red-400" />
                    }

                    <StatusBadge status={invoice.approval_status} />
                  </div>

                </div>

              )}

            </div>

          </section>


          {/* APPROVAL HISTORY */}

          <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

            <div className="flex items-center gap-2">

              <History
                size={18}
                className="text-blue-400"
              />

              <h2 className="font-semibold text-white">
                Approval history
              </h2>

            </div>


            <div className="mt-5 space-y-4">

              {[
                {
                  label: "Invoice uploaded",
                  actor: null,
                  date: invoice.uploaded_at,
                  visible: true
                },

                {
                  label: "Review completed",
                  actor: invoice.reviewed_by_id,
                  date: invoice.reviewed_at,
                  visible: Boolean(invoice.reviewed_at)
                },

                {
                  label: "Bank verification completed",
                  actor: invoice.verified_by_id,
                  date: invoice.verified_at,
                  visible: Boolean(invoice.verified_at)
                },

                {
                  label: "Invoice approved",
                  actor: invoice.approved_by_id,
                  date: invoice.approved_at,
                  visible: Boolean(invoice.approved_at)
                },

                {
                  label: "Invoice rejected",
                  actor: invoice.rejected_by_id,
                  date: invoice.rejected_at,
                  visible: Boolean(invoice.rejected_at)
                }

              ].filter(item => item.visible).map((item, index) => (

                <div
                  key={index}
                  className="flex gap-3"
                >

                  <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-blue-500" />

                  <div>

                    <p className="text-sm text-slate-200">
                      {item.label}
                    </p>

                    {item.actor !== null && (
                      <p className="mt-1 text-xs text-slate-500">
                        User ID: {item.actor}
                      </p>
                    )}

                    <p className="mt-1 text-xs text-slate-500">
                      {formatDateTime(item.date)}
                    </p>

                  </div>

                </div>

              ))}

            </div>

          </section>

        </div>

      </div>


      {/* FULL AUDIT EVENT HISTORY */}

      <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

        <h2 className="font-semibold text-white">
          Audit event history
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          Recorded actions for this invoice.
        </p>

        <div className="mt-5 space-y-3">

          {events.map(event => (

            <div
              key={event.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 p-4"
            >

              <div>

                <p className="text-sm font-medium text-white">
                  {event.action.replaceAll("_", " ")}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Actor ID: {event.actor_id ?? "System"}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {formatDateTime(event.created_at)}
                </p>

              </div>

              <span className={`text-xs font-semibold ${
                event.outcome === "SUCCESS"
                  ? "text-emerald-400"
                  : "text-red-400"
              }`}>
                {event.outcome}
              </span>

            </div>

          ))}

          {events.length === 0 && (

            <p className="py-4 text-sm text-slate-500">
              No audit events recorded yet.
            </p>

          )}

        </div>

      </section>

    </div>

  );

}