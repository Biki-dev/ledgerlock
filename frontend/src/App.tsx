import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import ProtectedRoute from "./components/common/ProtectedRoute";

import AppLayout from "./components/layout/AppLayout";

import LoginPage from "./pages/LoginPage";

import DashboardPage from "./pages/DashboardPage";

import InvoiceQueuePage from "./pages/InvoiceQueuePage";

import InvoiceDetailsPage from "./pages/InvoiceDetailsPage";

import AuditHistoryPage from "./pages/AuditHistoryPage";

import AssuranceLabPage from "./pages/AssuranceLabPage";

function ProtectedLayout({
  children
}: {
  children: React.ReactNode;
}) {

  return (

    <ProtectedRoute>

      <AppLayout>
        {children}
      </AppLayout>

    </ProtectedRoute>

  );
}


export default function App() {

  return (

    <BrowserRouter>

      <AuthProvider>

        <Routes>

          <Route
            path="/login"
            element={<LoginPage />}
          />

          <Route
            path="/"
            element={
              <ProtectedLayout>
                <DashboardPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/invoices"
            element={
              <ProtectedLayout>
                <InvoiceQueuePage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/invoices/:id"
            element={
              <ProtectedLayout>
                <InvoiceDetailsPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/audit"
            element={
              <ProtectedLayout>
                <AuditHistoryPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />

          <Route
            path="/assurance"
            element={
              <ProtectedLayout>
                <AssuranceLabPage />
              </ProtectedLayout>
            }
          />

        </Routes>

      </AuthProvider>

    </BrowserRouter>

  );
}