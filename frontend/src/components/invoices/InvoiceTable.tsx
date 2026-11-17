import {
  Link
} from "react-router-dom";

import {
  ArrowUpRight
} from "lucide-react";

import type { Invoice } from "../../types";

import StatusBadge from "../common/StatusBadge";

import {
  formatCurrency,
  formatDate
} from "../../utils/format";


export default function InvoiceTable({
  invoices
}: {
  invoices: Invoice[];
}) {

  return (

    <div className="overflow-x-auto">

      <table className="w-full min-w-[850px] text-left">

        <thead>

          <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">

            <th className="px-4 py-4 font-medium">
              Invoice
            </th>

            <th className="px-4 py-4 font-medium">
              Vendor
            </th>

            <th className="px-4 py-4 font-medium">
              Date
            </th>

            <th className="px-4 py-4 font-medium">
              Amount
            </th>

            <th className="px-4 py-4 font-medium">
              Risk
            </th>

            <th className="px-4 py-4 font-medium">
              Approval
            </th>

            <th className="px-4 py-4">
            </th>

          </tr>

        </thead>


        <tbody>

          {invoices.map(invoice => (

            <tr
              key={invoice.id}
              className="border-b border-slate-800/70 transition hover:bg-slate-800/30"
            >

              <td className="px-4 py-4">

                <Link
                  to={`/invoices/${invoice.id}`}
                  className="font-medium text-white hover:text-blue-400"
                >
                  {invoice.invoice_number || `INV-${invoice.id}`}
                </Link>

                <p className="mt-1 text-[11px] text-slate-500">
                  ID #{invoice.id}
                </p>

              </td>


              <td className="px-4 py-4 text-sm text-slate-300">
                {invoice.vendor_name || "Unknown vendor"}
              </td>


              <td className="px-4 py-4 text-sm text-slate-400">
                {formatDate(invoice.invoice_date)}
              </td>


              <td className="px-4 py-4 text-sm font-medium text-white">
                {formatCurrency(invoice.total)}
              </td>


              <td className="px-4 py-4">
                <StatusBadge status={invoice.risk_status} />
              </td>


              <td className="px-4 py-4">
                <StatusBadge status={invoice.approval_status} />
              </td>


              <td className="px-4 py-4">

                <Link
                  to={`/invoices/${invoice.id}`}
                  className="inline-flex rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white"
                >
                  <ArrowUpRight size={17} />
                </Link>

              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>

  );
}