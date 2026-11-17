import {
  useCallback,
  useEffect,
  useState
} from "react";

import {
  FlaskConical,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock3,
  ExternalLink,
  Copy,
  Bot,
  ShieldCheck
} from "lucide-react";

import api from "../services/api";

import type {
  AssuranceRun,
  AssuranceScenario,
  Invoice
} from "../types";

import StatusBadge from "../components/common/StatusBadge";

import Loading from "../components/common/Loading";

import {
  formatDateTime,
  formatCurrency
} from "../utils/format";


const agentStatusMeaning: Record<AssuranceRun["agent_status"], string> = {
  NOT_STARTED: "No failure feedback generated.",
  READY: "Repair prompt generated.",
  RUNNING: "Coding agent working.",
  COMPLETED: "Agent process finished successfully; retest is still required.",
  FAILED: "Agent process returned failure.",
};


export default function AssuranceLabPage() {

  const [scenarios, setScenarios] = useState<
    AssuranceScenario[]
  >([]);

  const [invoices, setInvoices] = useState<Invoice[]>([]);

  const [runs, setRuns] = useState<AssuranceRun[]>([]);

  const [selectedInvoice, setSelectedInvoice] = useState("");

  const [selectedScenario, setSelectedScenario] = useState(
    "bank_change_approval_guard"
  );

  const [selectedRun, setSelectedRun] = useState<number | null>(
    null
  );

  const [loading, setLoading] = useState(true);

  const [starting, setStarting] = useState(false);

  const [error, setError] = useState("");

  const [message, setMessage] = useState("");


  const activeRun = runs.find(
    run => run.id === selectedRun
  ) || null;


  const loadData = useCallback(async () => {

    try {

      const [
        scenariosResponse,
        invoicesResponse,
        runsResponse
      ] = await Promise.all([

        api.get<AssuranceScenario[]>(
          "/api/assurance/scenarios"
        ),

        api.get<Invoice[]>(
          "/api/invoices"
        ),

        api.get<{ runs: AssuranceRun[]; total: number }>(
          "/api/assurance/runs?limit=50"
        )

      ]);


      setScenarios(scenariosResponse.data);

      setInvoices(invoicesResponse.data);

      setRuns(runsResponse.data.runs);

      setSelectedInvoice(previous => {

        if (
          previous &&
          invoicesResponse.data.some(
            invoice => String(invoice.id) === previous
          )
        ) {
          return previous;
        }

        return "";
      });

    } catch {

      setError("Unable to load Assurance Lab.");

    } finally {

      setLoading(false);

    }

  }, []);


  useEffect(() => {

    void Promise.resolve().then(loadData);

    const timer = window.setInterval(() => {
      loadData();
    }, 3000);

    return () => window.clearInterval(timer);

  }, [loadData]);


  async function startRun(
    retestOfRunId?: number
  ) {

    const previousRun = retestOfRunId
      ? runs.find(run => run.id === retestOfRunId)
      : null;

    if (retestOfRunId && !previousRun) {
      setError("The failed run is no longer available for retesting.");
      return;
    }

    const invoiceId = previousRun
      ? previousRun.invoice_id
      : Number(selectedInvoice);

    const scenarioCode = previousRun
      ? previousRun.scenario_code
      : selectedScenario;

    if (!invoiceId) {

      setError("Select an invoice first.");

      return;
    }

    setStarting(true);

    setError("");
    setMessage("");

    try {

      if (previousRun) {
        setSelectedInvoice(String(previousRun.invoice_id));
        setSelectedScenario(previousRun.scenario_code);
      }

      const { data } = await api.post<AssuranceRun>(
        "/api/assurance/runs",
        {

          invoice_id: invoiceId,

          scenario_code: scenarioCode,

          retest_of_run_id: retestOfRunId ?? null

        }
      );

      setSelectedRun(data.id);

      setMessage("Kane execution started.");

      await loadData();

    } catch (err) {

      const message =
        (err as {
          response?: {
            data?: {
              detail?: string;
            };
          };
        }).response?.data?.detail;

      setError(message || "Unable to start Kane execution.");

    } finally {

      setStarting(false);

    }

  }


  async function copyCommand(
    runId: number
  ) {

    const command =
      `python scripts/repair_from_kane.py ${runId}`;

    await navigator.clipboard.writeText(command);

    setMessage("Repair command copied.");

  }


  const pendingRuns = runs.filter(
    run => ["QUEUED", "RUNNING"].includes(run.status)
  );


  if (loading) return <Loading />;


  return (

    <div className="space-y-7">


      {/* HEADER */}

      <div className="flex flex-wrap items-center justify-between gap-4">

        <div>

          <div className="flex items-center gap-2">

            <FlaskConical
              className="text-blue-400"
              size={22}
            />

            <h1 className="text-2xl font-bold text-white">
              Kane Assurance Lab
            </h1>

          </div>

          <p className="mt-2 text-sm text-slate-500">
            Independently verify LedgerLock's invoice approval workflow.
          </p>

        </div>


        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">

          <span className="h-2 w-2 rounded-full bg-emerald-400" />

          <span className="text-xs text-emerald-400">
            Kane integration enabled
          </span>

        </div>

      </div>


      {/* MESSAGE */}

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


      {/* TOP STATS */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">


        {[
          {
            title: "Total runs",
            value: runs.length,
            color: "text-white",
            icon: FlaskConical
          },

          {
            title: "Passed",
            value: runs.filter(r => r.status === "PASSED").length,
            color: "text-emerald-400",
            icon: CheckCircle2
          },

          {
            title: "Failed",
            value: runs.filter(r => r.status === "FAILED").length,
            color: "text-red-400",
            icon: XCircle
          },

          {
            title: "Running",
            value: pendingRuns.length,
            color: "text-blue-400",
            icon: Clock3
          }

        ].map(stat => (

          <div
            key={stat.title}
            className="rounded-xl border border-slate-800 bg-[#111827] p-5"
          >

            <div className="flex items-center justify-between">

              <p className="text-sm text-slate-500">
                {stat.title}
              </p>

              <stat.icon
                size={19}
                className={stat.color}
              />

            </div>

            <h2 className={`mt-4 text-3xl font-bold ${stat.color}`}>
              {stat.value}
            </h2>

          </div>

        ))}

      </div>


      {/* CREATE RUN */}

      <div className="grid gap-5 xl:grid-cols-[1fr_350px]">


        <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

          <div className="flex items-center gap-2">

            <ShieldCheck
              size={19}
              className="text-blue-400"
            />

            <h2 className="font-semibold text-white">
              Run verification
            </h2>

          </div>

          <p className="mt-2 text-xs text-slate-500">
            Choose an invoice and execute a predefined Kane scenario.
          </p>


          <div className="mt-6 space-y-5">


            <div>

              <label className="mb-2 block text-sm text-slate-300">
                Select invoice
              </label>

              <select
                value={selectedInvoice}
                onChange={e => setSelectedInvoice(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-[#080d18] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              >

                <option value="">
                  Choose invoice...
                </option>

                {invoices.filter(
                  invoice => invoice.approval_status === "PENDING"
                ).map(invoice => (

                  <option
                    key={invoice.id}
                    value={invoice.id}
                  >

                    #{invoice.id} ·
                    {invoice.vendor_name || "Unknown vendor"} ·
                    {invoice.risk_status} ·
                    {formatCurrency(invoice.total)}

                  </option>

                ))}

              </select>

            </div>


            <div>

              <label className="mb-2 block text-sm text-slate-300">
                Select scenario
              </label>

              <div className="grid gap-3 sm:grid-cols-2">

                {scenarios.map(scenario => (

                  <button
                    key={scenario.code}
                    onClick={() => setSelectedScenario(scenario.code)}
                    className={`rounded-xl border p-4 text-left transition ${
                      selectedScenario === scenario.code
                        ? "border-blue-500 bg-blue-500/10"
                        : "border-slate-700 bg-slate-900 hover:border-slate-500"
                    }`}
                  >

                    <p className="text-sm font-semibold text-white">
                      {scenario.title}
                    </p>

                    <p className="mt-2 text-xs leading-5 text-slate-500">
                      {scenario.description}
                    </p>

                    <div className="mt-3">
                      <StatusBadge status={scenario.required_risk_status} />
                    </div>

                  </button>

                ))}

              </div>

            </div>


            <button
              onClick={() => startRun()}
              disabled={starting || pendingRuns.length > 0 || !selectedInvoice}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-3 font-semibold text-white hover:bg-blue-500"
            >

              {starting
                ? <RefreshCw className="animate-spin" size={17} />
                : <Play size={17} />
              }

              {pendingRuns.length > 0
                ? "Another Kane run is active"
                : "Run Kane verification"
              }

            </button>


          </div>

        </section>


        {/* ACTIVE RUN */}

        <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

          <h2 className="font-semibold text-white">
            Execution status
          </h2>

          {!activeRun ? (

            <div className="py-12 text-center">

              <FlaskConical
                size={32}
                className="mx-auto text-slate-600"
              />

              <p className="mt-4 text-sm text-slate-400">
                Select a run to view its results.
              </p>

            </div>

          ) : (

            <div className="mt-6 space-y-4">

              <p className="text-xs text-slate-500">
                RUN #{activeRun.id}
              </p>

              <StatusBadge status={activeRun.status} />

              <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                <p className="text-xs text-slate-500">AI coding agent</p>
                <div className="mt-2">
                  <StatusBadge status={activeRun.agent_status} />
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  {agentStatusMeaning[activeRun.agent_status]}
                </p>
                {activeRun.agent_feedback_path && (
                  <p className="mt-2 break-all text-xs text-slate-500">
                    {activeRun.agent_feedback_path}
                  </p>
                )}
                <p className="mt-2 text-xs text-slate-500">
                  Completed means the agent process finished; only a passing Kane retest confirms the issue is fixed.
                </p>
              </div>

              <h3 className="text-lg font-semibold text-white">
                {activeRun.scenario_title}
              </h3>

              <p className="text-sm leading-6 text-slate-400">
                {activeRun.summary || activeRun.reason || "Waiting for Kane..."}
              </p>

              {activeRun.duration_seconds !== null && (

                <p className="text-xs text-slate-500">
                  Duration: {activeRun.duration_seconds.toFixed(1)} seconds
                </p>

              )}

              {activeRun.credits_consumed !== null && (

                <p className="text-xs text-slate-500">
                  Credits: {activeRun.credits_consumed}
                </p>

              )}


              {activeRun.test_url && (

                <a
                  href={activeRun.test_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
                >
                  Open Kane Test Manager
                  <ExternalLink size={15} />
                </a>

              )}


              {activeRun.evidence_path && (

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">

                  <p className="text-xs text-slate-500">
                    Local evidence pack
                  </p>

                  <p className="mt-2 break-all text-xs text-slate-300">
                    {activeRun.evidence_path}
                  </p>

                  <p className="mt-3 text-[11px] text-slate-500">
                    Run kane-cli evidence serve with this path to open it.
                  </p>

                </div>

              )}


              {activeRun.status === "FAILED" && (

                <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">

                  <div className="flex items-center gap-2">

                    <Bot
                      size={18}
                      className="text-red-400"
                    />

                    <p className="text-sm font-semibold text-white">
                      Agent repair available
                    </p>

                  </div>

                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    Send this failure report to your coding agent.
                  </p>

                  <button
                    onClick={() => copyCommand(activeRun.id)}
                    className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700 py-2 text-xs text-slate-200 hover:bg-slate-800"
                  >
                    <Copy size={14} />
                    Copy repair command
                  </button>

                  <button
                    onClick={() => startRun(activeRun.id)}
                    disabled={starting || pendingRuns.length > 0}
                    className="mt-3 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Run same scenario again
                  </button>

                </div>

              )}


              {activeRun.status === "PASSED" && (

                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">

                  <CheckCircle2
                    size={20}
                    className="text-emerald-400"
                  />

                  <p className="mt-2 text-sm font-semibold text-emerald-400">
                    Browser verification passed.
                  </p>

                </div>

              )}

            </div>

          )}

        </section>

      </div>


      {/* STEP RESULTS */}

      {activeRun && (

        <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

          <h2 className="font-semibold text-white">
            Kane execution steps
          </h2>

          <div className="mt-5 space-y-3">

            {activeRun.step_events.map((step, index) => (

              <div
                key={index}
                className="flex items-start gap-3 rounded-lg border border-slate-800 p-3"
              >

                {step.status === "failed" ? (

                  <XCircle
                    size={17}
                    className="mt-0.5 text-red-400"
                  />

                ) : (

                  <CheckCircle2
                    size={17}
                    className="mt-0.5 text-emerald-400"
                  />

                )}

                <div>

                  <p className="text-xs text-slate-500">
                    Step {step.step ?? index + 1}
                  </p>

                  <p className="mt-1 text-sm text-slate-300">
                    {step.remark || step.status}
                  </p>

                </div>

              </div>

            ))}

            {!activeRun.step_events.length && (

              <p className="py-5 text-sm text-slate-500">
                No execution steps recorded yet.
              </p>

            )}

          </div>

        </section>

      )}


      {/* RUN HISTORY */}

      <section className="rounded-xl border border-slate-800 bg-[#111827] p-5">

        <h2 className="font-semibold text-white">
          Run history
        </h2>

        <div className="mt-5 space-y-3">

          {runs.map(run => (

            <button
              key={run.id}
              onClick={() => setSelectedRun(run.id)}
              className={`flex w-full flex-wrap items-center justify-between gap-3 rounded-lg border p-4 text-left transition ${
                selectedRun === run.id
                  ? "border-blue-500 bg-blue-500/5"
                  : "border-slate-800 hover:bg-slate-800/40"
              }`}
            >

              <div>

                <p className="text-sm font-medium text-white">
                  {run.scenario_title}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Run #{run.id} · Invoice #{run.invoice_id}
                </p>

                <p className="mt-1 text-[11px] text-slate-600">
                  {formatDateTime(run.created_at)}
                </p>

                {run.retest_of_run_id && (

                  <p className="mt-1 text-[11px] text-blue-400">
                    Retest of #{run.retest_of_run_id}
                  </p>

                )}

              </div>


              <StatusBadge status={run.status} />

            </button>

          ))}

          {!runs.length && (

            <p className="py-8 text-center text-sm text-slate-500">
              No Kane runs yet.
            </p>

          )}

        </div>

      </section>

    </div>

  );

}