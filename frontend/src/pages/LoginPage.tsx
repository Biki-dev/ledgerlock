import {
  useState,
  type FormEvent
} from "react";

import {
  ShieldCheck,
  LockKeyhole
} from "lucide-react";

import {
  useNavigate
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import { getErrorMessage } from "../utils/format";


export default function LoginPage() {

  const { login } = useAuth();

  const navigate = useNavigate();

  const [email, setEmail] = useState(
    "reviewer@ledgerlock.demo"
  );

  const [password, setPassword] = useState(
    "Review123!"
  );

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  async function handleSubmit(
    event: FormEvent
  ) {

    event.preventDefault();

    setLoading(true);
    setError("");

    try {

      await login(email, password);

      navigate("/", { replace: true });

    } catch (err) {

      setError(getErrorMessage(err));

    } finally {

      setLoading(false);

    }
  }


  return (

    <div className="flex min-h-screen items-center justify-center bg-[#080d18] p-5">

      <div className="w-full max-w-md">

        <div className="mb-8 text-center">

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-500/20 bg-blue-500/10">

            <ShieldCheck
              size={28}
              className="text-blue-400"
            />

          </div>

          <h1 className="mt-5 text-3xl font-bold text-white">
            Ledger<span className="text-blue-500">Lock</span>
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Secure your accounts payable workflow.
          </p>

        </div>


        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-slate-800 bg-[#111827] p-7 shadow-2xl"
        >

          <h2 className="text-xl font-semibold text-white">
            Welcome back
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Sign in to your finance workspace.
          </p>


          {error && (

            <div className="mt-5 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
              {error}
            </div>

          )}


          <div className="mt-6 space-y-4">

            <div>

              <label className="mb-2 block text-sm text-slate-300">
                Email address
              </label>

              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-700 bg-[#080d18] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              />

            </div>


            <div>

              <label className="mb-2 block text-sm text-slate-300">
                Password
              </label>

              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-lg border border-slate-700 bg-[#080d18] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              />

            </div>


            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
            >

              <LockKeyhole size={17} />

              {loading ? "Signing in..." : "Sign in"}

            </button>

          </div>


          <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900 p-3">

            <p className="text-xs font-medium text-slate-300">
              Demo accounts
            </p>

            <p className="mt-2 text-[11px] leading-5 text-slate-500">
              Reviewer: reviewer@ledgerlock.demo
              <br />
              Approver: approver@ledgerlock.demo
              <br />
              Admin: admin@ledgerlock.demo
              <br />
              Passwords are configured in your backend .env.
            </p>

          </div>

        </form>

      </div>

    </div>

  );
}