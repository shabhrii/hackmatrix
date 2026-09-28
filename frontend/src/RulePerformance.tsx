import { useEffect, useState } from 'react';

export function RulePerformance() {
  const [rules, setRules] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/stats/rules').then(res => res.json()).then(data => setRules(data));
  }, []);

  return (
    <div className="p-4">
      <h1 className="page-title">Rule Performance</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
            <th style={{ padding: '8px 4px' }}>Rule ID</th>
            <th>Scenarios Detected</th>
            <th>Benign Quiet</th>
          </tr>
        </thead>
        <tbody>
          {rules.map((r: any) => (
            <tr key={r.rule_id} style={{ borderBottom: '1px solid var(--border)' }}>
              <td style={{ padding: '8px 4px' }} className="mono">{r.rule_id}</td>
              <td>{r.scenarios_detected}</td>
              <td style={{ color: r.benign_quiet ? 'var(--success)' : 'var(--critical)' }}>
                {r.benign_quiet ? 'PASS' : 'FAIL'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
