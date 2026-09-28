import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, AlertTriangle, Info, Search, Filter } from 'lucide-react';

export interface Alert {
  alert_id: string;
  title: string;
  severity: string;
  confidence: number;
  status: string;
  owner_id: string | null;
  employee_id: string | null;
  account_id: string | null;
  customer_id: string | null;
  rule_ids: string;
  evidence_count: number;
  created_at: string;
}

export function AlertQueue() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/alerts')
      .then(res => res.json())
      .then(data => {
        setAlerts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch alerts:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-4">Loading queue...</div>;
  }

  const renderSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return <AlertCircle size={16} color="var(--high)" />;
      case 'medium': return <AlertTriangle size={16} color="var(--medium)" />;
      default: return <Info size={16} color="var(--informational)" />;
    }
  };

  const calculateAge = (timestamp: string) => {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return "Unknown";
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  const getSubject = (a: Alert) => {
    return a.employee_id || a.account_id || a.customer_id || 'Unknown';
  };

  const handleKeyDown = (e: React.KeyboardEvent, alert_id: string) => {
    if (e.key === 'Enter') {
      navigate(`/alerts/${alert_id}`);
    }
  };

  return (
    <div>
      <h1 className="page-title">Alert queue</h1>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Filter size={14} /> Filter
        </button>
        <button style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Search size={14} /> Search
        </button>
      </div>

      <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
        <table>
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th>Alert</th>
              <th>Subject</th>
              <th>Rules</th>
              <th style={{ textAlign: 'right' }}>Evidence</th>
              <th style={{ textAlign: 'right' }}>Confidence</th>
              <th>Age</th>
              <th>Owner</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a, i) => (
              <tr 
                key={a.alert_id} 
                tabIndex={0} 
                onClick={() => navigate(`/alerts/${a.alert_id}`)}
                onKeyDown={(e) => handleKeyDown(e, a.alert_id)}
                style={{ cursor: 'pointer' }}
                autoFocus={i === 0}
              >
                <td style={{ textAlign: 'center' }}>{renderSeverityIcon(a.severity)}</td>
                <td style={{ fontWeight: 500 }}>{a.title}</td>
                <td className="mono">{getSubject(a)}</td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {JSON.parse(a.rule_ids || '[]').map((r: string) => (
                      <span key={r} style={{ background: 'var(--surface)', padding: '2px 6px', borderRadius: '2px', border: '1px solid var(--border)', fontSize: '11px', color: 'var(--text-muted)' }} className="mono">{r}</span>
                    ))}
                  </div>
                </td>
                <td style={{ textAlign: 'right' }}>{a.evidence_count}</td>
                <td style={{ textAlign: 'right' }}>{Math.round(a.confidence * 100)}%</td>
                <td>{calculateAge(a.created_at)}</td>
                <td style={{ color: 'var(--text-muted)' }}>{a.owner_id || 'Unassigned'}</td>
                <td style={{ textTransform: 'capitalize' }}>{a.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
