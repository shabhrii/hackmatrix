import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export function Cases() {
  const [cases, setCases] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('/api/cases')
      .then(res => res.json())
      .then(data => setCases(data));
  }, []);

  return (
    <div className="p-4">
      <h1 className="page-title">Cases</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
            <th style={{ padding: '8px 4px' }}>Case ID</th>
            <th>Status</th>
            <th>Owner</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c: any) => (
            <tr 
              key={c.case_id}
              style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
              onClick={() => navigate(`/cases/${c.case_id}`)}
            >
              <td style={{ padding: '8px 4px' }} className="mono">{c.case_id}</td>
              <td style={{ textTransform: 'capitalize' }}>{c.status}</td>
              <td>{c.owner_id}</td>
              <td>{new Date(Number(c.created_at) * 1000).toLocaleString()}</td>
            </tr>
          ))}
          {cases.length === 0 && (
            <tr>
              <td colSpan={4} style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)' }}>No cases found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function CaseDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [noteBody, setNoteBody] = useState('');

  useEffect(() => {
    fetch(`/api/cases/${id}`)
      .then(res => res.json())
      .then(d => setData(d));
  }, [id]);

  const addNote = () => {
    if (!noteBody.trim()) return;
    fetch(`/api/cases/${id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-user-role': 'analyst' },
      body: JSON.stringify({ body: noteBody })
    }).then(() => {
      setNoteBody('');
      fetch(`/api/cases/${id}`).then(res => res.json()).then(d => setData(d));
    });
  };

  const handleExport = () => {
    window.location.href = `/api/cases/${id}/export?format=md`;
  };

  if (!data || !data.case) return <div className="p-4">Loading case...</div>;

  return (
    <div className="p-4" style={{ display: 'flex', gap: '24px', height: '100%' }}>
      <div style={{ flex: 2 }}>
        <h1 className="page-title">Case Workspace — <span className="mono">{data.case.case_id}</span></h1>
        
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '16px', borderRadius: 'var(--radius)', marginBottom: '16px' }}>
          <h3>Status: <span style={{ textTransform: 'capitalize' }}>{data.case.status}</span></h3>
          <p>Owner: {data.case.owner_id}</p>
          <button onClick={handleExport} id="btn-export-bundle">Export Bundle</button>
        </div>

        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <h3>Notes</h3>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <input 
              type="text" 
              value={noteBody} 
              onChange={e => setNoteBody(e.target.value)} 
              placeholder="Add a note..." 
              style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', padding: '4px 8px' }}
              id="input-note"
            />
            <button onClick={addNote} id="btn-add-note">Add</button>
          </div>
          {data.notes.map((n: any) => (
            <div key={n.note_id} style={{ borderBottom: '1px solid var(--border)', padding: '8px 0' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{n.author_id} · {new Date(Number(n.created_at) * 1000).toLocaleString()}</div>
              <div>{n.body}</div>
            </div>
          ))}
        </div>
      </div>
      
      <div style={{ flex: 1 }}>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <h3>Activity Log</h3>
          {data.audit.map((a: any) => (
            <div key={a.audit_id || a.id} style={{ fontSize: '12px', marginBottom: '8px', paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
              <span className="mono" style={{ color: 'var(--text-muted)' }}>{new Date(Number(a.timestamp) * 1000).toLocaleTimeString()}</span>
              <div>{a.actor_id} performed {a.action}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
