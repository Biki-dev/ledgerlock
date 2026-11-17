import type {
  RiskStatus,
  ApprovalStatus
} from "../../types";

type Status =
  | RiskStatus
  | ApprovalStatus
  | "PENDING"
  | "CLEARED"
  | "VERIFIED";

const styles: Record<string, string> = {
  CLEAR: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

  REVIEW: "bg-amber-500/10 text-amber-400 border-amber-500/20",

  HOLD: "bg-red-500/10 text-red-400 border-red-500/20",

  APPROVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

  REJECTED: "bg-red-500/10 text-red-400 border-red-500/20",

  PENDING: "bg-blue-500/10 text-blue-400 border-blue-500/20",

  CLEARED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

  VERIFIED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
};

export default function StatusBadge({
  status
}: {
  status: Status | string;
}) {

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide ${
        styles[status] ||
        "border-slate-700 bg-slate-800 text-slate-300"
      }`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}