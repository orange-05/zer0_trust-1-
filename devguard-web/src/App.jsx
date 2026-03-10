import { useState, useEffect, useRef, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, Area, AreaChart
} from "recharts";

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const MOCK_PIPELINES = [
  { id: "pl-a1b2c3d4", commit_id: "3f8e21a", branch: "main", status: "passed", triggered_by: "github-actions", created_at: "2026-03-10T09:00:00Z" },
  { id: "pl-b2c3d4e5", commit_id: "7c4d9f2", branch: "feature/auth", status: "failed", triggered_by: "github-actions", created_at: "2026-03-10T08:30:00Z" },
  { id: "pl-c3d4e5f6", commit_id: "1a8b3e5", branch: "main", status: "passed", triggered_by: "push", created_at: "2026-03-10T07:00:00Z" },
  { id: "pl-d4e5f6g7", commit_id: "9d2f7c1", branch: "hotfix/sec", status: "passed", triggered_by: "github-actions", created_at: "2026-03-09T22:00:00Z" },
];

const MOCK_SCANS = [
  { id: "sc-a1", pipeline_id: "pl-a1b2c3d4", scan_type: "dependency", tool: "trivy", status: "passed", critical_count: 0, high_count: 1, created_at: "2026-03-10T09:01:00Z" },
  { id: "sc-a2", pipeline_id: "pl-a1b2c3d4", scan_type: "image", tool: "trivy", status: "passed", critical_count: 0, high_count: 0, created_at: "2026-03-10T09:03:00Z" },
  { id: "sc-b1", pipeline_id: "pl-b2c3d4e5", scan_type: "dependency", tool: "trivy", status: "failed", critical_count: 2, high_count: 5, created_at: "2026-03-10T08:31:00Z" },
  { id: "sc-c1", pipeline_id: "pl-c3d4e5f6", scan_type: "image", tool: "trivy", status: "passed", critical_count: 0, high_count: 2, created_at: "2026-03-10T07:02:00Z" },
  { id: "sc-d1", pipeline_id: "pl-d4e5f6g7", scan_type: "filesystem", tool: "trivy", status: "passed", critical_count: 0, high_count: 0, created_at: "2026-03-09T22:01:00Z" },
];

const MOCK_DEPLOYMENTS = [
  { id: "dp-a1", pipeline_id: "pl-a1b2c3d4", image_tag: "devguard-api:3f8e21a", signed: true, environment: "production", status: "deployed", created_at: "2026-03-10T09:10:00Z" },
  { id: "dp-c1", pipeline_id: "pl-c3d4e5f6", image_tag: "devguard-api:1a8b3e5", signed: true, environment: "staging", status: "deployed", created_at: "2026-03-10T07:15:00Z" },
  { id: "dp-d1", pipeline_id: "pl-d4e5f6g7", image_tag: "devguard-api:9d2f7c1", signed: true, environment: "production", status: "deployed", created_at: "2026-03-09T22:20:00Z" },
];

const MOCK_REPORT = { total_scans: 5, passed: 4, failed: 1, critical_vulnerabilities: 2, high_vulnerabilities: 8, trust_status: "trusted" };

// ─── API CLIENT ───────────────────────────────────────────────────────────────
const createApiClient = (baseUrl) => {
  let token = null;
  const headers = () => ({
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  });
  return {
    setToken: (t) => { token = t; },
    get: (path) => fetch(`${baseUrl}${path}`, { headers: headers() }).then(r => r.json()),
    post: (path, body) => fetch(`${baseUrl}${path}`, { method: "POST", headers: headers(), body: JSON.stringify(body) }).then(r => r.json()),
  };
};

// ─── STYLES ───────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&display=swap');

  :root {
    --black: #050708;
    --dark: #0a0c0f;
    --panel: #0e1114;
    --border: #1a2030;
    --green: #00ff88;
    --green-dim: #00cc6a;
    --green-glow: rgba(0,255,136,0.15);
    --red: #ff3355;
    --red-dim: #cc2244;
    --yellow: #ffcc00;
    --blue: #0088ff;
    --text: #c8d8e8;
    --text-dim: #5a7090;
    --mono: 'Share Tech Mono', monospace;
    --display: 'Rajdhani', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  html { scroll-behavior: smooth; }

  body {
    background: var(--black);
    color: var(--text);
    font-family: var(--display);
    overflow-x: hidden;
  }

  /* Scanlines overlay */
  body::before {
    content: '';
    position: fixed; inset: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
    pointer-events: none;
    z-index: 9999;
  }

  .app { min-height: 100vh; }

  /* NAV */
  .nav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 2rem;
    height: 56px;
    background: rgba(5,7,8,0.92);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }
  .nav-logo {
    font-family: var(--mono);
    font-size: 1rem;
    color: var(--green);
    letter-spacing: 0.1em;
    display: flex; align-items: center; gap: 0.5rem;
  }
  .nav-logo .bracket { color: var(--text-dim); }
  .nav-links { display: flex; gap: 2rem; }
  .nav-links a {
    font-family: var(--display); font-weight: 500; font-size: 0.8rem;
    color: var(--text-dim); text-decoration: none; letter-spacing: 0.12em;
    text-transform: uppercase; transition: color 0.2s;
    cursor: pointer;
  }
  .nav-links a:hover { color: var(--green); }
  .nav-badge {
    font-family: var(--mono); font-size: 0.65rem;
    color: var(--green); border: 1px solid var(--green);
    padding: 2px 8px; letter-spacing: 0.1em;
  }

  /* SECTIONS */
  section { min-height: 100vh; padding: 80px 0 60px; }

  /* HERO */
  .hero {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; position: relative; overflow: hidden;
    min-height: 100vh;
    background: radial-gradient(ellipse 80% 60% at 50% 40%, rgba(0,255,136,0.04) 0%, transparent 70%);
  }

  .hero-grid {
    position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(0,255,136,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,136,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
  }

  .hero-tag {
    font-family: var(--mono); font-size: 0.7rem; color: var(--green);
    letter-spacing: 0.25em; text-transform: uppercase;
    margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 0.75rem;
  }
  .hero-tag::before, .hero-tag::after {
    content: ''; flex: 1; max-width: 40px; height: 1px; background: var(--green);
  }

  .hero-title {
    font-family: var(--display); font-weight: 700;
    font-size: clamp(2.8rem, 7vw, 6rem);
    line-height: 0.95; letter-spacing: -0.02em;
    color: #fff; margin-bottom: 0.3rem;
  }
  .hero-title span { color: var(--green); }

  .hero-subtitle-line {
    font-family: var(--mono); font-size: clamp(0.75rem, 1.5vw, 1rem);
    color: var(--text-dim); letter-spacing: 0.2em;
    margin-bottom: 2.5rem; text-transform: uppercase;
  }

  .hero-desc {
    max-width: 540px;
    font-size: 1.05rem; font-weight: 400; line-height: 1.7;
    color: var(--text-dim); margin-bottom: 3rem;
  }

  .hero-ctas { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; }

  .btn-primary {
    background: var(--green); color: var(--black);
    border: none; padding: 0.8rem 2rem;
    font-family: var(--display); font-weight: 700; font-size: 0.85rem;
    letter-spacing: 0.12em; text-transform: uppercase;
    cursor: pointer; transition: all 0.2s;
    clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%);
  }
  .btn-primary:hover { background: #fff; transform: translateY(-2px); }

  .btn-secondary {
    background: transparent; color: var(--green);
    border: 1px solid var(--green); padding: 0.8rem 2rem;
    font-family: var(--display); font-weight: 600; font-size: 0.85rem;
    letter-spacing: 0.12em; text-transform: uppercase;
    cursor: pointer; transition: all 0.2s;
    clip-path: polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%);
  }
  .btn-secondary:hover { background: var(--green-glow); }

  .hero-stats {
    display: flex; gap: 3rem; margin-top: 4rem;
    padding-top: 3rem;
    border-top: 1px solid var(--border);
  }
  .stat { text-align: center; }
  .stat-num {
    font-family: var(--mono); font-size: 2rem; color: var(--green); display: block;
  }
  .stat-label {
    font-size: 0.7rem; letter-spacing: 0.2em; color: var(--text-dim);
    text-transform: uppercase; margin-top: 4px;
  }

  .hero-scroll {
    position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%);
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    letter-spacing: 0.2em; display: flex; flex-direction: column; align-items: center; gap: 8px;
    animation: bounce 2s ease-in-out infinite;
  }
  @keyframes bounce { 0%,100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(6px); } }

  /* SECTION HEADERS */
  .section-header {
    text-align: center; margin-bottom: 3rem;
  }
  .section-tag {
    font-family: var(--mono); font-size: 0.65rem; color: var(--green);
    letter-spacing: 0.3em; text-transform: uppercase; margin-bottom: 0.75rem;
  }
  .section-title {
    font-family: var(--display); font-weight: 700;
    font-size: clamp(1.8rem, 4vw, 3rem); color: #fff;
    letter-spacing: -0.01em;
  }
  .section-title span { color: var(--green); }
  .section-desc { color: var(--text-dim); margin-top: 0.75rem; font-size: 1rem; }

  /* CONTAINER */
  .container { max-width: 1200px; margin: 0 auto; padding: 0 2rem; }

  /* ARCHITECTURE SECTION */
  .arch-section { background: var(--dark); }
  .arch-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: start; }
  @media (max-width: 768px) { .arch-grid { grid-template-columns: 1fr; } }

  .pipeline-flow { display: flex; flex-direction: column; gap: 0; }
  .pipeline-stage {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.9rem 1.2rem;
    border: 1px solid var(--border);
    background: var(--panel);
    position: relative;
    transition: all 0.3s;
    cursor: default;
  }
  .pipeline-stage:not(:last-child)::after {
    content: '';
    position: absolute; bottom: -1px; left: 50%; transform: translateX(-50%);
    width: 1px; height: 1px;
    background: var(--green);
    z-index: 1;
  }
  .pipeline-stage:hover { border-color: var(--green); background: rgba(0,255,136,0.04); }
  .pipeline-stage.active { border-color: var(--green); background: rgba(0,255,136,0.08); }
  .pipeline-stage.blocked { border-color: var(--red); background: rgba(255,51,85,0.06); }

  .stage-num {
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    min-width: 24px;
  }
  .stage-icon { font-size: 1rem; min-width: 20px; text-align: center; }
  .stage-info { flex: 1; }
  .stage-name {
    font-weight: 600; font-size: 0.9rem; color: #fff; letter-spacing: 0.05em;
  }
  .stage-desc { font-size: 0.72rem; color: var(--text-dim); margin-top: 2px; font-family: var(--mono); }
  .stage-badge {
    font-family: var(--mono); font-size: 0.6rem; padding: 2px 8px;
    letter-spacing: 0.1em; text-transform: uppercase;
  }
  .badge-pass { color: var(--green); border: 1px solid var(--green); }
  .badge-fail { color: var(--red); border: 1px solid var(--red); }
  .badge-run { color: var(--yellow); border: 1px solid var(--yellow); }
  .badge-info { color: var(--blue); border: 1px solid var(--blue); }

  .connector {
    width: 1px; height: 16px; background: var(--border);
    margin: 0 auto; position: relative;
  }
  .connector.active { background: var(--green); box-shadow: 0 0 6px var(--green); }

  .arch-layers { display: flex; flex-direction: column; gap: 1px; }
  .arch-layer {
    padding: 1.2rem 1.5rem;
    border: 1px solid var(--border);
    background: var(--panel);
    position: relative; overflow: hidden;
    transition: border-color 0.3s;
  }
  .arch-layer:hover { border-color: var(--green); }
  .arch-layer::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: var(--green); opacity: 0.4;
  }
  .layer-title { font-weight: 700; font-size: 0.85rem; color: var(--green); letter-spacing: 0.1em; text-transform: uppercase; }
  .layer-files {
    display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.6rem;
  }
  .file-chip {
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    background: rgba(255,255,255,0.04); border: 1px solid var(--border);
    padding: 2px 8px;
  }
  .layer-arrow {
    text-align: center; color: var(--text-dim); font-size: 0.8rem;
    padding: 0.3rem; background: var(--dark);
    font-family: var(--mono);
  }

  /* DEMO SECTION */
  .demo-section { background: var(--black); }
  .demo-config {
    display: flex; align-items: center; gap: 1rem;
    background: var(--panel); border: 1px solid var(--border);
    padding: 0.75rem 1.2rem; margin-bottom: 2rem;
    font-family: var(--mono); font-size: 0.8rem;
  }
  .demo-config-label { color: var(--text-dim); white-space: nowrap; }
  .demo-config-input {
    flex: 1; background: transparent; border: none; border-bottom: 1px solid var(--border);
    color: var(--green); font-family: var(--mono); font-size: 0.8rem;
    outline: none; padding: 2px 4px;
  }
  .demo-config-input:focus { border-bottom-color: var(--green); }
  .demo-mode-badge {
    font-size: 0.6rem; padding: 3px 10px; letter-spacing: 0.15em; text-transform: uppercase;
  }
  .mode-sim { color: var(--yellow); border: 1px solid var(--yellow); }
  .mode-live { color: var(--green); border: 1px solid var(--green); }

  .demo-grid { display: grid; grid-template-columns: 380px 1fr; gap: 2rem; }
  @media (max-width: 900px) { .demo-grid { grid-template-columns: 1fr; } }

  .demo-panel {
    background: var(--panel); border: 1px solid var(--border);
    display: flex; flex-direction: column;
  }
  .demo-panel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.9rem 1.2rem;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono); font-size: 0.72rem;
  }
  .demo-panel-title { color: var(--green); letter-spacing: 0.1em; text-transform: uppercase; }
  .demo-panel-status { color: var(--text-dim); }

  .demo-form { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
  .form-group { display: flex; flex-direction: column; gap: 0.4rem; }
  .form-label {
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    letter-spacing: 0.15em; text-transform: uppercase;
  }
  .form-input {
    background: var(--dark); border: 1px solid var(--border);
    color: var(--text); font-family: var(--mono); font-size: 0.82rem;
    padding: 0.6rem 0.8rem; outline: none; transition: border-color 0.2s;
  }
  .form-input:focus { border-color: var(--green); }
  .form-error { font-family: var(--mono); font-size: 0.65rem; color: var(--red); }
  .form-success { font-family: var(--mono); font-size: 0.65rem; color: var(--green); }

  .demo-tabs {
    display: flex; border-bottom: 1px solid var(--border);
  }
  .demo-tab {
    flex: 1; padding: 0.75rem; text-align: center;
    font-family: var(--mono); font-size: 0.7rem; color: var(--text-dim);
    cursor: pointer; transition: all 0.2s; letter-spacing: 0.1em;
    border-bottom: 2px solid transparent;
    background: none; border-top: none; border-left: none; border-right: none;
  }
  .demo-tab.active { color: var(--green); border-bottom-color: var(--green); }
  .demo-tab:hover:not(.active) { color: var(--text); }

  /* TERMINAL / LOG */
  .terminal {
    background: #050505; border: 1px solid var(--border);
    font-family: var(--mono); font-size: 0.75rem;
    overflow: hidden;
  }
  .terminal-header {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.6rem 1rem; background: var(--panel);
    border-bottom: 1px solid var(--border);
  }
  .term-dot { width: 10px; height: 10px; border-radius: 50%; }
  .term-title { color: var(--text-dim); font-size: 0.65rem; margin-left: 0.5rem; }
  .terminal-body { padding: 1rem; min-height: 260px; max-height: 340px; overflow-y: auto; }
  .log-line { margin-bottom: 3px; line-height: 1.5; }
  .log-time { color: var(--text-dim); margin-right: 8px; }
  .log-info { color: var(--text); }
  .log-success { color: var(--green); }
  .log-error { color: var(--red); }
  .log-warn { color: var(--yellow); }
  .log-cmd { color: var(--blue); }
  .cursor {
    display: inline-block; width: 8px; height: 1em;
    background: var(--green); animation: blink 1s step-end infinite; vertical-align: text-bottom;
  }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

  /* PIPELINE RUNNER */
  .pipeline-runner { padding: 1.5rem; }
  .runner-stages { display: flex; flex-direction: column; gap: 0; }
  .runner-stage {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.65rem 0.8rem;
    border-left: 2px solid var(--border);
    margin-left: 12px;
    position: relative; transition: all 0.3s;
  }
  .runner-stage::before {
    content: '';
    position: absolute; left: -7px; top: 50%; transform: translateY(-50%);
    width: 12px; height: 12px; border-radius: 50%;
    border: 2px solid var(--border); background: var(--dark);
    transition: all 0.3s;
  }
  .runner-stage.done::before { border-color: var(--green); background: var(--green); }
  .runner-stage.running::before { border-color: var(--yellow); background: var(--yellow); animation: pulse 1s ease-in-out infinite; }
  .runner-stage.failed::before { border-color: var(--red); background: var(--red); }
  .runner-stage.done { border-left-color: var(--green); }
  .runner-stage.running { border-left-color: var(--yellow); }
  .runner-stage.failed { border-left-color: var(--red); }
  @keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(255,204,0,0.4); } 50% { box-shadow: 0 0 0 6px rgba(255,204,0,0); } }
  .runner-stage-name { font-size: 0.82rem; font-weight: 600; flex: 1; }
  .runner-stage-time { font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim); }

  /* DASHBOARD SECTION */
  .dash-section { background: var(--dark); }
  .metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin-bottom: 2rem; }
  @media (max-width: 900px) { .metrics-row { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 480px) { .metrics-row { grid-template-columns: 1fr; } }

  .metric-card {
    background: var(--panel); padding: 1.5rem;
    border: 1px solid var(--border);
    position: relative; overflow: hidden; transition: border-color 0.3s;
  }
  .metric-card:hover { border-color: var(--green); }
  .metric-card::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: var(--green); transform: scaleX(0); transform-origin: left;
    transition: transform 0.3s;
  }
  .metric-card:hover::after { transform: scaleX(1); }
  .metric-card.danger::after { background: var(--red); }
  .metric-card.danger:hover { border-color: var(--red); }

  .metric-label {
    font-family: var(--mono); font-size: 0.62rem; color: var(--text-dim);
    letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.75rem;
  }
  .metric-value {
    font-family: var(--display); font-weight: 700;
    font-size: 2.8rem; line-height: 1; color: #fff; margin-bottom: 0.4rem;
  }
  .metric-value.green { color: var(--green); }
  .metric-value.red { color: var(--red); }
  .metric-value.yellow { color: var(--yellow); }
  .metric-sub {
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
  }

  .charts-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; }
  @media (max-width: 900px) { .charts-grid { grid-template-columns: 1fr; } }

  .chart-card {
    background: var(--panel); border: 1px solid var(--border); padding: 1.5rem;
  }
  .chart-title {
    font-family: var(--mono); font-size: 0.65rem; color: var(--green);
    letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 1.2rem;
  }

  .pipelines-table { margin-top: 2rem; }
  .table-header {
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    letter-spacing: 0.2em; text-transform: uppercase;
    display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 80px;
    padding: 0.6rem 1rem; border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .table-row {
    display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 80px;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(26,32,48,0.5);
    background: var(--panel); transition: background 0.2s;
    font-size: 0.82rem;
  }
  .table-row:hover { background: rgba(0,255,136,0.03); }

  .status-dot {
    display: inline-flex; align-items: center; gap: 6px; font-family: var(--mono); font-size: 0.75rem;
  }
  .status-dot::before {
    content: ''; width: 6px; height: 6px; border-radius: 50%;
  }
  .status-passed .status-dot::before { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .status-failed .status-dot::before { background: var(--red); box-shadow: 0 0 6px var(--red); }
  .status-running .status-dot::before { background: var(--yellow); animation: pulse 1s infinite; }

  .trust-banner {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 1.5rem; margin-bottom: 2rem;
    border: 1px solid var(--green);
    background: rgba(0,255,136,0.05);
  }
  .trust-banner.danger { border-color: var(--red); background: rgba(255,51,85,0.05); }
  .trust-status {
    font-family: var(--mono); font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase;
    display: flex; align-items: center; gap: 0.75rem;
  }
  .trust-indicator {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green); box-shadow: 0 0 10px var(--green);
    animation: pulse 2s ease-in-out infinite;
  }
  .trust-indicator.danger { background: var(--red); box-shadow: 0 0 10px var(--red); }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--dark); }
  ::-webkit-scrollbar-thumb { background: var(--border); }
  ::-webkit-scrollbar-thumb:hover { background: var(--green); }

  /* FOOTER */
  .footer {
    background: var(--panel); border-top: 1px solid var(--border);
    padding: 2rem; text-align: center;
    font-family: var(--mono); font-size: 0.65rem; color: var(--text-dim);
    letter-spacing: 0.1em;
  }
  .footer span { color: var(--green); }

  /* RECHARTS CUSTOM */
  .recharts-tooltip-wrapper .recharts-default-tooltip {
    background: var(--panel) !important; border: 1px solid var(--border) !important;
    font-family: var(--mono) !important; font-size: 0.72rem !important;
  }

  /* ANIMATIONS */
  .fade-in { animation: fadeIn 0.6s ease forwards; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
  .fade-in-1 { animation-delay: 0.1s; opacity: 0; animation-fill-mode: forwards; }
  .fade-in-2 { animation-delay: 0.25s; opacity: 0; animation-fill-mode: forwards; }
  .fade-in-3 { animation-delay: 0.4s; opacity: 0; animation-fill-mode: forwards; }
  .fade-in-4 { animation-delay: 0.55s; opacity: 0; animation-fill-mode: forwards; }

  .glitch {
    position: relative;
  }
  .glitch::before, .glitch::after {
    content: attr(data-text);
    position: absolute; inset: 0;
    color: var(--green);
  }
  .glitch::before { animation: glitch1 4s infinite; clip-path: polygon(0 20%, 100% 20%, 100% 40%, 0 40%); opacity: 0.5; }
  .glitch::after { animation: glitch2 4s infinite; clip-path: polygon(0 60%, 100% 60%, 100% 80%, 0 80%); opacity: 0.3; }
  @keyframes glitch1 { 0%,95%,100% { transform: translateX(0); } 96% { transform: translateX(-3px); } 98% { transform: translateX(3px); } }
  @keyframes glitch2 { 0%,93%,100% { transform: translateX(0); } 94% { transform: translateX(3px); } 97% { transform: translateX(-3px); } }

  .input-select {
    background: var(--dark); border: 1px solid var(--border);
    color: var(--text); font-family: var(--mono); font-size: 0.82rem;
    padding: 0.6rem 0.8rem; outline: none; width: 100%;
    transition: border-color 0.2s; cursor: pointer;
  }
  .input-select:focus { border-color: var(--green); }

  .checkbox-row { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
  .checkbox-box {
    width: 18px; height: 18px; border: 1px solid var(--border);
    background: var(--dark); display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: 0.7rem; color: var(--green);
    flex-shrink: 0; cursor: pointer; transition: all 0.2s;
  }
  .checkbox-box.checked { border-color: var(--green); background: rgba(0,255,136,0.1); }
  .checkbox-label { font-size: 0.82rem; color: var(--text); }

  .result-card {
    margin-top: 1rem; padding: 1rem;
    border: 1px solid var(--border); background: var(--dark);
    font-family: var(--mono); font-size: 0.75rem;
  }
  .result-card.success { border-color: var(--green); background: rgba(0,255,136,0.04); }
  .result-card.blocked { border-color: var(--red); background: rgba(255,51,85,0.04); }
  .result-title { font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.05em; }
  .result-row { display: flex; justify-content: space-between; color: var(--text-dim); margin-bottom: 3px; }
  .result-row span:last-child { color: var(--text); }
`;

// ─── PIPELINE STAGES DATA ─────────────────────────────────────────────────────
const PIPELINE_STAGES_INFO = [
  { num: "01", icon: "⬇", name: "Checkout", desc: "Pull source from GitHub", type: "info" },
  { num: "02", icon: "🔍", name: "Lint", desc: "flake8 — PEP8 compliance", type: "pass" },
  { num: "03", icon: "🧪", name: "Test", desc: "pytest --cov ≥ 70%", type: "pass" },
  { num: "04", icon: "🛡", name: "Dependency Scan", desc: "Trivy → requirements.txt", type: "warn" },
  { num: "05", icon: "🐳", name: "Docker Build", desc: "non-root slim image", type: "info" },
  { num: "06", icon: "🔬", name: "Image Scan", desc: "Trivy → OS + packages", type: "pass" },
  { num: "07", icon: "📋", name: "SBOM Generate", desc: "Syft → spdx.json", type: "info" },
  { num: "08", icon: "✍", name: "Sign Image", desc: "Cosign keyless signing", type: "pass" },
  { num: "09", icon: "🚀", name: "Deploy", desc: "Only if ALL gates pass", type: "pass" },
];

const ARCH_LAYERS = [
  { title: "API Layer", files: ["health.py", "auth.py", "pipelines.py", "scans.py", "deployments.py"] },
  { title: "Service Layer", files: ["auth_service.py", "pipeline_service.py", "scan_service.py", "deployment_service.py"] },
  { title: "Repository Layer", files: ["base_repository.py", "json_repository.py", "user_repository.py", "scan_repository.py"] },
  { title: "Data Store", files: ["users.json", "pipelines.json", "scan_reports.json", "deployments.json"] },
];

const RUNNER_STAGES = [
  "Checkout code",
  "Install dependencies",
  "Run flake8 lint",
  "Run pytest suite",
  "Trivy dep scan",
  "Docker build",
  "Trivy image scan",
  "Generate SBOM",
  "Cosign sign",
  "Deploy",
];

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const shortDate = (iso) => new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

function useTypewriter(text, speed = 40) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    setDisplayed("");
    let i = 0;
    const iv = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(iv);
    }, speed);
    return () => clearInterval(iv);
  }, [text]);
  return displayed;
}

// ─── NAV ─────────────────────────────────────────────────────────────────────
function Nav({ onNav }) {
  return (
    <nav className="nav">
      <div className="nav-logo">
        <span className="bracket">[</span>DevGuard<span className="bracket">]</span>
      </div>
      <div className="nav-links">
        {["Hero", "Architecture", "Demo", "Dashboard"].map(s => (
          <a key={s} onClick={() => onNav(s.toLowerCase())}>{s}</a>
        ))}
      </div>
      <div className="nav-badge">v1.0.0</div>
    </nav>
  );
}

// ─── HERO ─────────────────────────────────────────────────────────────────────
function Hero({ onNav }) {
  const typed = useTypewriter("Zero-Trust Supply Chain Security Pipeline", 35);
  return (
    <section id="hero" className="hero">
      <div className="hero-grid" />
      <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div className="hero-tag fade-in fade-in-1">DevSecOps Platform</div>
        <h1 className="hero-title fade-in fade-in-2 glitch" data-text="DEVGUARD">
          DEV<span>GUARD</span>
        </h1>
        <div className="hero-subtitle-line fade-in fade-in-2">
          {typed}<span className="cursor" />
        </div>
        <p className="hero-desc fade-in fade-in-3">
          A control system for build trust. Every code change passes lint, tests, vulnerability
          scans, SBOM generation, and cryptographic image signing before a single byte reaches production.
        </p>
        <div className="hero-ctas fade-in fade-in-4">
          <button className="btn-primary" onClick={() => onNav("demo")}>Run Live Demo</button>
          <button className="btn-secondary" onClick={() => onNav("architecture")}>View Architecture</button>
        </div>
        <div className="hero-stats fade-in fade-in-4">
          {[["9", "Pipeline Stages"], ["3", "Security Scans"], ["0", "Untrusted Deploys"], ["100%", "Sign Coverage"]].map(([n, l]) => (
            <div className="stat" key={l}>
              <span className="stat-num">{n}</span>
              <span className="stat-label">{l}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="hero-scroll">▼ scroll</div>
    </section>
  );
}

// ─── ARCHITECTURE ─────────────────────────────────────────────────────────────
function Architecture() {
  const [activeStage, setActiveStage] = useState(null);
  return (
    <section id="architecture" className="arch-section">
      <div className="container">
        <div className="section-header">
          <div className="section-tag">// system design</div>
          <h2 className="section-title">How It <span>Works</span></h2>
          <p className="section-desc">9-stage pipeline with hard security gates at every step</p>
        </div>
        <div className="arch-grid">
          <div>
            <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--green)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "1rem" }}>
              CI/CD Pipeline Stages
            </div>
            <div className="pipeline-flow">
              {PIPELINE_STAGES_INFO.map((stage, i) => (
                <div key={i}>
                  <div
                    className={`pipeline-stage ${activeStage === i ? "active" : ""}`}
                    onMouseEnter={() => setActiveStage(i)}
                    onMouseLeave={() => setActiveStage(null)}
                  >
                    <span className="stage-num">{stage.num}</span>
                    <span className="stage-icon">{stage.icon}</span>
                    <div className="stage-info">
                      <div className="stage-name">{stage.name}</div>
                      <div className="stage-desc">{stage.desc}</div>
                    </div>
                    <span className={`stage-badge ${stage.type === "pass" ? "badge-pass" : stage.type === "warn" ? "badge-run" : "badge-info"}`}>
                      {stage.type === "pass" ? "gate" : stage.type === "warn" ? "scan" : "step"}
                    </span>
                  </div>
                  {i < PIPELINE_STAGES_INFO.length - 1 && (
                    <div className={`connector ${activeStage === i ? "active" : ""}`} />
                  )}
                </div>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--green)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "1rem" }}>
              Application Architecture
            </div>
            <div className="arch-layers">
              {ARCH_LAYERS.map((layer, i) => (
                <div key={i}>
                  <div className="arch-layer">
                    <div className="layer-title">{layer.title}</div>
                    <div className="layer-files">
                      {layer.files.map(f => <span key={f} className="file-chip">{f}</span>)}
                    </div>
                  </div>
                  {i < ARCH_LAYERS.length - 1 && <div className="layer-arrow">↓</div>}
                </div>
              ))}
            </div>
            <div style={{ marginTop: "2rem", background: "var(--panel)", border: "1px solid var(--border)", padding: "1.2rem" }}>
              <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--green)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "0.75rem" }}>Zero-Trust Policy</div>
              {[
                { label: "signed = false", result: "BLOCKED", ok: false },
                { label: "critical_count > 0", result: "BLOCKED", ok: false },
                { label: "scan status = failed", result: "BLOCKED", ok: false },
                { label: "no scans found", result: "BLOCKED", ok: false },
                { label: "all gates passed", result: "ALLOWED", ok: true },
              ].map(r => (
                <div key={r.label} style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--mono)", fontSize: "0.72rem", padding: "0.3rem 0", borderBottom: "1px solid rgba(26,32,48,0.5)" }}>
                  <span style={{ color: "var(--text-dim)" }}>{r.label}</span>
                  <span style={{ color: r.ok ? "var(--green)" : "var(--red)" }}>→ {r.result}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── DEMO ─────────────────────────────────────────────────────────────────────
function Demo() {
  const [apiUrl, setApiUrl] = useState("");
  const [isLive, setIsLive] = useState(false);
  const [tab, setTab] = useState("auth");
  const [logs, setLogs] = useState([]);
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [authMode, setAuthMode] = useState("login");
  const [token, setToken] = useState(null);
  const [authStatus, setAuthStatus] = useState(null);
  const [pipelineForm, setPipelineForm] = useState({ commit_id: "", branch: "main", triggered_by: "github-actions" });
  const [scanForm, setScanForm] = useState({ pipeline_id: "", scan_type: "dependency", tool: "trivy", status: "passed", critical_count: 0, high_count: 0 });
  const [deployForm, setDeployForm] = useState({ pipeline_id: "", image_tag: "", signed: true, environment: "production" });
  const [runnerState, setRunnerState] = useState("idle"); // idle | running | done | failed
  const [runnerStages, setRunnerStages] = useState(RUNNER_STAGES.map(n => ({ name: n, state: "pending" })));
  const [lastResult, setLastResult] = useState(null);
  const logRef = useRef(null);
  const api = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  useEffect(() => {
    if (apiUrl.trim()) {
      api.current = createApiClient(apiUrl.trim());
      setIsLive(true);
    } else {
      setIsLive(false);
    }
  }, [apiUrl]);

  const addLog = useCallback((msg, type = "info") => {
    const time = new Date().toLocaleTimeString("en-US", { hour12: false });
    setLogs(l => [...l, { time, msg, type }]);
  }, []);

  const clearLogs = () => setLogs([]);

  // ── AUTH ──
  const handleAuth = async () => {
    clearLogs();
    addLog(`$ devguard auth ${authMode}`, "cmd");
    addLog(`connecting to ${isLive ? apiUrl : "mock://devguard-api"}...`, "info");
    await sleep(500);

    if (isLive) {
      try {
        const endpoint = authMode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
        const res = await api.current.post(endpoint, authForm);
        if (res.success) {
          if (authMode === "login" && res.data?.access_token) {
            api.current.setToken(res.data.access_token);
            setToken(res.data.access_token);
          }
          addLog(`✓ ${res.message || "Success"}`, "success");
          setAuthStatus({ ok: true, msg: authMode === "login" ? "Authenticated. JWT token stored." : "User created." });
        } else {
          addLog(`✗ ${res.message || "Failed"}`, "error");
          setAuthStatus({ ok: false, msg: res.message });
        }
      } catch (e) {
        addLog(`✗ Connection failed: ${e.message}`, "error");
        setAuthStatus({ ok: false, msg: "Cannot reach API. Check URL and CORS." });
      }
    } else {
      await sleep(400);
      addLog(`POST /api/v1/auth/${authMode} → 200 OK`, "success");
      await sleep(200);
      addLog(`✓ JWT token issued`, "success");
      addLog(`eyJhbGciOiJIUzI1NiJ9.eyJpZCI6InVzci1kZW1vIn0.xxx`, "warn");
      setToken("mock-jwt-token");
      setAuthStatus({ ok: true, msg: "Simulated auth. Token stored in memory." });
    }
  };

  // ── PIPELINE RUNNER ──
  const runPipeline = async () => {
    clearLogs();
    setRunnerState("running");
    setLastResult(null);
    const stages = RUNNER_STAGES.map(n => ({ name: n, state: "pending" }));
    setRunnerStages([...stages]);

    const hasCritical = scanForm.critical_count > 0 || scanForm.status === "failed";
    const willDeploy = deployForm.signed && !hasCritical;

    addLog("$ github-actions trigger: push to main", "cmd");
    await sleep(300);

    for (let i = 0; i < RUNNER_STAGES.length; i++) {
      stages[i].state = "running";
      setRunnerStages([...stages]);
      addLog(`[${String(i + 1).padStart(2, "0")}] Running: ${RUNNER_STAGES[i]}...`, "info");
      await sleep(600 + Math.random() * 400);

      // Simulate failure conditions
      if (i === 8 && !deployForm.signed) {
        stages[i].state = "failed";
        setRunnerStages([...stages]);
        addLog(`✗ Image signing FAILED — deployment blocked`, "error");
        setRunnerState("failed");
        setLastResult({ ok: false, reason: "Image not signed (signed: false)" });
        return;
      }
      if (i === 6 && hasCritical) {
        stages[i].state = "failed";
        setRunnerStages([...stages]);
        addLog(`✗ CRITICAL vulnerabilities found: ${scanForm.critical_count} — deployment blocked`, "error");
        setRunnerState("failed");
        setLastResult({ ok: false, reason: `${scanForm.critical_count} critical vulnerabilities found` });
        return;
      }

      stages[i].state = "done";
      setRunnerStages([...stages]);
      addLog(`✓ ${RUNNER_STAGES[i]} complete`, "success");

      if (isLive && token) {
        if (i === 0) {
          try {
            const res = await api.current.post("/api/v1/pipelines", {
              commit_id: pipelineForm.commit_id || "demo-" + Date.now().toString(16).slice(-6),
              branch: pipelineForm.branch,
              status: "running",
              triggered_by: pipelineForm.triggered_by,
            });
            if (res.data?.id) {
              setScanForm(f => ({ ...f, pipeline_id: res.data.id }));
              setDeployForm(f => ({ ...f, pipeline_id: res.data.id }));
              addLog(`  pipeline_id: ${res.data.id}`, "warn");
            }
          } catch { addLog("  (live API call failed, continuing simulation)", "warn"); }
        }
      }
    }

    if (willDeploy) {
      addLog("🚀 All gates passed. Deploying...", "success");
      addLog(`✓ devguard-api:${(pipelineForm.commit_id || "demo").slice(0, 7)} → production`, "success");
      setRunnerState("done");
      setLastResult({ ok: true, image: `devguard-api:${(pipelineForm.commit_id || "demo").slice(0, 7)}`, env: deployForm.environment });
    }
  };

  const stageColors = { pending: "var(--text-dim)", running: "var(--yellow)", done: "var(--green)", failed: "var(--red)" };

  return (
    <section id="demo" className="demo-section">
      <div className="container">
        <div className="section-header">
          <div className="section-tag">// interactive demo</div>
          <h2 className="section-title">Live <span>Demo</span></h2>
          <p className="section-desc">Simulate or connect your real DevGuard API</p>
        </div>

        <div className="demo-config">
          <span className="demo-config-label">API_URL=</span>
          <input
            className="demo-config-input"
            placeholder="http://localhost:5000  (leave empty for simulation)"
            value={apiUrl}
            onChange={e => setApiUrl(e.target.value)}
          />
          <span className={`demo-mode-badge ${isLive ? "mode-live" : "mode-sim"}`}>
            {isLive ? "● LIVE" : "○ SIM"}
          </span>
        </div>

        <div className="demo-grid">
          {/* LEFT: Controls */}
          <div className="demo-panel">
            <div className="demo-panel-header">
              <span className="demo-panel-title">// controls</span>
              <span className="demo-panel-status">{isLive ? "live mode" : "simulation"}</span>
            </div>
            <div className="demo-tabs">
              {["auth", "pipeline", "scan"].map(t => (
                <button key={t} className={`demo-tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                  {t}
                </button>
              ))}
            </div>

            {tab === "auth" && (
              <div className="demo-form">
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {["login", "register"].map(m => (
                    <button key={m} onClick={() => setAuthMode(m)}
                      style={{ flex: 1, padding: "0.5rem", fontFamily: "var(--mono)", fontSize: "0.7rem", letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer", background: authMode === m ? "var(--green)" : "transparent", color: authMode === m ? "var(--black)" : "var(--text-dim)", border: "1px solid " + (authMode === m ? "var(--green)" : "var(--border)"), transition: "all 0.2s" }}>
                      {m}
                    </button>
                  ))}
                </div>
                <div className="form-group">
                  <label className="form-label">Username</label>
                  <input className="form-input" value={authForm.username} onChange={e => setAuthForm(f => ({ ...f, username: e.target.value }))} placeholder="admin" />
                </div>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input className="form-input" type="password" value={authForm.password} onChange={e => setAuthForm(f => ({ ...f, password: e.target.value }))} placeholder="StrongPass123!" />
                </div>
                {authStatus && <div className={authStatus.ok ? "form-success" : "form-error"}>{authStatus.msg}</div>}
                <button className="btn-primary" style={{ width: "100%" }} onClick={handleAuth}>
                  {authMode === "login" ? "Login → Get Token" : "Register Account"}
                </button>
                {token && <div style={{ fontFamily: "var(--mono)", fontSize: "0.62rem", color: "var(--green)", wordBreak: "break-all" }}>✓ token: {token.slice(0, 40)}...</div>}
              </div>
            )}

            {tab === "pipeline" && (
              <div className="demo-form">
                <div className="form-group">
                  <label className="form-label">Commit ID</label>
                  <input className="form-input" value={pipelineForm.commit_id} onChange={e => setPipelineForm(f => ({ ...f, commit_id: e.target.value }))} placeholder="3f8e21a" />
                </div>
                <div className="form-group">
                  <label className="form-label">Branch</label>
                  <select className="input-select" value={pipelineForm.branch} onChange={e => setPipelineForm(f => ({ ...f, branch: e.target.value }))}>
                    {["main", "develop", "feature/auth", "hotfix/sec"].map(b => <option key={b}>{b}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Critical Vulnerabilities</label>
                  <input className="form-input" type="number" min="0" value={scanForm.critical_count}
                    onChange={e => setScanForm(f => ({ ...f, critical_count: parseInt(e.target.value) || 0 }))} />
                  <span style={{ fontFamily: "var(--mono)", fontSize: "0.62rem", color: scanForm.critical_count > 0 ? "var(--red)" : "var(--text-dim)" }}>
                    {scanForm.critical_count > 0 ? "⚠ Deploy will be blocked" : "✓ No criticals"}
                  </span>
                </div>
                <div className="checkbox-row" onClick={() => setDeployForm(f => ({ ...f, signed: !f.signed }))}>
                  <div className={`checkbox-box ${deployForm.signed ? "checked" : ""}`}>{deployForm.signed ? "✓" : ""}</div>
                  <span className="checkbox-label">Sign image with Cosign</span>
                </div>
                {!deployForm.signed && <div className="form-error">⚠ Unsigned image — deploy will be blocked</div>}
                <div className="form-group">
                  <label className="form-label">Target Environment</label>
                  <select className="input-select" value={deployForm.environment} onChange={e => setDeployForm(f => ({ ...f, environment: e.target.value }))}>
                    {["production", "staging", "development"].map(e => <option key={e}>{e}</option>)}
                  </select>
                </div>
                <button className="btn-primary" style={{ width: "100%" }}
                  onClick={runPipeline}
                  disabled={runnerState === "running"}>
                  {runnerState === "running" ? "Running Pipeline..." : "▶ Run Full Pipeline"}
                </button>
              </div>
            )}

            {tab === "scan" && (
              <div className="demo-form">
                <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--text-dim)", lineHeight: 1.7 }}>
                  <div style={{ color: "var(--green)", marginBottom: "0.5rem" }}>POST /api/v1/scans</div>
                  <pre style={{ background: "var(--dark)", padding: "1rem", fontSize: "0.7rem", overflowX: "auto", color: "var(--text)" }}>{JSON.stringify({
                    pipeline_id: scanForm.pipeline_id || "pl-xxxxxxxx",
                    scan_type: scanForm.scan_type,
                    tool: scanForm.tool,
                    status: scanForm.critical_count > 0 ? "failed" : "passed",
                    critical_count: scanForm.critical_count,
                    high_count: scanForm.high_count || 0,
                  }, null, 2)}</pre>
                </div>
                <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--text-dim)", lineHeight: 1.7 }}>
                  <div style={{ color: "var(--green)", marginBottom: "0.5rem" }}>POST /api/v1/deployments</div>
                  <pre style={{ background: "var(--dark)", padding: "1rem", fontSize: "0.7rem", overflowX: "auto", color: "var(--text)" }}>{JSON.stringify({
                    pipeline_id: deployForm.pipeline_id || "pl-xxxxxxxx",
                    image_tag: `devguard-api:${pipelineForm.commit_id || "latest"}`,
                    signed: deployForm.signed,
                    environment: deployForm.environment,
                    status: "deployed",
                  }, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Terminal + Runner */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div className="terminal">
              <div className="terminal-header">
                <div className="term-dot" style={{ background: "#ff5f56" }} />
                <div className="term-dot" style={{ background: "#ffbd2e" }} />
                <div className="term-dot" style={{ background: "#27c93f" }} />
                <span className="term-title">devguard-pipeline — bash</span>
                <button onClick={clearLogs} style={{ marginLeft: "auto", background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontFamily: "var(--mono)", fontSize: "0.65rem" }}>clear</button>
              </div>
              <div className="terminal-body" ref={logRef}>
                {logs.length === 0 && (
                  <div className="log-line log-info" style={{ color: "var(--text-dim)" }}>
                    DevGuard Pipeline Console — ready<span className="cursor" />
                  </div>
                )}
                {logs.map((l, i) => (
                  <div key={i} className={`log-line log-${l.type}`}>
                    <span className="log-time">{l.time}</span>
                    <span>{l.msg}</span>
                  </div>
                ))}
                {logs.length > 0 && <div className="log-line"><span className="cursor" /></div>}
              </div>
            </div>

            <div className="demo-panel">
              <div className="demo-panel-header">
                <span className="demo-panel-title">// pipeline stages</span>
                <span className="demo-panel-status" style={{ color: runnerState === "done" ? "var(--green)" : runnerState === "failed" ? "var(--red)" : "var(--text-dim)" }}>
                  {runnerState}
                </span>
              </div>
              <div className="pipeline-runner">
                <div className="runner-stages">
                  {runnerStages.map((s, i) => (
                    <div key={i} className={`runner-stage ${s.state}`}>
                      <span className="runner-stage-name" style={{ color: stageColors[s.state] || "var(--text-dim)" }}>
                        {s.name}
                      </span>
                      <span className="runner-stage-time">
                        {s.state === "done" ? "✓" : s.state === "failed" ? "✗" : s.state === "running" ? "..." : "—"}
                      </span>
                    </div>
                  ))}
                </div>
                {lastResult && (
                  <div className={`result-card ${lastResult.ok ? "success" : "blocked"}`}>
                    <div className="result-title" style={{ color: lastResult.ok ? "var(--green)" : "var(--red)" }}>
                      {lastResult.ok ? "✓ DEPLOYMENT SUCCESSFUL" : "✗ DEPLOYMENT BLOCKED"}
                    </div>
                    {lastResult.ok ? (
                      <>
                        <div className="result-row"><span>image</span><span>{lastResult.image}</span></div>
                        <div className="result-row"><span>environment</span><span>{lastResult.env}</span></div>
                        <div className="result-row"><span>signed</span><span>true</span></div>
                      </>
                    ) : (
                      <div className="result-row"><span>reason</span><span style={{ color: "var(--red)" }}>{lastResult.reason}</span></div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── DASHBOARD ────────────────────────────────────────────────────────────────
function Dashboard() {
  const [data, setData] = useState({
    pipelines: MOCK_PIPELINES,
    scans: MOCK_SCANS,
    deployments: MOCK_DEPLOYMENTS,
    report: MOCK_REPORT,
  });

  const { pipelines, scans, deployments, report } = data;

  const scanChartData = [
    { name: "Passed", value: report.passed, fill: "#00ff88" },
    { name: "Failed", value: report.failed, fill: "#ff3355" },
  ];

  const vulnChartData = [
    { name: "Critical", count: report.critical_vulnerabilities, fill: "#ff3355" },
    { name: "High", count: report.high_vulnerabilities, fill: "#ffcc00" },
  ];

  const trendData = [
    { day: "Mon", passed: 3, failed: 1 },
    { day: "Tue", passed: 4, failed: 0 },
    { day: "Wed", passed: 2, failed: 2 },
    { day: "Thu", passed: 5, failed: 1 },
    { day: "Fri", passed: 4, failed: 0 },
    { day: "Sat", passed: 3, failed: 0 },
    { day: "Sun", passed: 4, failed: 0 },
  ];

  const trusted = report.trust_status === "trusted";

  return (
    <section id="dashboard" className="dash-section">
      <div className="container">
        <div className="section-header">
          <div className="section-tag">// security dashboard</div>
          <h2 className="section-title">Security <span>Metrics</span></h2>
          <p className="section-desc">Real-time overview of pipeline health and trust status</p>
        </div>

        <div className={`trust-banner ${trusted ? "" : "danger"}`}>
          <div className="trust-status">
            <div className={`trust-indicator ${trusted ? "" : "danger"}`} />
            SYSTEM TRUST STATUS: {trusted ? "TRUSTED" : "UNTRUSTED"}
          </div>
          <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--text-dim)" }}>
            {trusted ? "All security checks passing. Deployments authorized." : "Critical vulnerabilities detected. Deployments blocked."}
          </div>
        </div>

        <div className="metrics-row">
          {[
            { label: "Total Pipelines", value: pipelines.length, sub: `${pipelines.filter(p => p.status === "passed").length} passed`, color: "green" },
            { label: "Total Scans", value: report.total_scans, sub: `${report.passed} passed / ${report.failed} failed`, color: "" },
            { label: "Critical Vulns", value: report.critical_vulnerabilities, sub: "across all scans", color: report.critical_vulnerabilities > 0 ? "red" : "green", danger: report.critical_vulnerabilities > 0 },
            { label: "Signed Deploys", value: deployments.filter(d => d.signed).length, sub: `of ${deployments.length} total`, color: "green" },
          ].map((m, i) => (
            <div key={i} className={`metric-card ${m.danger ? "danger" : ""}`}>
              <div className="metric-label">{m.label}</div>
              <div className={`metric-value ${m.color}`}>{m.value}</div>
              <div className="metric-sub">{m.sub}</div>
            </div>
          ))}
        </div>

        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-title">// scan results</div>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={scanChartData} dataKey="value" cx="50%" cy="50%" outerRadius={65} innerRadius={35}>
                  {scanChartData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#0e1114", border: "1px solid #1a2030", fontFamily: "monospace", fontSize: "0.72rem" }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", justifyContent: "center", gap: "1.5rem" }}>
              {scanChartData.map(d => (
                <div key={d.name} style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ width: 8, height: 8, background: d.fill, borderRadius: 2 }} />
                  <span style={{ color: "var(--text-dim)" }}>{d.name}: <span style={{ color: d.fill }}>{d.value}</span></span>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-title">// vulnerabilities found</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={vulnChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                <XAxis dataKey="name" tick={{ fill: "#5a7090", fontFamily: "monospace", fontSize: 11 }} axisLine={false} />
                <YAxis tick={{ fill: "#5a7090", fontFamily: "monospace", fontSize: 11 }} axisLine={false} />
                <Tooltip contentStyle={{ background: "#0e1114", border: "1px solid #1a2030", fontFamily: "monospace", fontSize: "0.72rem" }} />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {vulnChartData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="chart-title">// pipeline trend (7d)</div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gPass" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gFail" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff3355" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ff3355" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                <XAxis dataKey="day" tick={{ fill: "#5a7090", fontFamily: "monospace", fontSize: 11 }} axisLine={false} />
                <YAxis tick={{ fill: "#5a7090", fontFamily: "monospace", fontSize: 11 }} axisLine={false} />
                <Tooltip contentStyle={{ background: "#0e1114", border: "1px solid #1a2030", fontFamily: "monospace", fontSize: "0.72rem" }} />
                <Area type="monotone" dataKey="passed" stroke="#00ff88" fill="url(#gPass)" strokeWidth={2} />
                <Area type="monotone" dataKey="failed" stroke="#ff3355" fill="url(#gFail)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="pipelines-table" style={{ marginTop: "2rem" }}>
          <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--green)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "0.75rem" }}>
            Recent Pipeline Runs
          </div>
          <div className="table-header">
            <span>Pipeline ID</span><span>Commit</span><span>Branch</span><span>Triggered</span><span>Status</span>
          </div>
          {pipelines.map(p => (
            <div key={p.id} className={`table-row status-${p.status}`}>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--text-dim)" }}>{p.id}</span>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--blue)" }}>{p.commit_id}</span>
              <span style={{ fontSize: "0.8rem" }}>{p.branch}</span>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.68rem", color: "var(--text-dim)" }}>{p.triggered_by}</span>
              <span><span className="status-dot">{p.status}</span></span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: "2rem" }}>
          <div style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--green)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "0.75rem" }}>
            Recent Deployments
          </div>
          <div className="table-header" style={{ gridTemplateColumns: "1fr 1fr 1fr 80px 80px" }}>
            <span>Deploy ID</span><span>Image Tag</span><span>Environment</span><span>Signed</span><span>Status</span>
          </div>
          {deployments.map(d => (
            <div key={d.id} className="table-row" style={{ gridTemplateColumns: "1fr 1fr 1fr 80px 80px" }}>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--text-dim)" }}>{d.id}</span>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--blue)" }}>{d.image_tag}</span>
              <span style={{ fontSize: "0.8rem" }}>{d.environment}</span>
              <span style={{ color: d.signed ? "var(--green)" : "var(--red)", fontFamily: "var(--mono)", fontSize: "0.72rem" }}>{d.signed ? "✓ yes" : "✗ no"}</span>
              <span style={{ color: "var(--green)", fontFamily: "var(--mono)", fontSize: "0.72rem" }}>{d.status}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────
export default function App() {
  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      <style>{styles}</style>
      <div className="app">
        <Nav onNav={scrollTo} />
        <Hero onNav={scrollTo} />
        <Architecture />
        <Demo />
        <Dashboard />
        <footer className="footer">
          <span>DevGuard</span> — Zero-Trust Supply Chain Security Pipeline &nbsp;·&nbsp;
          Built with Flask · Docker · GitHub Actions · Trivy · Cosign · Terraform
        </footer>
      </div>
    </>
  );
}
