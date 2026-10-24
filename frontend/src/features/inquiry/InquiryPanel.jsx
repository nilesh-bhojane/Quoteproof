import { useState } from 'react';

const sample = 'Need 500 boxes 12x10x8, 3-ply, and 200 smaller ones. Delivery to Pune next week. What is the rate?';

export default function InquiryPanel() {
  const [inquiry, setInquiry] = useState(sample);
  const [result, setResult] = useState(null);   // {items, missing_fields, warnings}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ---------------------------------------------------------------------------
  // Helper – call backend extraction endpoint
  // ---------------------------------------------------------------------------
  function extract() {
    // Reset state
    setResult(null);
    setError(null);
    setLoading(true);

    fetch('/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inquiry_text: inquiry })
    })
      .then(res => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        return res.json();
      })
      .then(data => setResult(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CONTRIBUTOR A · INQUIRY EXTRACTION</p>
          <h2>Customer inquiry</h2>
        </div>
        <span className="status">Draft intake</span>
      </div>
      <label htmlFor="inquiry">Paste the customer's message</label>
      <textarea
        id="inquiry"
        value={inquiry}
        onChange={e => { setInquiry(e.target.value); setResult(null); setError(null); }}
        rows="5"
      />
      <div className="actions">
        <button className="secondary" onClick={() => { setInquiry(sample); setResult(null); setError(null); }}>
          Load sample
        </button>
        <button className="primary" onClick={extract}>
          Run extraction
        </button>
      </div>
      {loading && <p className="info">Extracting…</p>}
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result">
          <div className="result-title">
            Extraction result{' '}
            {result.missing_fields.length ? (
              <span className="status warning">Needs review</span>
            ) : (
              <span className="status success">Ready</span>
            )}
          </div>
          {result.items.map((it, i) => (
            <div key={i} className="item-row">
              <div>
                <strong>{it.description}</strong>
                {Object.keys(it.specifications).length ? (
                  <small>{JSON.stringify(it.specifications)}</small>
                ) : null}
              </div>
              <strong>{it.quantity} pcs</strong>
            </div>
          ))}
          {result.missing_fields.length > 0 && (
            <p className="warning-text">
              Missing details: {result.missing_fields.join(', ')}.
            </p>
          )}
          {result.warnings.map((w, i) => (
            <p key={i} className="muted">{w}</p>
          ))}
        </div>
      )}
    </section>
  );
}
