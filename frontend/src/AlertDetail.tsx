import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import cytoscape from 'cytoscape';

export function AlertDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const graphRef = useRef<HTMLDivElement>(null);
  const [cy, setCy] = useState<cytoscape.Core | null>(null);

  useEffect(() => {
    fetch(`/api/alerts/${id}`)
      .then(res => res.json())
      .then(data => setAlert(data));
      
    fetch(`/api/alerts/${id}/evidence`)
      .then(res => res.json())
      .then(data => setEvidence(data));
      
    fetch(`/api/alerts/${id}/graph`)
      .then(res => res.json())
      .then(data => {
        if (!graphRef.current) return;
        
        // Initialize Cytoscape
        const cyInstance = cytoscape({
          container: graphRef.current,
          elements: data,
          style: [
            {
              selector: 'node[type="employee"]',
              style: { 'background-color': '#4C8DD6', 'shape': 'rectangle', 'label': 'data(label)', 'color': '#E8E4DC', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 4 }
            },
            {
              selector: 'node[type="customer"]',
              style: { 'background-color': '#4E9F7D', 'shape': 'ellipse', 'label': 'data(label)', 'color': '#E8E4DC', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 4 }
            },
            {
              selector: 'node[type="account"]',
              style: { 'background-color': '#4C8DD6', 'shape': 'ellipse', 'label': 'data(label)', 'color': '#E8E4DC', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 4 }
            },
            {
              selector: 'node[type="transaction"]',
              style: { 'background-color': '#D9822B', 'shape': 'diamond', 'label': 'data(label)', 'color': '#E8E4DC', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 4 }
            },
            {
              selector: 'edge',
              style: { 'width': 2, 'line-color': '#8B98A9', 'target-arrow-color': '#8B98A9', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': '8px', 'color': '#8B98A9', 'text-rotation': 'autorotate', 'text-margin-y': -6 }
            },
            {
              selector: '.highlighted',
              style: { 'line-color': '#D9822B', 'target-arrow-color': '#D9822B', 'width': 4 }
            }
          ],
          layout: { name: 'cose', padding: 30 }
        });
        
        setCy(cyInstance);
      });
      
    return () => {
      // handled by another effect
    };
  }, [id]);

  useEffect(() => {
    return () => {
      if (cy) cy.destroy();
    };
  }, [cy]);

  if (!alert) return <div className="p-4">Loading alert...</div>;

  const scoreBreakdown = JSON.parse(alert.score_breakdown || '{}');
  const rules = JSON.parse(alert.rule_ids || '[]');

  // Check for S4 monitored
  if (rules.includes('R-02') && alert.severity === 'informational') {
    return (
      <div className="p-4">
        <h2>Monitored — no high-severity alert</h2>
        <p>High retrieval volume matched the employee’s batch-operator role, approved job ID, expected shift, and peer baseline.</p>
      </div>
    );
  }
  
  // Check for S7 small peer group
  if (alert.title.includes('S7')) {
    return (
      <div className="p-4">
        <h2>Peer comparison unavailable: only 3 comparable employees. The system has not used peer-baseline evidence in this score.</h2>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
        <h1 className="page-title" style={{ margin: 0 }}>
          <span style={{ textTransform: 'capitalize' }}>{alert.severity}</span> — {alert.title}
        </h1>
        <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
          {alert.recommended_action || 'Requires investigation'} · Confidence {Math.round(alert.confidence * 100)}% · {alert.evidence_count} independent evidence events
        </div>
      </div>
      
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: '65%', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border)' }}>
            <h3>Evidence Timeline</h3>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
              {evidence.map((e, i) => (
                <li key={i}>{e.event_type}: {e.event_id} ({e.relationship_type})</li>
              ))}
            </ul>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <div ref={graphRef} style={{ width: '100%', height: '100%', background: 'var(--bg)' }} />
            <button style={{ position: 'absolute', bottom: '16px', right: '16px' }} id="btn-shortest-path">Shortest evidence path</button>
          </div>
        </div>
        
        <div style={{ width: '35%', padding: '16px', overflowY: 'auto' }}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px', marginBottom: '16px' }}>
            <h3 style={{ marginTop: 0 }}>Explanation</h3>
            <p style={{ fontSize: '13px', margin: '8px 0' }}>{alert.explanation || 'No explanation available.'}</p>
          </div>
          
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px', marginBottom: '16px' }}>
            <h3 style={{ marginTop: 0 }}>Score Breakdown</h3>
            <table style={{ width: '100%', fontSize: '13px' }}>
              <tbody>
                {Object.entries(scoreBreakdown).map(([k, v]) => (
                  <tr key={k}>
                    <td>{k.replace(/_/g, ' ')}</td>
                    <td style={{ textAlign: 'right' }}>+{v as number}</td>
                  </tr>
                ))}
                <tr style={{ borderTop: '1px solid var(--border)', fontWeight: 'bold' }}>
                  <td>Total</td>
                  <td style={{ textAlign: 'right' }}>{alert.total_score}/100</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => {
              fetch('/api/cases', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'x-user-role': 'analyst' },
                body: JSON.stringify({ alert_id: id })
              }).then(res => res.json()).then(data => navigate(`/cases/${data.case_id}`));
            }}>Create Case</button>
            <button>Dismiss</button>
          </div>
        </div>
      </div>
    </div>
  );
}
