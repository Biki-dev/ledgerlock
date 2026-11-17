import {
  useRef,
  useState,
  type ChangeEvent
} from "react";

import {
  Upload,
  FileText,
  LoaderCircle
} from "lucide-react";

import {
  useNavigate
} from "react-router-dom";

import api from "../../services/api";

import type { Invoice } from "../../types";

import { getErrorMessage } from "../../utils/format";


export default function UploadInvoice() {

  const navigate = useNavigate();

  const inputRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [progress, setProgress] = useState(0);


  async function handleFile(
    event: ChangeEvent<HTMLInputElement>
  ) {

    const file = event.target.files?.[0];

    if (!file) return;

    setError("");
    setProgress(0);

    if (!file.name.toLowerCase().endsWith(".pdf")) {

      setError("Only PDF files are supported.");

      event.target.value = "";

      return;
    }

    if (file.size > 10 * 1024 * 1024) {

      setError("Maximum upload size is 10 MB.");

      event.target.value = "";

      return;
    }

    const formData = new FormData();

    formData.append("file", file);

    setLoading(true);

    try {

      const { data } = await api.post<Invoice>(
        "/api/invoices/upload",
        formData,
        {
          onUploadProgress: (event) => {

            if (event.total) {
              setProgress(
                Math.round(
                  event.loaded / event.total * 100
                )
              );
            }
          }
        }
      );

      // Open the newly uploaded invoice.

      navigate(`/invoices/${data.id}`);

    } catch (err) {

      setError(getErrorMessage(err));

    } finally {

      setLoading(false);

      if (inputRef.current) {
        inputRef.current.value = "";
      }

    }
  }


  return (

    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5">

      <div className="flex items-center gap-3">

        <div className="rounded-lg bg-blue-500/10 p-3">
          <FileText className="text-blue-400" />
        </div>

        <div>
          <h3 className="font-semibold text-white">
            Upload an invoice
          </h3>

          <p className="mt-1 text-xs text-slate-500">
            PDF only · Maximum 10 MB
          </p>
        </div>

      </div>


      <button
        onClick={() => inputRef.current?.click()}
        disabled={loading}
        className="mt-5 flex w-full flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/60 px-4 py-8 transition hover:border-blue-500 hover:bg-blue-500/5"
      >

        {loading ? (

          <LoaderCircle
            size={28}
            className="animate-spin text-blue-400"
          />

        ) : (

          <Upload
            size={28}
            className="text-blue-400"
          />

        )}

        <p className="mt-3 text-sm font-medium text-slate-200">
          {loading ? "Processing invoice..." : "Click to upload PDF"}
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Invoice extraction and risk analysis
        </p>

        {loading && (

          <div className="mt-4 h-1.5 w-full rounded-full bg-slate-800">

            <div
              className="h-1.5 rounded-full bg-blue-500 transition-all"
              style={{ width: `${progress}%` }}
            />

          </div>

        )}

      </button>


      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFile}
        className="hidden"
      />


      {error && (

        <p className="mt-3 text-sm text-red-400">
          {error}
        </p>

      )}

    </div>

  );
}