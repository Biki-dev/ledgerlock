import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  description: string;
  icon: LucideIcon;
  color: string;
}

export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
  color
}: Props) {

  return (
    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">

      <div className="flex items-start justify-between">

        <div>
          <p className="text-sm text-slate-400">
            {title}
          </p>

          <h2 className="mt-3 text-3xl font-semibold text-white">
            {value}
          </h2>

          <p className="mt-2 text-xs text-slate-500">
            {description}
          </p>
        </div>

        <div className={`rounded-lg p-3 ${color}`}>
          <Icon size={21} />
        </div>

      </div>

    </div>
  );
}