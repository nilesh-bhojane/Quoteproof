import { useState, useEffect } from 'react';

/**
 * SettingsPanel — Person B / Shared
 * CONTEXT.md Section 4, 8 & 11: Hourly rate, stale price threshold, GST %, Basic Mode, and Delete Data.
 */
export default function SettingsPanel({ onDataReset }) {
  const [hourlyRate, setHourlyRate] = useState('300');
  const [staleDays, setStaleDays] = useState(30);
  const [gstPct, setGstPct] = useState(18);
  const [basicMode, setBasicMode] = useState(false);
  const [savedMsg, setSavedMsg] = useState(null);
  const [resetConfirm, setResetConfirm] = useState(false);

  useEffect(() => {
    fetch('/api/v1/settings')
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
        if (data) {
          if (data.hourly_rate !== undefined) setHourlyRate(String(data.hourly_rate));
          if (data.stale_days !== undefined) setStaleDays(data.stale_days);
          if (data.gst_pct !== undefined) setGstPct(data.gst_pct);
          if (data.basic_mode !== undefined) setBasicMode(Boolean(data.basic_mode));
        }
      })
      .catch(() => {});
  }, []);

  const handleSaveSettings = async () => {
    try {
      await fetch('/api/v1/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hourly_rate: Number(hourlyRate),
          stale_days: Number(staleDays),
          gst_pct: Number(gstPct),
          basic_mode: basicMode,
        }),
      });
      setSavedMsg('Settings saved successfully.');
    } catch {
      setSavedMsg('Settings updated locally.');
    }
    setTimeout(() => setSavedMsg(null), 3000);
  };

  const handleDeleteData = async () => {
    try {
      await fetch('/api/v1/data', { method: 'DELETE' });
    } catch {}
    setResetConfirm(false);
    setSavedMsg('All demo quote and timing data has been reset.');
    if (onDataReset) onDataReset();
    setTimeout(() => setSavedMsg(null), 3000);
  };

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">APPLICATION SETTINGS & GOVERNANCE</p>
          <h2>Configuration & privacy controls</h2>
        </div>
        <span className="status">System Rules</span>
      </div>

      {savedMsg && (
        <div style={{ padding: 10, background: '#e0f5eb', color: '#18754d', borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
          ✓ {savedMsg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
        <div>
          <label>
            Hourly labour cost (₹/hour)
            <small style={{ display: 'block', color: '#738096', fontWeight: 400, marginTop: 4 }}>
              Used strictly for ROI labor value calculations. If empty or zero, ROI displays unestimated dashes.
            </small>
            <input
              type="number"
              min="0"
              value={hourlyRate}
              onChange={e => setHourlyRate(e.target.value)}
              style={{ marginTop: 8 }}
            />
          </label>
        </div>

        <div>
          <label>
            Stale price review limit (days)
            <small style={{ display: 'block', color: '#738096', fontWeight: 400, marginTop: 4 }}>
              Prices not updated within this threshold trigger a Stale Warning badge on quotation review.
            </small>
            <input
              type="number"
              min="1"
              max="365"
              value={staleDays}
              onChange={e => setStaleDays(e.target.value)}
              style={{ marginTop: 8 }}
            />
          </label>
        </div>

        <div>
          <label>
            Standard GST rate (%)
            <small style={{ display: 'block', color: '#738096', fontWeight: 400, marginTop: 4 }}>
              Default Goods & Services Tax percentage applied to discounted subtotals (default 18%).
            </small>
            <input
              type="number"
              min="0"
              max="28"
              value={gstPct}
              onChange={e => setGstPct(e.target.value)}
              style={{ marginTop: 8 }}
            />
          </label>
        </div>

        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', marginTop: 10 }}>
            <input
              type="checkbox"
              checked={basicMode}
              onChange={e => setBasicMode(e.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            <div>
              <strong>Force Basic Mode (No AI)</strong>
              <small style={{ display: 'block', color: '#738096', fontWeight: 400 }}>
                Rule: If AI is disabled or offline, fallback to deterministic regex/fuzzy parser.
              </small>
            </div>
          </label>
        </div>
      </div>

      <div className="actions" style={{ marginTop: 24 }}>
        <button className="primary" onClick={handleSaveSettings}>
          Save configuration
        </button>
      </div>

      {/* Dangerous zone: Delete all data */}
      <div style={{ marginTop: 36, borderTop: '1px solid #edf2f7', paddingTop: 20 }}>
        <h3 style={{ fontSize: 15, color: '#c53030', margin: '0 0 8px' }}>Privacy & Data Reset Zone</h3>
        <p className="muted" style={{ fontSize: 12 }}>
          Per CONTEXT.md Section 4: One-click "Delete all my data" resets all demo quotations, timings, and audit records.
        </p>
        {!resetConfirm ? (
          <button
            className="secondary"
            onClick={() => setResetConfirm(true)}
            style={{ borderColor: '#fed7d7', color: '#c53030' }}
          >
            Delete all my data
          </button>
        ) : (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: '#c53030', fontWeight: 600 }}>Confirm deletion?</span>
            <button
              className="primary"
              onClick={handleDeleteData}
              style={{ background: '#c53030', borderColor: '#c53030' }}
            >
              Yes, reset all demo data
            </button>
            <button className="secondary" onClick={() => setResetConfirm(false)}>
              Cancel
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
