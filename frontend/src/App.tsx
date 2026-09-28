import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';
import { AlertQueue } from './AlertQueue';
import { AlertDetail } from './AlertDetail';
import { Cases, CaseDetail } from './Cases';
import { Overview } from './Overview';
import { RulePerformance } from './RulePerformance';
import { DataReplay } from './DataReplay';

const ROLES = ['analyst', 'supervisor', 'admin'] as const;
type Role = (typeof ROLES)[number];

function Shell() {
  const [role, setRole] = useState<Role>('analyst');

  const navItems = [
    { to: '/', label: 'Overview' },
    { to: '/alerts', label: 'Alert queue' },
    { to: '/graph', label: 'Investigation graph' },
    { to: '/cases', label: 'Cases' },
    { to: '/rules', label: 'Rule performance' },
    { to: '/replay', label: 'Data replay' },
  ];

  return (
    <div className="shell">
      <div className="topbar">
        <span className="topbar-tenant">Deccan Cooperative Bank (synthetic)</span>
        <span className="topbar-item">Replay</span>
        <span className="topbar-item">Fresh</span>
        <span className="topbar-spacer" />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as Role)}
          aria-label="Switch user role"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <button onClick={() => fetch('/api/demo/reset', { method: 'POST' })}>
          Reset demo
        </button>
      </div>

      <div className="banner">
        Synthetic hackathon data — not for real financial decisions.
      </div>

      <nav className="nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `nav-item${isActive ? ' active' : ''}`
            }
            end={item.to === '/'}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/alerts" element={<AlertQueue />} />
          <Route path="/alerts/:id" element={<AlertDetail />} />
          <Route path="/graph" element={<Placeholder title="Investigation graph" />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          <Route path="/rules" element={<RulePerformance />} />
          <Route path="/replay" element={<DataReplay />} />
        </Routes>
      </main>
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return <h1 className="page-title">{title}</h1>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
