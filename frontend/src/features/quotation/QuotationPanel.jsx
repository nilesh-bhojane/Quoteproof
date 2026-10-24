import React, { useEffect } from 'react';
import priceListData from '../../data/priceList.json';

/**
 * QuotationPanel — Contributor B
 *
 * Editable quote table with review / approve / reject flow.
 * Matches extracted descriptions to known SKUs from the sample price list.
 * Calculates subtotal, configured tax and total in code (not in an LLM).
 * Blocks approval when any required field (qty, unitPrice) is unresolved.
 */
export default function QuotationPanel() {
  const [priceList, setPriceList] = React.useState([]);
  const [items, setItems] = React.useState([
    { description: 'Large box', sku: '', qty: 500, unitPrice: 0, matched: false },
    { description: 'Small box', sku: '', qty: 0, unitPrice: 0, matched: false },
  ]);
  const [taxRate, setTaxRate] = React.useState(18);
  const [status, setStatus] = React.useState('draft'); // draft | approved | rejected

  // Load the static price list
  useEffect(() => {
    setPriceList(priceListData);
  }, []);

  // When price list is loaded, enrich items with SKU & unitPrice via description matching
  useEffect(() => {
    if (priceList.length === 0) return;
    setItems(prev =>
      prev.map(it => {
        if (it.matched) return it; // already matched, don't overwrite user edits
        const match = priceList.find(
          p => p.description.toLowerCase() === it.description.toLowerCase()
        );
        if (match) {
          return { ...it, sku: match.sku, unitPrice: match.unitPrice, matched: true };
        }
        return it;
      })
    );
  }, [priceList]);

  const updateItem = (index, field, value) => {
    setItems(prev => {
      const newItems = [...prev];
      newItems[index] = { ...newItems[index], [field]: Number(value) };
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
        <button className="primary" onClick={() => setStatus('draft')}>
          Save review changes
        </button>{' '}
        <button
          className="secondary"
          disabled={!canApprove}
          onClick={() => setStatus('approved')}
        >
          Approve
        </button>{' '}
        <button
          className="secondary"
          onClick={() => setStatus('rejected')}
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
