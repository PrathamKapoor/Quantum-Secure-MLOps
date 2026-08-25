import { Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import ErrorBoundary from "./components/ErrorBoundary";
import Overview from "./pages/Overview";
import Forecasting from "./pages/Forecasting";
import Models from "./pages/Models";
import DriftMonitoring from "./pages/DriftMonitoring";
import Governance from "./pages/Governance";
import AgentAssistant from "./pages/AgentAssistant";
import DemoMode from "./pages/DemoMode";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-100 px-8 py-6">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/forecasting" element={<Forecasting />} />
            <Route path="/models" element={<Models />} />
            <Route path="/drift" element={<DriftMonitoring />} />
            <Route path="/governance" element={<Governance />} />
            <Route path="/agent" element={<AgentAssistant />} />
            <Route path="/demo" element={<DemoMode />} />
            <Route path="/reports" element={<Reports />} />
            <Route
              path="*"
              element={<p className="text-sm text-slate-500">Page not found.</p>}
            />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
