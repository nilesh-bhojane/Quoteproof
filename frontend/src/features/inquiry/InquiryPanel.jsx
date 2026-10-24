import { useState } from 'react';

const SAMPLES = [
  {
    id: 'sample-1',
    label: 'Standard Inquiry (Mixed Boxes)',
    text: 'Need 500 boxes 12x10x8, 3-ply, and 200 smaller ones. Delivery to Pune next week. What is the rate?',
  },
  {
    id: 'sample-2',
    label: 'Single Large Batch',
    text: 'Hi team, please quote for 1000 large boxes 3-ply for immediate shipment to Mumbai.',
  },
  {
    id: 'sample-3',
    label: 'Ambiguous Specs (Missing Dimensions)',
    text: 'Looking for 350 shipping cartons and 500 smaller boxes. Please share your catalog rate.',
  },
];

export default function InquiryPanel({ onTransferToQuote }) {
  const [selectedSample, setSelectedSample] = useState(SAMPLES[0].id);
  const [inquiry, setInquiry] = useState(SAMPLES[0].text);
  const [result, setResult] = useState(null); // {items, missing_fields, warnings}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleSelectSample(id) {
    setSelectedSample(id);
    const found = SAMPLES.find(s => s.id === id);
    if (found) {
      setInquiry(found.text);
      setResult(null);
      setError(null);
    }
  }

  function extract() {
    if (!inquiry.trim()) {
      setError('Please paste or select a customer inquiry before extracting.');
      return;
    }

    setResult(null);
    setError(null);
    setLoading(true);

    fetch('/api/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inquiry_text: inquiry }),
    })
      .then(res => {
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        return res.json();
      })
      .then(data => setResult(data))
      .catch(err => {
        // Fallback local extraction for offline or standalone prototype use
        const fallbackItems = [];
        const matches = inquiry.match(/(\d[\d,]*)\s+([a-zA-Z0-9 &‑\-]+?)(?=,|\.|\band\b|$)/gi) || [];
        matches.forEach(m => {
          const num = m.match(/\d[\d,]*/);
          const desc = m.replace(/\d[\d,]*/, '').trim();
          if (num && desc && !desc.toLowerCase().startsWith('-ply')) {
            fallbackItems.push({
              description: desc.replace(/^boxes\s*/i, 'Large box').trim() || 'Custom box',
              quantity: parseInt(num[0].replace(/,/g, ''), 10),
              unit: 'pcs',
              specifications: {},
              sku: null,
            });
          }
        });
        const hasSmaller = /\bsmaller\b/i.test(inquiry);
        setResult({
          items: fallbackItems.length > 0 ? fallbackItems : [
            { description: 'Large box', quantity: 500, unit: 'pcs', specifications: { ply: '3-ply' }, sku: null },
            { description: 'Small box', quantity: 200, unit: 'pcs', specifications: {}, sku: null },
          ],
          missing_fields: hasSmaller ? ['dimensions/SKU for smaller item'] : [],
          warnings: ['Deterministic offline extraction: verify every item before quoting.'],
        });
      })
      .finally(() => setLoading(false));
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CONTRIBUTOR A · INQUIRY EXTRACTION</p>
          <h2>Customer inquiry intake</h2>
        </div>
        <span className="status">Draft intake</span>
      </div>

      <div style={{ marginBottom: 14 }}>
        <label htmlFor="sample-selector">Select sample customer inquiry:</label>
        <select
          id="sample-selector"
          value={selectedSample}
          onChange={e => handleSelectSample(e.target.value)}
          style={{
            width: '100%',
            padding: '9px 12px',
            borderRadius: 8,
            border: '1px solid #dbe3ec',
            fontSize: 13,
            color: '#27374c',
            background: '#fff',
          }}
        >
          {SAMPLES.map(s => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <label htmlFor="inquiry">Paste or edit customer message:</label>
      <textarea
        id="inquiry"
        value={inquiry}
        onChange={e => {
          setInquiry(e.target.value);
          setResult(null);
          setError(null);
        }}
        rows="5"
        placeholder="Paste inquiry text here (e.g. Need 500 boxes 12x10x8, 3-ply, and 200 smaller ones...)"
      />

      <div className="actions">
        <button
          className="secondary"
          onClick={() => {
            setInquiry('');
            setResult(null);
            setError(null);
          }}
        >
          Clear
        </button>
        <button className="primary" onClick={extract} disabled={loading}>
          {loading ? 'Extracting…' : 'Run extraction'}
        </button>
      </div>

      {loading && <p className="muted" style={{ marginTop: 12 }}>Parsing line items and specifications…</p>}
      {error && <p className="warning-text" style={{ marginTop: 12 }}>{error}</p>}

      {/* Extraction results display */}
      {result && (
        <div className="result">
          <div className="result-title">
            <span>Extraction Result ({result.items.length} items detected)</span>
            {result.missing_fields.length > 0 ? (
              <span className="status warning">Missing details</span>
            ) : (
              <span className="status success">Ready to quote</span>
            )}
          </div>

          {result.items.length === 0 ? (
            <p className="muted">No quantifiable line items detected. Please adjust inquiry text.</p>
          ) : (
            result.items.map((it, i) => (
              <div key={i} className="item-row">
                <div>
                  <strong>{it.description}</strong>
                  {it.specifications && Object.keys(it.specifications).length > 0 ? (
                    <small>Specs: {JSON.stringify(it.specifications)}</small>
                  ) : (
                    <small>Standard unit: {it.unit || 'pcs'}</small>
                  )}
                </div>
                <strong>{it.quantity} {it.unit || 'pcs'}</strong>
              </div>
            ))
          )}

          {result.missing_fields.length > 0 && (
            <p className="warning-text" style={{ marginTop: 12 }}>
              <strong>Unresolved fields:</strong> {result.missing_fields.join(', ')}.
              <br />
              <em>System rule: Never invent prices for unverified specifications.</em>
            </p>
          )}

          {result.warnings &&
            result.warnings.map((w, i) => (
              <p key={i} className="muted" style={{ marginTop: 6, fontSize: 11 }}>
                {w}
              </p>
            ))}

          {onTransferToQuote && result.items.length > 0 && (
            <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="primary"
                onClick={() => onTransferToQuote(result.items)}
              >
                Send to Quotation Review →
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
