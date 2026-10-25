import React, { useEffect, useState } from 'react';
import priceListData from '../../data/priceList.json';
import Timer from './Timer.jsx';

/**
 * QuotationPanel — Contributor B (Integrated)
 *
 * Editable quote table with review / approve / reject flow.
 * Matches extracted descriptions to known SKUs from the sample price list.
 * Calculates subtotal, configured tax and total in code (not in an LLM).
 * Blocks approval when any required field (qty, unitPrice) or "Approved by" name is unresolved.
 */
export default function QuotationPanel({ initialItems, onRecordEvent }) {
  const [priceList, setPriceList] = useState([]);
  const [items, setItems] = useState([
    { description: 'Large box', sku: 'DEMO001', qty: 500, unitPrice: 24, matched: true },
    { description: 'Small box', sku: 'SMALL001', qty: 0, unitPrice: 12, matched: true },
  ]);
  const [quoteHistory, setQuoteHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [taxRate, setTaxRate] = useState(18);
  const [status, setStatus] = useState('draft'); // draft | approved | rejected
  const [approvedBy, setApprovedBy] = useState('Karan Sapate');

  // Load the static price list and past quotes history from database
  useEffect(() => {
    setPriceList(priceListData);
    loadHistory();
  }, []);

  function loadHistory() {
    setLoadingHistory(true);
    fetch('/api/v1/quotes')
      .then(res => (res.ok ? res.json() : []))
      .then(data => {
        if (Array.isArray(data)) {
          setQuoteHistory(data);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  }

  function loadQuoteFromHistory(q) {
    if (q && q.items && q.items.length > 0) {
      const formatted = q.items.map(it => ({
        description: it.description || 'Item',
        sku: it.id || '',
        qty: Number(it.qty) || 0,
        unitPrice: Number(it.unit_price_snapshot) || 0,
        matched: true,
      }));
      setItems(formatted);
      setStatus(q.status || 'draft');
    }
  }

  // Accept items from upstream Inquiry extraction if provided
  useEffect(() => {
    if (initialItems && initialItems.length > 0) {
      const formatted = initialItems.map(it => ({
        description: it.description || 'Custom item',
        sku: it.sku || '',
        qty: it.quantity || 0,
        unitPrice: it.unitPrice || 0,
        matched: false,
      }));
      setItems(formatted);
      setStatus('draft');
      if (onRecordEvent) {
        onRecordEvent({
          id: `evt-${Date.now()}`,
          event_type: 'draft_created',
          title: 'Draft quote initialized from inquiry',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          details: `Imported ${formatted.length} line items from intake extraction`,
        });
      }
    }
  }, [initialItems]);

  // When price list is loaded or items change, enrich items with SKU & unitPrice via description matching
  useEffect(() => {
    if (priceList.length === 0) return;
    setItems(prev =>
      prev.map(it => {
        if (it.matched && it.unitPrice > 0) return it; // already matched, preserve edits
        const match = priceList.find(
          p =>
            p.description.toLowerCase().includes(it.description.toLowerCase()) ||
            it.description.toLowerCase().includes(p.description.toLowerCase())
        );
        if (match) {
          return {
            ...it,
            sku: match.sku,
            unitPrice: it.unitPrice > 0 ? it.unitPrice : match.unitPrice,
            matched: true,
          };
        }
        return it;
      })
    );
  }, [priceList]);

  const updateItem = (index, field, value) => {
    setItems(prev => {
      const newItems = [...prev];
      const prevVal = newItems[index][field];
      const nextVal = Number(value);
      newItems[index] = { ...newItems[index], [field]: nextVal };

      // Check if a zero quantity or price was just resolved
      if (prevVal === 0 && nextVal > 0 && onRecordEvent) {
        onRecordEvent({
          id: `evt-${Date.now()}`,
          event_type: 'warning_resolved',
          title: `Resolved specification: ${newItems[index].description}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          details: `Set ${field} to ${nextVal}`,
        });
      }
      return newItems;
    });
    setStatus('draft');
  };

  const subtotal = items.reduce(
    (sum, it) => sum + Math.max(0, it.qty || 0) * Math.max(0, it.unitPrice || 0),
    0
  );
  const safeTaxRate = Math.max(0, Math.min(100, Number(taxRate) || 0));
  const tax = subtotal * safeTaxRate / 100;
  const total = subtotal + tax;

  const money = n =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(n);

  // Approval is blocked when any item has qty <= 0 or unitPrice <= 0, or approvedBy is empty
  const unresolvedItems = items.filter(it => !(it.qty > 0 && it.unitPrice > 0));
  const canApprove = unresolvedItems.length === 0 && items.length > 0 && approvedBy.trim().length > 0;

  function handleApprove() {
    setStatus('approved');
    const evt = {
      id: `evt-${Date.now()}`,
      event_type: 'approved',
      title: `Quotation approved by ${approvedBy}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: `Approved total: ${money(total)} (${items.length} verified lines). Approver: ${approvedBy}`,
    };
    if (onRecordEvent) onRecordEvent(evt);
    fetch('/api/v1/quotes/active-quote/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved_by: approvedBy }),
    }).catch(() => {});
  }

  function handleReject() {
    setStatus('rejected');
    const evt = {
      id: `evt-${Date.now()}`,
      event_type: 'rejected',
      title: 'Quotation rejected by reviewer',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: `Rejected quote with subtotal ${money(subtotal)}`,
    };
    if (onRecordEvent) onRecordEvent(evt);
    fetch('/api/v1/quotes/active-quote/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'Rejected during human review' }),
    }).catch(() => {});
  }

  function handleSaveReview() {
    setStatus('draft');
    if (onRecordEvent) {
      onRecordEvent({
        id: `evt-${Date.now()}`,
        event_type: 'fields_edited',
        title: 'Review changes saved',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        details: `Updated lines: Subtotal ${money(subtotal)}, Tax ${safeTaxRate}%`,
      });
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">CONTRIBUTOR B · VALIDATION & APPROVAL</p>
          <h2>Quotation review</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Timer quoteId="active-quote" />
          <span
            className={
              status === 'approved'
                ? 'status success'
                : status === 'rejected'
                ? 'status warning'
                : 'status'
            }
          >
            {status === 'approved'
              ? `Approved by ${approvedBy}`
              : status === 'rejected'
              ? 'Rejected'
              : 'Awaiting review'}
          </span>
        </div>
      </div>

      {/* Validation notice — shown when fields are unresolved */}
      {unresolvedItems.length > 0 && (
        <div className="notice">
          <strong>Validation warning</strong>
          <p>
            {unresolvedItems.length} item(s) have missing quantity or unit price.
            Resolve all fields before approving.
          </p>
        </div>
      )}

      {/* Quote table */}
      <div className="table-head">
        <span>Item</span>
        <span>Qty</span>
        <span>Unit price</span>
        <span>Line total</span>
      </div>
      {items.map((it, idx) => (
        <div className="table-line" key={it.sku || idx}>
          <div>
            <strong>{it.description}</strong>
            <small>{it.sku || 'No SKU match'}</small>
          </div>
          <input
            aria-label="Quantity"
            type="number"
            min="0"
            value={it.qty}
            onChange={e => updateItem(idx, 'qty', e.target.value)}
          />
          <input
            aria-label="Unit price in rupees"
            type="number"
            min="0"
            value={it.unitPrice}
            onChange={e => updateItem(idx, 'unitPrice', e.target.value)}
          />
          <strong>{money(Math.max(0, it.qty || 0) * Math.max(0, it.unitPrice || 0))}</strong>
        </div>
      ))}

      {/* Tax & totals */}
      <div className="tax-row">
        <label>
          Tax rate (%)
          <input
            type="number"
            min="0"
            max="100"
            value={taxRate}
            onChange={e => {
              setTaxRate(e.target.value);
              setStatus('draft');
            }}
          />
        </label>
        <div className="totals">
          <div>
            <span>Subtotal</span>
            <strong>{money(subtotal)}</strong>
          </div>
          <div>
            <span>Tax</span>
            <strong>{money(tax)}</strong>
          </div>
          <div className="grand-total">
            <span>Demo total</span>
            <strong>{money(total)}</strong>
          </div>
        </div>
      </div>

      {/* Approval Details */}
      <div style={{ marginTop: 16, marginBottom: 16, background: '#f8fafc', padding: '12px 16px', borderRadius: 10, border: '1px solid #e2e8f0' }}>
        <label style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#4a5568' }}>Approved by (Required Owner Name):</span>
          <input
            type="text"
            value={approvedBy}
            onChange={e => setApprovedBy(e.target.value)}
            placeholder="e.g. Karan Sapate (Owner)"
            style={{ width: 220, padding: '6px 10px', borderRadius: 6, border: '1px solid #cbd5e1' }}
          />
        </label>
      </div>

      {/* Action buttons — review / approve / reject */}
      <div className="actions">
        <button className="primary" onClick={handleSaveReview}>
          Save review changes
        </button>{' '}
        <button
          className="secondary"
          disabled={!canApprove}
          onClick={handleApprove}
        >
          Approve
        </button>{' '}
        <button
          className="secondary"
          onClick={handleReject}
          style={{ borderColor: '#e2a0a0', color: '#a03030' }}
        >
          Reject
        </button>
      </div>

      {/* Past Quotes History */}
      <div style={{ marginTop: 28, paddingTop: 18, borderTop: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800, color: '#1e293b' }}>
            Past Quotes History ({quoteHistory.length})
          </h3>
          <button className="btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }} onClick={loadHistory}>
            ↻ Refresh History
          </button>
        </div>

        {quoteHistory.length === 0 ? (
          <p className="muted">No past quotes recorded yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {quoteHistory.slice(0, 8).map(q => (
              <div
                key={q.id}
                onClick={() => loadQuoteFromHistory(q)}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 14px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontSize: 12,
                }}
              >
                <div>
                  <strong>{q.inquiry_masked ? q.inquiry_masked.slice(0, 45) + '…' : `Quote #${q.id.slice(0, 8)}`}</strong>
                  <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>
                    {q.items ? `${q.items.length} line item(s)` : 'Items unlisted'} · {q.created_at ? new Date(q.created_at).toLocaleDateString() : 'Recent'}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`status ${q.status === 'approved' ? 'success' : q.status === 'rejected' ? 'warning' : ''}`}>
                    {q.status}
                  </span>
                  <strong style={{ fontSize: 13 }}>{money(q.total)}</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="muted" style={{ marginTop: 16 }}>
        Immutable snapshot rule: Approved quotations cannot be altered. Corrections create new revision events.
      </p>
    </section>
  );
}
