import { useEffect, useState } from 'react';

export function DataReplay() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/stats/replay').then(res => res.json()).then(d => setData(d));
  }, []);

  if (!data) return <div className="p-4">Loading...</div>;

  return (
    <div className="p-4">
      <h1 className="page-title">Data Replay</h1>
      <div style={{ marginBottom: '24px' }}>
        <strong>Quarantined Records: </strong> <span style={{ color: data.quarantined > 0 ? 'var(--critical)' : 'var(--success)' }}>{data.quarantined}</span>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
            <th style={{ padding: '8px 4px' }}>Batch ID</th>
            <th>Records Ingested</th>
            <th>Freshness (Latest Timestamp)</th>
          </tr>
        </thead>
        <tbody>
          {data.batches.map((b: any) => (
            <tr key={b.batch_id} style={{ borderBottom: '1px solid var(--border)' }}>
              <td style={{ padding: '8px 4px' }} className="mono">{b.batch_id}</td>
              <td>{b.count}</td>
              <td>{new Date(Number(b.freshness) * 1000).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
