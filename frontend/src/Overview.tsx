import { useEffect, useState } from 'react';

export function Overview() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/stats/overview').then(res => res.json()).then(d => setData(d));
  }, []);

  if (!data) return <div className="p-4">Loading...</div>;

  const maxRule = Math.max(...Object.values(data.by_rule || {x:1}) as number[]);

  return (
    <div className="p-4">
      <h1 className="page-title">Overview</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--surface)', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Open High Alerts</div>
          <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--critical)' }}>{data.open_high}</div>
        </div>
        <div style={{ background: 'var(--surface)', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Open Med Alerts</div>
          <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--warning)' }}>{data.open_med}</div>
        </div>
        <div style={{ background: 'var(--surface)', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Median Evidence</div>
          <div style={{ fontSize: '24px', fontWeight: 600 }}>{data.median_evidence}</div>
        </div>
        <div style={{ background: 'var(--surface)', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>False Positives</div>
          <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--success)', marginTop: '8px' }}>{data.fp_test_status}</div>
        </div>
      </div>

      <div style={{ background: 'var(--surface)', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginBottom: '24px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px' }}>Open Alerts by Rule</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {Object.entries(data.by_rule).map(([rule, count]: [string, any]) => (
            <div key={rule} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '80px', fontSize: '12px' }} className="mono">{rule}</div>
              <div style={{ flex: 1, background: 'var(--bg)', height: '12px', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ background: 'var(--primary)', height: '100%', width: `${(count / maxRule) * 100}%` }} />
              </div>
              <div style={{ width: '40px', fontSize: '12px', textAlign: 'right' }}>{count}</div>
            </div>
          ))}
        </div>
      </div>
      
      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
        Last Ingestion: {new Date(Number(data.last_ingestion) * 1000).toLocaleString()}
      </div>
    </div>
  );
}
