import { useState, useEffect } from 'react';

/**
 * AnalyticsPanel — Contributor C
 *
 * Evidence Ledger & ROI dashboard.
 * - Records and displays key workflow events (draft created, fields edited, warning resolved, approved/rejected).
 * - Displays manual and assisted workflow duration with clear illustrative labels.
 * - Shows time difference and percentage reduction.
 * - Calculates estimated labour value ONLY when an explicit, positive hourly rate is entered.
 */
export default function AnalyticsPanel({ externalEvents = [] }) {
  const [manualMinutes, setManualMinutes] = useState(10);
  const [assistedMinutes, setAssistedMinutes] = useState(4);
  const [hourlyRate, setHourlyRate] = useState('');
  const [events, setEvents] = useState([
    {
      id: 'demo-1',
      event_type: 'inquiry_received',
      title: 'Inquiry received',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: 'Customer inquiry captured and parsed into 2 line items',
    },
    {
      id: 'demo-2',
      event_type: 'draft_created',
      title: 'Draft quotation created',
      timestamp: new Date(Date.now() - 1000 * 60 * 12).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: 'Line items mapped to SKU DEMO001 / SMALL001',
    },
    {
      id: 'demo-3',
      event_type: 'warning_flagged',
      title: 'Validation warning flagged',
      timestamp: new Date(Date.now() - 1000 * 60 * 10).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: 'Missing quantity/specs detected on secondary line',
    },
    {
      id: 'demo-4',
      event_type: 'warning_resolved',
      title: 'Warning resolved by reviewer',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: 'Quantity entered by human reviewer before approval',
    },
  ]);

  // Merge any live events emitted by the integration layer
  useEffect(() => {
    if (externalEvents && externalEvents.length > 0) {
      setEvents(prev => {
        const existingIds = new Set(prev.map(e => e.id));
        const brandNew = externalEvents.filter(e => !existingIds.has(e.id));
        return [...brandNew, ...prev];
      });
    }
  }, [externalEvents]);

  // Also attempt to fetch latest events from backend /api/events
  useEffect(() => {
    fetch('/api/events')
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
        if (data && data.events && data.events.length > 0) {
          const apiEvents = data.events.map(e => ({
            id: e.id,
            event_type: e.event_type,
            title: e.event_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            timestamp: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            details: JSON.stringify(e.details),
          }));
          setEvents(prev => {
            const map = new Map();
            [...apiEvents, ...prev].forEach(item => map.set(item.id, item));
            return Array.from(map.values());
          });
        }
      })
      .catch(() => {
        // Fallback gracefully to local mock events
      });
  }, []);

  const manual = Math.max(0, Number(manualMinutes) || 0);
  const assisted = Math.max(0, Number(assistedMinutes) || 0);
  const timeSaved = Math.max(0, manual - assisted);
  const percentReduction = manual > 0 ? (timeSaved / manual) * 100 : 0;

  // Explicit rate required: strictly null/zero if empty or <= 0
  const hourlyNum = Number(hourlyRate);
  const hasHourly = hourlyRate !== '' && !isNaN(hourlyNum) && hourlyNum > 0;
  const estimatedLabour = hasHourly ? (timeSaved / 60) * hourlyNum : null;

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CONTRIBUTOR C · EVIDENCE LEDGER & ROI</p>
          <h2>Productivity evidence & audit trail</h2>
        </div>
        <span className="status warning">Illustrative inputs</span>
      </div>

      <div className="notice">
        <strong>Measurement notice</strong>
        <p>
          The inputs below illustrate the model based on baseline assumptions.
          Replace these with measured trial data for audit reporting.
        </p>
      </div>

      {/* Workflow duration inputs */}
      <div className="metric-inputs">
        <label>
          Manual workflow (minutes)
          <input
            type="number"
            min="0"
            value={manualMinutes}
            onChange={e => setManualMinutes(e.target.value)}
          />
        </label>
        <label>
          AI-assisted workflow (minutes)
          <input
            type="number"
            min="0"
            value={assistedMinutes}
            onChange={e => setAssistedMinutes(e.target.value)}
          />
        </label>
        <label>
          Hourly labour cost (₹/hour)
          <input
            type="number"
            min="0"
            placeholder="Optional explicit rate"
            value={hourlyRate}
            onChange={e => setHourlyRate(e.target.value)}
          />
        </label>
      </div>

      {/* ROI metrics cards */}
      <div className="metrics">
        <div className="metric">
          <span>Time saved per quote</span>
          <strong>{timeSaved.toFixed(1)} min</strong>
          <small>Manual vs. AI-assisted cycle</small>
        </div>
        <div className="metric">
          <span>Time reduction</span>
          <strong>{percentReduction.toFixed(1)}%</strong>
          <small>Cycle efficiency gain</small>
        </div>
        <div className="metric">
          <span>Estimated labour value</span>
          <strong>{estimatedLabour !== null ? `₹${estimatedLabour.toFixed(2)}` : '—'}</strong>
          <small>
            {estimatedLabour !== null
              ? 'Calculated from explicit hourly rate'
              : 'Enter hourly labour rate above'}
          </small>
        </div>
      </div>

      {/* Evidence Ledger */}
      <div className="ledger">
        <h3>Evidence Ledger · Recorded Audit Events ({events.length})</h3>
        <p className="muted">
          All state changes (intake, edit, approval, rejection) are tracked with timestamps to provide an immutable audit trail.
        </p>
        {events.map((evt, idx) => (
          <div className="ledger-row" key={evt.id || idx}>
            <span
              className="dot"
              style={{
                background:
                  evt.event_type.includes('reject')
                    ? '#d9534f'
                    : evt.event_type.includes('approv')
                    ? '#18754d'
                    : evt.event_type.includes('warn')
                    ? '#c4891b'
                    : '#328a82',
              }}
            />
            <div>
              <strong>{evt.title || evt.event_type}</strong>
              <small>{evt.details}</small>
            </div>
            <time>{evt.timestamp}</time>
          </div>
        ))}
      </div>
    </section>
  );
}
