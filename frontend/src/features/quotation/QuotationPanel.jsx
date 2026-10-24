import React, { useEffect, useState } from 'react';
import priceListData from '../../data/priceList.json';

/**
 * QuotationPanel — Contributor B (Integrated)
 *
 * Editable quote table with review / approve / reject flow.
 * Matches extracted descriptions to known SKUs from the sample price list.
 * Calculates subtotal, configured tax and total in code (not in an LLM).
 * Blocks approval when any required field (qty, unitPrice) is unresolved.
 */
export default function QuotationPanel({ initialItems, onRecordEvent }) {
  const [priceList, setPriceList] = useState([]);
  const [items, setItems] = useState([
    { description: 'Large box', sku: '', qty: 500, unitPrice: 0, matched: false },
    { description: 'Small box', sku: '', qty: 0, unitPrice: 0, matched: false },
  ]);
  const [taxRate, setTaxRate] = useState(18);
  const [status, setStatus] = useState('draft'); // draft | approved | rejected

  // Load the static price list
  useEffect(() => {
    setPriceList(priceListData);
  }, []);

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

  // Approval is blocked when any item has qty <= 0 or unitPrice <= 0
  const unresolvedItems = items.filter(it => !(it.qty > 0 && it.unitPrice > 0));
  const canApprove = unresolvedItems.length === 0 && items.length > 0;

  function handleApprove() {
    setStatus('approved');
    const evt = {
      id: `evt-${Date.now()}`,
      event_type: 'approved',
      title: 'Quotation approved by reviewer',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      details: `Approved total: ${money(total)} (${items.length} verified lines)`,
    };
    if (onRecordEvent) onRecordEvent(evt);
    // Post to backend audit trail API
    fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quote_id: 'quote-001', event_type: 'approved', details: { total, items: items.length } }),
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
    // Post to backend audit trail API
    fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quote_id: 'quote-001', event_type: 'rejected', details: { total } }),
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
            ? 'Approved for demo'
            : status === 'rejected'
            ? 'Rejected'
            : 'Awaiting review'}
        </span>
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

      <p className="muted">
        Demo calculation only. Tax rate and unit price are editable assumptions;
        unresolved lines must be completed before a real quote is approved.
      </p>
    </section>
  );
}
