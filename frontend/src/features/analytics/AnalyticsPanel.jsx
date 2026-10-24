import { useState } from 'react';
export default function AnalyticsPanel() {
  const [manual, setManual] = useState(10);
  const [assisted, setAssisted] = useState(4);
  const [hourly, setHourly] = useState(300);
  const saved = Math.max(0, Number(manual)||0) - Math.max(0, Number(assisted)||0);
  const reduction = Number(manual)>0 ? saved / Number(manual) * 100 : 0;
  const value = saved / 60 * Math.max(0, Number(hourly)||0);
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">CONTRIBUTOR C · EVIDENCE LEDGER</p><h2>Productivity evidence</h2></div><span className="status warning">Illustrative inputs</span></div>
    <p className="muted">Replace these example inputs with timings recorded during real, comparable trials. These values are not measured results.</p>
    <div className="metric-inputs"><label>Manual minutes<input type="number" min="0" value={manual} onChange={e=>setManual(e.target.value)}/></label><label>Assisted minutes<input type="number" min="0" value={assisted} onChange={e=>setAssisted(e.target.value)}/></label><label>Labour cost ₹/hour<input type="number" min="0" value={hourly} onChange={e=>setHourly(e.target.value)}/></label></div>
    <div className="metrics"><div className="metric"><span>Time saved</span><strong>{saved.toFixed(1)} min</strong></div><div className="metric"><span>Time reduction</span><strong>{reduction.toFixed(1)}%</strong></div><div className="metric"><span>Estimated labour value</span><strong>₹{value.toFixed(2)}</strong><small>per quotation, based on entered rate</small></div></div>
    <div className="ledger"><h3>Evidence Ledger · example events</h3><div className="ledger-row"><span className="dot"></span><div><strong>Inquiry received</strong><small>Input captured · sample record</small></div><time>Event 01</time></div><div className="ledger-row"><span className="dot"></span><div><strong>Missing specification flagged</strong><small>Review required before approval</small></div><time>Event 02</time></div><div className="ledger-row"><span className="dot"></span><div><strong>Human review</strong><small>Approval event should be persisted by backend</small></div><time>Event 03</time></div></div>
  </section>;
}
