
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const REFRESH_MS = 15000;
const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

const COLORS = {
  CRITICAL: "#fb7185",
  HIGH: "#fb923c",
  MEDIUM: "#facc15",
  LOW: "#34d399",
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || `HTTP ${response.status}`;
    const error = new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail)
    );
    error.status = response.status;
    throw error;
  }

  return data;
}

function show(value, fallback = "Not available") {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }
  return typeof value === "object"
    ? JSON.stringify(value, null, 2)
    : String(value);
}

function dateText(value) {
  if (!value) return "Not available";
  const input =
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T/.test(value) &&
    !/(Z|[+-]\d{2}:\d{2})$/i.test(value)
      ? `${value}Z`
      : value;
  const date = new Date(input);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function Badge({ value }) {
  const name = show(value, "UNKNOWN");
  const color =
    COLORS[name] ||
    ({
      APPROVED: "#34d399",
      REJECTED: "#fb7185",
      PENDING: "#facc15",
      SIMULATED: "#34d399",
      NEW: "#60a5fa",
      OPEN: "#60a5fa",
      COMPLETED: "#34d399",
    }[name] || "#cbd5e1");

  return (
    <span className="badge" style={{ color, borderColor: `${color}70` }}>
      <span className="badge-dot" style={{ background: color }} />
      {name}
    </span>
  );
}

function SectionTitle({ eyebrow, title, description }) {
  return (
    <div className="section-title">
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
  );
}

function Stat({ label, value, color, description }) {
  return (
    <div className="stat panel">
      <span>{label}</span>
      <strong style={{ color: color || "#f3f6ff" }}>{value}</strong>
      <small>{description}</small>
    </div>
  );
}

function SeverityChart({ incidents }) {
  return (
    <div className="bars">
      {SEVERITIES.map((severity) => {
        const count = incidents.filter(
          (x) => String(x.severity).toUpperCase() === severity
        ).length;
        const width = incidents.length ? (count / incidents.length) * 100 : 0;

        return (
          <div className="bar-line" key={severity}>
            <span>{severity}</span>
            <div className="track">
              <div
                className="fill"
                style={{ width: `${width}%`, background: COLORS[severity] }}
              />
            </div>
            <strong>{count}</strong>
          </div>
        );
      })}
    </div>
  );
}

function StatusChart({ incidents }) {
  const counts = {};

  incidents.forEach((incident) => {
    const status = String(incident.status || "UNKNOWN").toUpperCase();
    counts[status] = (counts[status] || 0) + 1;
  });

  const palette = ["#38bdf8", "#a78bfa", "#34d399", "#facc15", "#fb7185"];
  const entries = Object.entries(counts);
  let previous = 0;

  const gradient = entries
    .map(([name, count], i) => {
      const start = previous;
      previous += incidents.length ? (count / incidents.length) * 100 : 0;
      return `${palette[i % palette.length]} ${start}% ${previous}%`;
    })
    .join(",");

  return (
    <div className="donut-layout">
      <div
        className="donut"
        style={{ background: gradient ? `conic-gradient(${gradient})` : "#27364d" }}
      >
        <div className="donut-inner">
          <strong>{incidents.length}</strong>
          <small>INCIDENTS</small>
        </div>
      </div>

      <div className="legend">
        {entries.length ? entries.map(([name, count], i) => (
          <div key={name}>
            <span style={{ background: palette[i % palette.length] }} />
            {name}
            <strong>{count}</strong>
          </div>
        )) : <p>No incidents recorded.</p>}
      </div>
    </div>
  );
}

function LoginScreen({ onLogin }) {
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!password || submitting) return;

    setSubmitting(true);
    setError("");

    try {
      await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      setPassword("");
      await onLogin();
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card panel">
        <div className="login-logo">N</div>
        <span className="eyebrow">Protected Operations Workspace</span>
        <h1>NEXUS AI</h1>
        <p>Operations & Incident Intelligence Platform</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="admin-password">Administrator Password</label>
          <input
            id="admin-password"
            className="input"
            type="password"
            autoComplete="current-password"
            placeholder="Enter administrator password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <div className="alert" role="alert">{error}</div>}

          <button
            className="btn primary login-button"
            type="submit"
            disabled={submitting || !password}
          >
            {submitting ? "Signing in..." : "Secure Sign In →"}
          </button>
        </form>

        <small className="login-foot">
          Authorized administrators only · Session-based authentication
        </small>
      </div>
    </div>
  );
}

function App() {
  const [auth, setAuth] = useState({
    loading: true,
    enabled: false,
    authenticated: false,
  });
  const [authError, setAuthError] = useState("");

  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const [selected, setSelected] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");

  const [workflow, setWorkflow] = useState(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowError, setWorkflowError] = useState("");
  const [workflowMessage, setWorkflowMessage] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const [aiReport, setAiReport] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiRunning, setAiRunning] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiMessage, setAiMessage] = useState("");

  const fetchingRef = useRef(false);
  const versionRef = useRef(0);
  const mountedRef = useRef(true);

  function handleUnauthorized(err) {
    if (err?.status === 401) {
      versionRef.current += 1;
      setSelected(null);
      setWorkflow(null);
      setAiReport(null);
      setAuth((prev) => ({ ...prev, authenticated: false }));
      return true;
    }
    return false;
  }

  const checkAuth = useCallback(async () => {
    setAuthError("");

    try {
      const data = await api("/api/auth/me");

      if (!mountedRef.current) return;

      setAuth({
        loading: false,
        enabled: Boolean(data.auth_enabled),
        authenticated: Boolean(data.authenticated),
      });
    } catch (err) {
      if (mountedRef.current) {
        setAuthError(err.message);
        setAuth((prev) => ({ ...prev, loading: false }));
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    checkAuth();

    return () => {
      mountedRef.current = false;
      versionRef.current += 1;
    };
  }, [checkAuth]);

  const canAccess = !auth.loading && (!auth.enabled || auth.authenticated);

  const loadIncidents = useCallback(async (initial = false) => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;

    if (initial) setLoading(true);
    else setRefreshing(true);

    try {
      const data = await api("/api/incidents");
      if (!mountedRef.current) return;

      setIncidents(Array.isArray(data.incidents) ? data.incidents : []);
      setLastUpdated(new Date().toISOString());
      setError("");
    } catch (err) {
      if (mountedRef.current) {
        if (err.status === 401) {
          versionRef.current += 1;
          setSelected(null);
          setAuth((prev) => ({ ...prev, authenticated: false }));
        } else {
          setError(err.message);
        }
      }
    } finally {
      fetchingRef.current = false;
      if (mountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    if (!canAccess) return;
    loadIncidents(true);
  }, [canAccess, loadIncidents]);

  useEffect(() => {
    if (!canAccess || !autoRefresh) return;

    const timer = setInterval(() => {
      if (document.visibilityState === "visible") loadIncidents();
    }, REFRESH_MS);

    return () => clearInterval(timer);
  }, [canAccess, autoRefresh, loadIncidents]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();

    return incidents.filter((incident) => {
      const severityMatch =
        severityFilter === "ALL" ||
        String(incident.severity).toUpperCase() === severityFilter;

      const searchMatch =
        !term ||
        [incident.id, incident.service, incident.status, incident.severity]
          .some((value) => String(value || "").toLowerCase().includes(term));

      return severityMatch && searchMatch;
    });
  }, [incidents, search, severityFilter]);

  const stats = useMemo(() => ({
    total: incidents.length,
    critical: incidents.filter((x) => x.severity === "CRITICAL").length,
    high: incidents.filter((x) => x.severity === "HIGH").length,
    active: incidents.filter((x) => x.status !== "RESOLVED").length,
  }), [incidents]);

  const recentActivity = useMemo(
    () => [...incidents]
      .sort((a, b) => new Date(b.detected_at || 0) - new Date(a.detected_at || 0))
      .slice(0, 5),
    [incidents]
  );

  async function logout() {
    try {
      await api("/api/auth/logout", { method: "POST" });
      versionRef.current += 1;
      setSelected(null);
      setWorkflow(null);
      setAiReport(null);
      setIncidents([]);
      await checkAuth();
    } catch (err) {
      setAuthError(err.message);
    }
  }

  async function loadWorkflow(id, version) {
    setWorkflowLoading(true);
    setWorkflowError("");

    try {
      const data = await api(`/api/incidents/${encodeURIComponent(id)}/workflow`);

      if (version === versionRef.current && mountedRef.current) {
        setWorkflow(data);
      }
    } catch (err) {
      if (version === versionRef.current && mountedRef.current) {
        if (!handleUnauthorized(err)) setWorkflowError(err.message);
      }
    } finally {
      if (version === versionRef.current && mountedRef.current) {
        setWorkflowLoading(false);
      }
    }
  }

  async function loadAIReport(id, version) {
    setAiLoading(true);
    setAiError("");

    try {
      const data = await api(
        `/api/incidents/${encodeURIComponent(id)}/investigation-report`
      );

      if (version === versionRef.current && mountedRef.current) {
        setAiReport(data.status === "AVAILABLE" ? data.report : null);
      }
    } catch (err) {
      if (version === versionRef.current && mountedRef.current) {
        if (!handleUnauthorized(err)) setAiError(err.message);
      }
    } finally {
      if (version === versionRef.current && mountedRef.current) {
        setAiLoading(false);
      }
    }
  }

  async function openIncident(id) {
    const version = ++versionRef.current;

    setSelected(null);
    setWorkflow(null);
    setAiReport(null);
    setReviewer("");
    setWorkflowError("");
    setWorkflowMessage("");
    setDetailsError("");
    setAiError("");
    setAiMessage("");
    setDetailsLoading(true);

    try {
      const data = await api(`/api/incidents/${encodeURIComponent(id)}`);

      if (version !== versionRef.current || !mountedRef.current) return;

      setSelected(data);

      await Promise.all([
        loadWorkflow(id, version),
        loadAIReport(id, version),
      ]);
    } catch (err) {
      if (version === versionRef.current && mountedRef.current) {
        if (!handleUnauthorized(err)) setDetailsError(err.message);
      }
    } finally {
      if (version === versionRef.current && mountedRef.current) {
        setDetailsLoading(false);
      }
    }
  }

  function closeIncident() {
    versionRef.current += 1;
    setSelected(null);
    setWorkflow(null);
    setAiReport(null);
    setDetailsError("");
    setWorkflowError("");
    setWorkflowMessage("");
    setAiError("");
    setAiMessage("");
    setDetailsLoading(false);
    setWorkflowLoading(false);
    setAiLoading(false);
  }

  async function runInvestigation() {
    const id = selected?.incident?.id;
    if (!id || aiRunning) return;

    const version = versionRef.current;
    setAiRunning(true);
    setAiError("");
    setAiMessage("");

    try {
      const result = await api(
        `/api/incidents/${encodeURIComponent(id)}/investigate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "DETERMINISTIC" }),
        }
      );

      if (version !== versionRef.current || !mountedRef.current) return;

      if (result.status !== "INVESTIGATION_COMPLETED") {
        throw new Error("Investigation did not complete.");
      }

      setAiReport(result.report);
      setAiMessage("Investigation completed and saved successfully.");

      const updated = await api(`/api/incidents/${encodeURIComponent(id)}`);

      if (version === versionRef.current && mountedRef.current) {
        setSelected(updated);
        loadIncidents();
      }
    } catch (err) {
      if (version === versionRef.current && mountedRef.current) {
        if (!handleUnauthorized(err)) setAiError(err.message);
      }
    } finally {
      if (mountedRef.current) setAiRunning(false);
    }
  }

  async function submitAction(action) {
    const id = selected?.incident?.id;
    if (!id || actionLoading || !workflow) return;

    const simulate = action === "SIMULATE";

    if (!simulate && reviewer.trim().length < 2) {
      setWorkflowError("Enter a reviewer name (at least 2 characters).");
      return;
    }

    const version = versionRef.current;
    setActionLoading(true);
    setWorkflowError("");
    setWorkflowMessage("");

    try {
      const path = simulate
        ? `/api/incidents/${encodeURIComponent(id)}/remediation/simulate`
        : `/api/incidents/${encodeURIComponent(id)}/approval`;

      await api(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          simulate ? {} : { decision: action, reviewer: reviewer.trim() }
        ),
      });

      if (version === versionRef.current && mountedRef.current) {
        setWorkflowMessage(
          simulate
            ? "Safe simulation recorded. No infrastructure was changed."
            : "Human approval decision recorded."
        );
        await loadWorkflow(id, version);
      }
    } catch (err) {
      if (version === versionRef.current && mountedRef.current) {
        if (!handleUnauthorized(err)) setWorkflowError(err.message);
      }
    } finally {
      if (mountedRef.current) setActionLoading(false);
    }
  }

  const incident = selected?.incident || {};
  const investigation = selected?.investigation || {};
  const evidence = selected?.evidence || {};
  const timelineData = selected?.timeline || {};

  const evidenceGroups = [
    ["Metrics", evidence.metrics || []],
    ["Logs", evidence.logs || []],
    ["Database", evidence.database || []],
    ["Other", evidence.other || []],
  ];

  const timeline = [
    ...(timelineData.metrics || []),
    ...(timelineData.logs || []),
    ...(timelineData.other || []),
  ].sort((a, b) => new Date(a.timestamp || 0) - new Date(b.timestamp || 0));

  return (
    <div className="app">
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; }
        .app {
          --bg:#080d19; --panel:#111a2c; --border:#26334b;
          --muted:#8b9ab2; background:var(--bg); color:#e9eef9;
          min-height:100vh; font-family:Inter,system-ui,sans-serif;
          line-height:1.5;
        }
        .app button,.app input,.app select { font:inherit; }
        .app button { cursor:pointer; }
        .app button:disabled { opacity:.45; cursor:not-allowed; }
        .topbar {
          padding:17px max(25px,calc((100vw - 1380px)/2));
          background:#0c1423; border-bottom:1px solid var(--border);
          display:flex; align-items:center; justify-content:space-between;
          gap:16px;
        }
        .brand { display:flex; gap:13px; align-items:center; }
        .brand-logo,.login-logo {
          width:46px; height:46px; border-radius:12px;
          display:grid; place-items:center; font-size:24px;
          background:linear-gradient(135deg,#2563eb,#06b6d4);
          color:white; font-weight:900;
        }
        .brand h1 { margin:0; font-size:21px; letter-spacing:.06em; }
        .brand small { color:var(--muted); font-size:11px; }
        .header-actions { display:flex; align-items:center; gap:16px; }
        .connection { font-size:12px; font-weight:750; display:flex; align-items:center; gap:8px; }
        .dot { width:9px; height:9px; border-radius:50%; background:#34d399; }
        .dot.red { background:#fb7185; }
        .shell { max-width:1440px; margin:auto; padding:30px 28px 65px; }
        .main-heading { display:flex; justify-content:space-between; gap:20px; align-items:center; margin-bottom:26px; }
        .main-heading h2 { font-size:32px; margin:0 0 9px; }
        .main-heading p,.section-title p,.muted { font-size:12px; color:var(--muted); }
        .eyebrow { display:block; color:#38bdf8; font-size:11px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:8px; }
        .panel { background:var(--panel); border:1px solid var(--border); border-radius:15px; min-width:0; }
        .card { padding:23px; margin-bottom:20px; }
        .section-title { margin-bottom:20px; }
        .section-title h2 { font-size:20px; margin:0 0 6px; }
        .section-title p { margin:0; }
        .btn {
          border:1px solid #334766; background:#1b2a42; color:#e9eef9;
          border-radius:9px; padding:10px 15px; font-size:12px; font-weight:700;
        }
        .btn:hover:not(:disabled) { background:#243a59; border-color:#38bdf8; }
        .btn.primary { background:#2563eb; border-color:#3b82f6; color:#fff; }
        .btn.danger { background:#481f31; border-color:#9f3548; color:#fda4af; }
        .controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
        .toggle { color:#a7b7cf; font-size:12px; display:flex; align-items:center; gap:7px; }
        .toggle input { accent-color:#38bdf8; }
        .input,.select {
          background:#0c1423; color:#e9eef9; border:1px solid #30415a;
          border-radius:9px; padding:11px 13px; outline:none;
        }
        .input:focus,.select:focus { border-color:#38bdf8; }
        .stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-bottom:22px; }
        .stat { padding:21px; }
        .stat span,.stat small { display:block; font-size:12px; color:var(--muted); }
        .stat strong { display:block; font-size:34px; margin:7px 0; }
        .two { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
        .bars { display:grid; gap:18px; padding:8px 0; }
        .bar-line { display:grid; grid-template-columns:85px 1fr 25px; gap:10px; align-items:center; font-size:11px; }
        .track { height:9px; border-radius:20px; background:#27364d; overflow:hidden; }
        .fill { height:100%; border-radius:20px; }
        .donut-layout { display:flex; align-items:center; gap:26px; }
        .donut { height:150px; width:150px; border-radius:50%; display:grid; place-items:center; flex-shrink:0; }
        .donut-inner { width:106px; height:106px; border-radius:50%; background:var(--panel); display:flex; align-items:center; justify-content:center; flex-direction:column; }
        .donut-inner strong { font-size:29px; }
        .donut-inner small { font-size:10px; color:var(--muted); }
        .legend { flex:1; min-width:0; }
        .legend > div { display:flex; gap:9px; align-items:center; margin-bottom:10px; font-size:12px; }
        .legend > div > span { width:9px; height:9px; border-radius:3px; }
        .legend strong { margin-left:auto; }
        .toolbar { display:flex; gap:11px; flex-wrap:wrap; margin-bottom:16px; }
        .toolbar .input { flex:1; min-width:225px; }
        .table-wrap { overflow-x:auto; }
        table { width:100%; border-collapse:collapse; min-width:740px; text-align:left; }
        th { color:#8498b5; letter-spacing:.1em; font-size:10px; padding:13px; border-bottom:1px solid var(--border); }
        td { padding:16px 13px; border-bottom:1px solid #202d42; font-size:12px; color:#c7d2e3; }
        tbody tr { cursor:pointer; }
        tbody tr:hover { background:#1d2b43; }
        tbody tr:focus-visible { outline:2px solid #38bdf8; }
        .incident-id { color:#7dd3fc; font-weight:800; }
        .badge { display:inline-flex; gap:7px; align-items:center; border:1px solid; border-radius:7px; padding:5px 9px; font-size:10px; font-weight:800; white-space:nowrap; }
        .badge-dot { width:6px; height:6px; border-radius:50%; }
        .activity-item { border-top:1px solid var(--border); padding:13px 0; display:flex; justify-content:space-between; align-items:center; gap:14px; }
        .activity-item strong { font-size:12px; color:#7dd3fc; }
        .activity-item p { margin:4px 0; color:#9aabc2; font-size:12px; }
        .activity-item small { color:#7c8da7; font-size:11px; }
        .info-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:20px; }
        .info { border:1px solid #2a3b54; border-radius:10px; background:#0c1423; padding:15px; min-width:0; }
        .info span { display:block; font-size:11px; color:var(--muted); margin-bottom:7px; }
        .info strong { font-size:13px; overflow-wrap:anywhere; }
        .subcard { background:#0c1423; border:1px solid #26334b; border-radius:12px; padding:19px; margin-bottom:18px; min-width:0; }
        .subcard h3 { font-size:16px; margin:0 0 12px; }
        .subcard h4 { color:#7dd3fc; font-size:13px; margin:16px 0 8px; }
        .subcard p { color:#b2c1d4; font-size:12px; overflow-wrap:anywhere; }
        .record { border-top:1px solid #283950; padding:13px 0; }
        .record strong { display:block; font-size:12px; margin-bottom:5px; }
        .record p { margin:6px 0; }
        .record small { font-size:11px; color:#8395af; }
        .alert { padding:12px 14px; border-radius:9px; margin:12px 0; font-size:12px; color:#fda4af; background:#4c1d2c66; border:1px solid #9f3548; }
        .alert.success { background:#064e3b55; color:#86efac; border-color:#047857; }
        .empty { text-align:center; padding:25px; color:var(--muted); font-size:13px; }
        .ai-panel { background:linear-gradient(140deg,#111e34,#0c1423); border-color:#2563eb66; }
        .ai-header { display:flex; justify-content:space-between; align-items:center; gap:20px; margin-bottom:15px; }
        .ai-header h3 { font-size:21px; margin:0 0 8px; }
        .ai-summary { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:20px 0; }
        .ai-item { display:flex; align-items:flex-start; gap:12px; background:#14233a; border:1px solid #263b59; border-radius:9px; padding:12px; margin-bottom:9px; }
        .ai-item p { margin:0; }
        .ai-icon { display:grid; place-items:center; flex-shrink:0; width:24px; height:24px; border-radius:7px; background:#064e3b; color:#6ee7b7; font-weight:800; }
        .ai-icon.warning { color:#fb7185; background:#4c1d2c; }
        .notice { background:#0e2941; border:1px solid #2563eb66; border-radius:10px; padding:17px; }
        .notice strong { color:#93c5fd; font-size:13px; }
        .notice p { margin:7px 0 0; }
        .login-page { min-height:100vh; display:grid; place-items:center; padding:24px; background:radial-gradient(ellipse at 50% 25%,#152d50,#080d19 65%); }
        .login-card { width:100%; max-width:420px; padding:38px; }
        .login-logo { margin-bottom:24px; }
        .login-card h1 { font-size:31px; margin:0 0 6px; letter-spacing:.06em; }
        .login-card p { font-size:13px; color:var(--muted); margin-bottom:28px; }
        .login-card label { display:block; font-size:12px; color:#cbd5e1; margin-bottom:10px; }
        .login-card .input { display:block; width:100%; margin-bottom:16px; }
        .login-button { width:100%; padding:13px; }
        .login-foot { display:block; margin-top:24px; color:var(--muted); font-size:11px; text-align:center; }
        .footer { text-align:center; color:#64748b; font-size:11px; padding:15px; }
        @media(max-width:980px) {
          .stats,.info-grid,.ai-summary { grid-template-columns:repeat(2,minmax(0,1fr)); }
          .two { grid-template-columns:1fr; }
        }
        @media(max-width:600px) {
          .shell { padding:22px 14px 40px; }
          .topbar { padding:14px; }
          .brand h1 { font-size:17px; }
          .brand small { font-size:9px; }
          .main-heading,.ai-header { flex-direction:column; align-items:flex-start; }
          .main-heading h2 { font-size:25px; }
          .card { padding:15px; }
          .stat { padding:14px; }
          .stat strong { font-size:27px; }
          .stats { gap:10px; }
          .donut { width:125px; height:125px; }
          .donut-inner { width:88px; height:88px; }
          .donut-layout { gap:14px; }
          .header-actions { gap:8px; flex-wrap:wrap; justify-content:flex-end; }
        }
      `}</style>

      {auth.loading ? (
        <div className="login-page">
          <div className="panel login-card">
            <h2>Connecting to NEXUS AI...</h2>
          </div>
        </div>
      ) : auth.enabled && !auth.authenticated ? (
        <>
          {authError && <div className="alert" role="alert">{authError}</div>}
          <LoginScreen onLogin={checkAuth} />
        </>
      ) : (
        <>
          <header className="topbar">
            <div className="brand">
              <div className="brand-logo">N</div>
              <div>
                <h1>NEXUS AI</h1>
                <small>Operations & Incident Intelligence</small>
              </div>
            </div>

            <div className="header-actions">
              <div className="connection">
                <span className={`dot ${error ? "red" : ""}`} />
                {error ? "API OFFLINE" : "API CONNECTED"}
              </div>
              {auth.enabled && (
                <button className="btn" onClick={logout}>Sign Out</button>
              )}
            </div>
          </header>

          <main className="shell">
            <section className="main-heading">
              <div>
                <span className="eyebrow">Security Operations Center</span>
                <h2>Live Threat Intelligence</h2>
                <p>Incident monitoring, AI investigation and human-controlled remediation.</p>
                <p className="muted">
                  Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : "Never"}
                  {" · "}
                  {autoRefresh ? "Auto-refresh every 15s" : "Auto-refresh paused"}
                </p>
              </div>
              <div className="controls">
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                  />
                  Auto-refresh
                </label>
                <button
                  className="btn"
                  disabled={loading || refreshing}
                  onClick={() => loadIncidents()}
                >
                  {refreshing ? "Refreshing..." : "↻ Refresh Data"}
                </button>
              </div>
            </section>

            {error && <div className="alert" role="alert">{error}</div>}

            <div className="stats">
              <Stat label="Total Incidents" value={stats.total} description="Recorded cases" />
              <Stat label="Critical Alerts" value={stats.critical} color="#fb7185" description="Critical severity" />
              <Stat label="Active Incidents" value={stats.active} color="#facc15" description="Not marked resolved" />
              <Stat label="High Severity" value={stats.high} color="#a78bfa" description="High priority cases" />
            </div>

            <div className="two">
              <section className="panel card">
                <SectionTitle eyebrow="Threat Analytics" title="Severity Distribution" description="Incident counts and severity proportions" />
                <SeverityChart incidents={incidents} />
              </section>

              <section className="panel card">
                <SectionTitle eyebrow="Operations Overview" title="Incident Status" description="Distribution of incident lifecycle states" />
                <StatusChart incidents={incidents} />
              </section>
            </div>

            <section className="panel card">
              <SectionTitle eyebrow="Threat Monitoring" title="Incident Queue" description="Search and investigate recorded incidents" />

              <div className="toolbar">
                <input
                  className="input"
                  type="search"
                  placeholder="Search by incident ID, service or status..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select
                  className="select"
                  aria-label="Severity filter"
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <option value="ALL">All Severities</option>
                  {SEVERITIES.map((severity) => (
                    <option value={severity} key={severity}>{severity}</option>
                  ))}
                </select>
              </div>

              {loading ? <p className="empty">Loading incidents...</p> :
                !filtered.length ? <p className="empty">No matching incidents.</p> : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Incident ID</th>
                          <th>Service</th>
                          <th>Severity</th>
                          <th>Status</th>
                          <th>Confidence</th>
                          <th>Detected At</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((item) => (
                          <tr
                            key={item.id}
                            role="button"
                            tabIndex={0}
                            onClick={() => openIncident(item.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                openIncident(item.id);
                              }
                            }}
                          >
                            <td className="incident-id">{item.id}</td>
                            <td>{show(item.service)}</td>
                            <td><Badge value={item.severity} /></td>
                            <td><Badge value={item.status} /></td>
                            <td>{show(item.confidence)}</td>
                            <td>{dateText(item.detected_at)}</td>
                            <td>→</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              <p className="muted">
                Showing {filtered.length} of {incidents.length} incidents
              </p>
            </section>

            <section className="panel card">
              <SectionTitle eyebrow="Monitoring Feed" title="Recent Incident Activity" description="Latest detected incidents from the database" />
              {recentActivity.length ? recentActivity.map((item) => (
                <div className="activity-item" key={item.id}>
                  <div>
                    <strong>{item.id}</strong>
                    <p>{show(item.service)} · {show(item.status)}</p>
                    <small>{dateText(item.detected_at)}</small>
                  </div>
                  <Badge value={item.severity} />
                </div>
              )) : <p className="empty">No activity recorded.</p>}
            </section>

            {detailsLoading && <div className="panel card empty">Loading incident details...</div>}
            {detailsError && <div className="alert" role="alert">{detailsError}</div>}

            {selected && !detailsLoading && (
              <section className="panel card">
                <div className="main-heading">
                  <div>
                    <span className="eyebrow">Incident Investigation</span>
                    <h2>{show(incident.id)}</h2>
                    <p>AI analysis, evidence, timeline and human approval controls.</p>
                  </div>
                  <button className="btn" onClick={closeIncident}>Close</button>
                </div>

                <div className="info-grid">
                  <div className="info"><span>Service</span><strong>{show(incident.service)}</strong></div>
                  <div className="info"><span>Severity</span><Badge value={incident.severity} /></div>
                  <div className="info"><span>Incident Status</span><Badge value={incident.status} /></div>
                  <div className="info">
                    <span>AI Confidence</span>
                    <strong>{show(aiReport?.confidence || investigation.confidence)}</strong>
                  </div>
                </div>

                <div className="subcard ai-panel">
                  <div className="ai-header">
                    <div>
                      <span className="eyebrow">AI-Powered Incident Intelligence</span>
                      <h3>AI Investigation Center</h3>
                      <p>Evidence-based root cause assessment and recommended actions.</p>
                    </div>
                    <button
                      className="btn primary"
                      disabled={aiRunning || aiLoading}
                      onClick={runInvestigation}
                    >
                      {aiRunning ? "Analyzing..." : aiReport ? "↻ Re-run Investigation" : "✦ Run AI Investigation"}
                    </button>
                  </div>

                  <p className="muted">Deterministic mode · No API charges · No automatic remediation</p>
                  {aiLoading && <p>Loading saved investigation report...</p>}
                  {aiError && <div className="alert" role="alert">{aiError}</div>}
                  {aiMessage && <div className="alert success" role="status">{aiMessage}</div>}

                  {aiReport ? (
                    <>
                      <div className="ai-summary">
                        <div className="info"><span>Status</span><strong style={{ color: "#34d399" }}>COMPLETED</strong></div>
                        <div className="info"><span>Confidence</span><Badge value={aiReport.confidence} /></div>
                        <div className="info"><span>Mode</span><strong>{show(aiReport.investigation_mode)}</strong></div>
                        <div className="info"><span>Generated At</span><strong>{dateText(aiReport.generated_at)}</strong></div>
                      </div>

                      <div className="subcard">
                        <span className="eyebrow">Root Cause Intelligence</span>
                        <h3>Probable Root Cause</h3>
                        <p>{show(aiReport.root_cause)}</p>
                        <p className="muted">Advisory assessment; root cause is not confirmed.</p>
                      </div>

                      <div className="two">
                        <div className="subcard">
                          <span className="eyebrow">Evidence Analysis</span>
                          <h3>Key Findings</h3>
                          {aiReport.findings?.length ? aiReport.findings.map((finding, index) => (
                            <div className="ai-item" key={index}>
                              <span className="ai-icon warning">!</span>
                              <p>{finding}</p>
                            </div>
                          )) : <p>No specific findings available.</p>}
                        </div>

                        <div className="subcard">
                          <span className="eyebrow">Recommended Response</span>
                          <h3>Suggested Actions</h3>
                          {aiReport.recommendations?.length ? aiReport.recommendations.map((action, index) => (
                            <div className="ai-item" key={index}>
                              <span className="ai-icon">✓</span>
                              <p>{action}</p>
                            </div>
                          )) : <p>No recommendations available.</p>}
                        </div>
                      </div>

                      <div className="notice">
                        <strong>Human Review Required</strong>
                        <p>Recommendations are advisory. Remediation requires the human approval workflow.</p>
                      </div>
                    </>
                  ) : !aiLoading && (
                    <p className="empty">No report yet. Click Run AI Investigation.</p>
                  )}
                </div>

                <div className="two">
                  <div className="subcard">
                    <span className="eyebrow">Intelligence Analysis</span>
                    <h3>Current Root Cause Summary</h3>
                    <p>{show(aiReport?.root_cause || investigation.root_cause, "No analysis available.")}</p>
                    <div className="record">
                      <strong>Confidence</strong>
                      <p>{show(aiReport?.confidence || investigation.confidence)}</p>
                    </div>
                  </div>
                  <div className="subcard">
                    <span className="eyebrow">Incident Metadata</span>
                    <h3>Detection Information</h3>
                    <div className="record"><strong>Incident ID</strong><p>{show(incident.id)}</p></div>
                    <div className="record"><strong>Detected At</strong><p>{dateText(incident.detected_at)}</p></div>
                  </div>
                </div>

                <div className="two">
                  <div className="subcard">
                    <span className="eyebrow">Forensic Intelligence</span>
                    <h3>Evidence Correlation</h3>
                    <p>Total evidence: {evidence.summary?.total ?? 0}</p>
                    {evidenceGroups.every(([, items]) => !items.length) && <p>No evidence records.</p>}
                    {evidenceGroups.map(([name, items]) => items.length ? (
                      <div key={name}>
                        <h4>{name} ({items.length})</h4>
                        {items.map((item, i) => (
                          <div className="record" key={`${name}-${item.id ?? i}`}>
                            <strong>{show(item.type)}</strong>
                            <p>{show(item.details)}</p>
                          </div>
                        ))}
                      </div>
                    ) : null)}
                  </div>

                  <div className="subcard">
                    <span className="eyebrow">Event Tracking</span>
                    <h3>Incident Timeline</h3>
                    {timeline.length ? timeline.map((event, i) => (
                      <div className="record" key={`${event.id ?? i}-${event.type}`}>
                        <strong>{show(event.type)}</strong>
                        <p>{show(event.description)}</p>
                        <small>{dateText(event.timestamp)}</small>
                      </div>
                    )) : <p>No timeline available.</p>}
                  </div>
                </div>

                <div className="subcard">
                  <span className="eyebrow">Human-in-the-Loop</span>
                  <h3>Remediation Control Center</h3>
                  <p>Human approval is required for safe simulation. No real infrastructure action is performed.</p>

                  {workflowLoading && <p>Loading workflow...</p>}
                  {workflowError && <div className="alert" role="alert">{workflowError}</div>}
                  {workflowMessage && <div className="alert success" role="status">{workflowMessage}</div>}

                  {workflow && (
                    <>
                      <div className="info-grid">
                        <div className="info"><span>Approval</span><Badge value={workflow.approval_status} /></div>
                        <div className="info"><span>Remediation</span><Badge value={workflow.remediation_status} /></div>
                        <div className="info"><span>Reviewer</span><strong>{show(workflow.reviewer, "Not assigned")}</strong></div>
                        <div className="info"><span>Decision Time</span><strong>{dateText(workflow.decision_at)}</strong></div>
                      </div>

                      {workflow.approval_status === "PENDING" && (
                        <div className="subcard">
                          <h3>Human Approval Required</h3>
                          <p>Review carefully. Recorded approval decisions cannot be changed.</p>

                          <label htmlFor="reviewer">Reviewer Name</label>
                          <input
                            id="reviewer"
                            className="input"
                            style={{ display: "block", width: "100%", maxWidth: 380, margin: "10px 0" }}
                            value={reviewer}
                            maxLength={100}
                            placeholder="Enter reviewer name"
                            onChange={(e) => setReviewer(e.target.value)}
                          />
                          <div className="controls">
                            <button
                              className="btn primary"
                              disabled={actionLoading || reviewer.trim().length < 2}
                              onClick={() => submitAction("APPROVE")}
                            >
                              {actionLoading ? "Processing..." : "Approve"}
                            </button>
                            <button
                              className="btn danger"
                              disabled={actionLoading || reviewer.trim().length < 2}
                              onClick={() => submitAction("REJECT")}
                            >
                              {actionLoading ? "Processing..." : "Reject"}
                            </button>
                          </div>
                        </div>
                      )}

                      {workflow.approval_status === "REJECTED" && (
                        <div className="subcard">
                          <h3 style={{ color: "#fb7185" }}>Remediation Rejected</h3>
                          <p>Rejected by {show(workflow.reviewer)}. Simulation is blocked.</p>
                        </div>
                      )}

                      {workflow.approval_status === "APPROVED" &&
                        workflow.remediation_status !== "SIMULATED" && (
                          <div className="subcard">
                            <h3 style={{ color: "#34d399" }}>Approval Granted</h3>
                            <p>Safe remediation simulation can now be recorded.</p>
                            <button
                              className="btn primary"
                              disabled={actionLoading}
                              onClick={() => submitAction("SIMULATE")}
                            >
                              {actionLoading ? "Running..." : "Run Safe Simulation"}
                            </button>
                          </div>
                        )}

                      {workflow.remediation_status === "SIMULATED" && (
                        <div className="subcard">
                          <h3 style={{ color: "#34d399" }}>Simulation Completed</h3>
                          <p>No production infrastructure was modified.</p>
                          <button className="btn" disabled>Simulation Completed</button>
                        </div>
                      )}

                      {workflow.simulation_result && (
                        <div className="subcard">
                          <h3>Simulation Result</h3>
                          <p>{show(workflow.simulation_result)}</p>
                        </div>
                      )}

                      <div className="subcard">
                        <span className="eyebrow">Compliance & Accountability</span>
                        <h3>Workflow Audit Trail</h3>
                        {workflow.audit?.length ? workflow.audit.map((event, i) => (
                          <div className="record" key={event.id ?? i}>
                            <Badge value={event.action} />
                            <p>{show(event.details)}</p>
                            <small>
                              {show(event.actor, "Unknown actor")} · {dateText(event.timestamp)}
                            </small>
                          </div>
                        )) : <p>No audit events recorded.</p>}
                      </div>
                    </>
                  )}
                </div>
              </section>
            )}

            <footer className="footer">
              NEXUS AI · Operations & Incident Intelligence · Development Environment
            </footer>
          </main>
        </>
      )}
    </div>
  );
}

export default App;
