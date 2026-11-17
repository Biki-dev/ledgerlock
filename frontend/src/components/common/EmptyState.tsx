import { FileSearch } from "lucide-react";

export default function EmptyState({
  title,
  description
}: {
  title: string;
  description: string;
}) {

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 py-16 text-center">

      <FileSearch
        size={36}
        className="text-slate-500"
      />

      <h3 className="mt-4 font-medium text-white">
        {title}
      </h3>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>

    </div>
  );
}